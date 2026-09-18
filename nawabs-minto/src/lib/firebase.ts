import { initializeApp } from "firebase/app";
import {
  getAuth,
  connectAuthEmulator,
  browserLocalPersistence,
  setPersistence,
} from "firebase/auth";
import {
  initializeFirestore,
  persistentLocalCache,
  persistentMultipleTabManager,
  connectFirestoreEmulator,
} from "firebase/firestore";
import { getFunctions, connectFunctionsEmulator } from "firebase/functions";
import { getMessaging, isSupported } from "firebase/messaging";

// PLACEHOLDER CONFIG — replace with your real Firebase project config
// (Project settings > General > Your apps > SDK setup and configuration)
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY ?? "REPLACE_ME",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN ?? "nawabs-minto.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID ?? "nawabs-minto",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET ?? "nawabs-minto.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID ?? "000000000000",
  appId: import.meta.env.VITE_FIREBASE_APP_ID ?? "1:000000000000:web:0000000000000000000000",
};

export const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
void setPersistence(auth, browserLocalPersistence);

// Firestore offline persistence — required so the driver app keeps working
// through brief connectivity drops and syncs queued writes when back online.
export const db = initializeFirestore(app, {
  localCache: persistentLocalCache({
    tabManager: persistentMultipleTabManager(),
  }),
});

export const functions = getFunctions(app);

export async function getMessagingIfSupported() {
  if (await isSupported()) {
    return getMessaging(app);
  }
  return null;
}

// Local dev: point at the Firebase emulator suite when VITE_USE_EMULATORS=1
if (import.meta.env.VITE_USE_EMULATORS === "1") {
  connectAuthEmulator(auth, "http://127.0.0.1:9099", { disableWarnings: true });
  connectFirestoreEmulator(db, "127.0.0.1", 8080);
  connectFunctionsEmulator(functions, "127.0.0.1", 5001);
}
