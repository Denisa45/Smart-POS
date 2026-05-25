importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyAXAm1Q9aJJp57kG_DX9LjTG0w3BYki68o",
  authDomain: "iot-kiosk-pos.firebaseapp.com",
  databaseURL: "https://iot-kiosk-pos-default-rtdb.europe-west1.firebasedatabase.app",
  projectId: "iot-kiosk-pos",
  storageBucket: "iot-kiosk-pos.firebasestorage.app",
  messagingSenderId: "813825236516",
  appId: "1:813825236516:web:cb54677e33cce820de82b1"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
  self.registration.showNotification(payload.notification.title, {
    body: payload.notification.body,
    icon: '/static/assets/icon.png'
  });
});
