import { useEffect, useState } from "react";
import { collection, doc, onSnapshot, updateDoc } from "firebase/firestore";
import { db } from "@/lib/firebase";
import type { Driver } from "@/types";

export function useDrivers() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsub = onSnapshot(collection(db, "drivers"), (snap) => {
      setDrivers(snap.docs.map((d) => ({ id: d.id, ...d.data() }) as Driver));
      setLoading(false);
    });
    return unsub;
  }, []);

  return { drivers, loading };
}

export async function setDriverStatus(driverId: string, status: Driver["status"]) {
  await updateDoc(doc(db, "drivers", driverId), { status });
}

export async function setDriverFcmToken(driverId: string, fcmToken: string | null) {
  await updateDoc(doc(db, "drivers", driverId), { fcmToken });
}
