import pyrebase

config = {
    "apiKey": "AIzaSyAXAm1Q9aJJp57kG_DX9LjTG0w3BYki68o",
    "authDomain": "iot-kiosk-pos.firebaseapp.com",
    "databaseURL": "https://iot-kiosk-pos-default-rtdb.europe-west1.firebasedatabase.app",
    "storageBucket": "iot-kiosk-pos.firebasestorage.app"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()
