import { useEffect } from "react";
import { getToken } from "firebase/messaging";
import { getMessagingIfSupported } from "@/lib/firebase";
import { setDriverFcmToken } from "@/hooks/useDrivers";

/** Registers this device for push notifications and stores the token on the driver's doc. */
export function useRegisterFcmToken(driverId: string | undefined) {
  useEffect(() => {
    if (!driverId) return;
    if (typeof Notification === "undefined") return;

    let cancelled = false;

    async function register() {
      try {
        if (Notification.permission === "default") {
          await Notification.requestPermission();
        }
        if (Notification.permission !== "granted") return;

        const messaging = await getMessagingIfSupported();
        if (!messaging || cancelled) return;

        const registration = await navigator.serviceWorker.register("/firebase-messaging-sw.js");
        const token = await getToken(messaging, {
          vapidKey: import.meta.env.VITE_FIREBASE_VAPID_KEY,
          serviceWorkerRegistration: registration,
        });
        if (token && !cancelled && driverId) {
          await setDriverFcmToken(driverId, token);
        }
      } catch {
        // Push notifications are a nice-to-have — silently skip on unsupported browsers.
      }
    }

    void register();
    return () => {
      cancelled = true;
    };
  }, [driverId]);
}
