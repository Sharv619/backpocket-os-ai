import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  onAuthStateChanged,
  signInWithCustomToken,
  signOut as firebaseSignOut,
} from "firebase/auth";
import { doc, onSnapshot } from "firebase/firestore";
import { httpsCallable } from "firebase/functions";
import { auth, db, functions } from "@/lib/firebase";
import type { Driver } from "@/types";

interface DriverLoginResult {
  token: string;
  driverId: string;
}

interface DriverAuthState {
  driver: Driver | null;
  loading: boolean;
  error: string | null;
  signIn: (phone: string, pin: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const DriverAuthContext = createContext<DriverAuthState | null>(null);

export function DriverAuthProvider({ children }: { children: ReactNode }) {
  const [driver, setDriver] = useState<Driver | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let unsubDriverDoc: (() => void) | undefined;

    const unsubAuth = onAuthStateChanged(auth, async (firebaseUser) => {
      unsubDriverDoc?.();
      if (!firebaseUser) {
        setDriver(null);
        setLoading(false);
        return;
      }
      const tokenResult = await firebaseUser.getIdTokenResult();
      if (tokenResult.claims.role !== "driver") {
        setDriver(null);
        setLoading(false);
        return;
      }
      unsubDriverDoc = onSnapshot(doc(db, "drivers", firebaseUser.uid), (snap) => {
        setDriver(snap.exists() ? ({ id: snap.id, ...snap.data() } as Driver) : null);
        setLoading(false);
      });
    });

    return () => {
      unsubAuth();
      unsubDriverDoc?.();
    };
  }, []);

  async function signIn(phone: string, pin: string) {
    setError(null);
    try {
      const driverLogin = httpsCallable<{ phone: string; pin: string }, DriverLoginResult>(
        functions,
        "driverLogin",
      );
      const result = await driverLogin({ phone, pin });
      await signInWithCustomToken(auth, result.data.token);
    } catch {
      setError("Couldn't sign in — check the phone number and PIN.");
      throw new Error("driver-sign-in-failed");
    }
  }

  async function signOut() {
    await firebaseSignOut(auth);
  }

  return (
    <DriverAuthContext.Provider value={{ driver, loading, error, signIn, signOut }}>
      {children}
    </DriverAuthContext.Provider>
  );
}

export function useDriverAuth() {
  const ctx = useContext(DriverAuthContext);
  if (!ctx) throw new Error("useDriverAuth must be used within DriverAuthProvider");
  return ctx;
}
