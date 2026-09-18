// Background FCM handler for the driver PWA.
// Uses the compat SDK because service workers can't use bundler-based imports.
importScripts("https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.14.1/firebase-messaging-compat.js");

// PLACEHOLDER CONFIG — must match src/lib/firebase.ts. Service workers can't read
// Vite env vars, so if you change the real project config, update it here too.
firebase.initializeApp({
  apiKey: "REPLACE_ME",
  authDomain: "nawabs-minto.firebaseapp.com",
  projectId: "nawabs-minto",
  storageBucket: "nawabs-minto.appspot.com",
  messagingSenderId: "000000000000",
  appId: "1:000000000000:web:0000000000000000000000",
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const title = payload.notification?.title ?? "Nawab's Minto";
  const options = {
    body: payload.notification?.body ?? "You have a new delivery.",
    icon: "/icons/icon-192.png",
  };
  self.registration.showNotification(title, options);
});
