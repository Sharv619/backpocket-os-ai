import { initializeApp } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";
import { getFirestore, FieldValue } from "firebase-admin/firestore";
import { getMessaging } from "firebase-admin/messaging";
import { onCall, HttpsError } from "firebase-functions/v2/https";
import { onDocumentUpdated } from "firebase-functions/v2/firestore";
import * as bcrypt from "bcryptjs";

initializeApp();
const db = getFirestore();

interface DriverLoginRequest {
  phone: string;
  pin: string;
}

/**
 * Driver login: phone + PIN in, a Firebase custom token out.
 * The token's uid equals the driver's Firestore doc id, with a `role: "driver"`
 * claim, so Firestore security rules can key off both directly.
 */
export const driverLogin = onCall<DriverLoginRequest>(async (request) => {
  const phone = request.data.phone?.trim();
  const pin = request.data.pin?.trim();
  if (!phone || !pin) {
    throw new HttpsError("invalid-argument", "Phone and PIN are required.");
  }

  const snapshot = await db.collection("drivers").where("phone", "==", phone).limit(1).get();
  if (snapshot.empty) {
    throw new HttpsError("not-found", "No driver found with that phone number.");
  }

  const driverDoc = snapshot.docs[0];
  const driver = driverDoc.data() as { pinHash?: string };
  if (!driver.pinHash || !(await bcrypt.compare(pin, driver.pinHash))) {
    throw new HttpsError("permission-denied", "Incorrect PIN.");
  }

  const token = await getAuth().createCustomToken(driverDoc.id, { role: "driver" });
  return { token, driverId: driverDoc.id };
});

interface SetDriverPinRequest {
  driverId: string;
  pin: string;
}

/** Lets a signed-in staff member set/reset a driver's PIN without touching Firestore by hand. */
export const setDriverPin = onCall<SetDriverPinRequest>(async (request) => {
  if (!request.auth) {
    throw new HttpsError("unauthenticated", "Sign in as staff first.");
  }
  const staffDoc = await db.collection("staff").doc(request.auth.uid).get();
  if (!staffDoc.exists) {
    throw new HttpsError("permission-denied", "Only staff can set driver PINs.");
  }

  const { driverId, pin } = request.data;
  if (!driverId || !/^\d{4,6}$/.test(pin ?? "")) {
    throw new HttpsError("invalid-argument", "driverId and a 4-6 digit pin are required.");
  }

  const pinHash = await bcrypt.hash(pin, 10);
  await db.collection("drivers").doc(driverId).set({ pinHash }, { merge: true });
  return { ok: true };
});

/**
 * On every order update: keeps drivers.currentOrderId in sync, and pushes a
 * push notification to the driver the instant an order is newly assigned to them.
 */
export const onOrderWritten = onDocumentUpdated("orders/{orderId}", async (event) => {
  const before = event.data?.before.data();
  const after = event.data?.after.data();
  if (!before || !after) return;

  const orderId = event.params.orderId;
  const driverId = (after.assignedDriverId as string | null) ?? null;
  const prevDriverId = (before.assignedDriverId as string | null) ?? null;
  const isActive = after.status !== "delivered" && after.status !== "cancelled";

  if (driverId !== prevDriverId) {
    if (prevDriverId) {
      await db.collection("drivers").doc(prevDriverId).update({ currentOrderId: FieldValue.delete() });
    }
    if (driverId) {
      await db.collection("drivers").doc(driverId).update({
        currentOrderId: isActive ? orderId : FieldValue.delete(),
      });

      const driverDoc = await db.collection("drivers").doc(driverId).get();
      const fcmToken = driverDoc.data()?.fcmToken as string | undefined;
      if (fcmToken) {
        await getMessaging().send({
          token: fcmToken,
          notification: {
            title: "New delivery assigned",
            body: `${after.customerName} — ${after.deliveryAddress || "pickup"}`,
          },
          data: { orderId },
        });
      }
    }
  } else if (driverId && !isActive) {
    await db.collection("drivers").doc(driverId).update({ currentOrderId: FieldValue.delete() });
  }
});
