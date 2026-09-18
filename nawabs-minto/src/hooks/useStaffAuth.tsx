import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut as firebaseSignOut,
  type User,
} from "firebase/auth";
import { doc, getDoc } from "firebase/firestore";
import { auth, db } from "@/lib/firebase";
import type { StaffMember } from "@/types";

interface StaffAuthState {
  user: User | null;
  staff: StaffMember | null;
  loading: boolean;
  error: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const StaffAuthContext = createContext<StaffAuthState | null>(null);

export function StaffAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [staff, setStaff] = useState<StaffMember | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);
      if (firebaseUser) {
        const staffDoc = await getDoc(doc(db, "staff", firebaseUser.uid));
        setStaff(
          staffDoc.exists()
            ? ({ id: staffDoc.id, ...staffDoc.data() } as StaffMember)
            : {
                id: firebaseUser.uid,
                name: firebaseUser.email ?? "Staff",
                email: firebaseUser.email ?? "",
                role: "staff",
              },
        );
      } else {
        setStaff(null);
      }
      setLoading(false);
    });
  }, []);

  async function signIn(email: string, password: string) {
    setError(null);
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch {
      setError("Couldn't sign in — check the email and password.");
      throw new Error("sign-in-failed");
    }
  }

  async function signOut() {
    await firebaseSignOut(auth);
  }

  return (
    <StaffAuthContext.Provider
      value={{ user, staff, loading, error, signIn, signOut }}
    >
      {children}
    </StaffAuthContext.Provider>
  );
}

export function useStaffAuth() {
  const ctx = useContext(StaffAuthContext);
  if (!ctx) throw new Error("useStaffAuth must be used within StaffAuthProvider");
  return ctx;
}
