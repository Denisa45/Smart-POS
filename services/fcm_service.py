import firebase_admin
from firebase_admin import credentials, messaging
import os

# only initialize once; push notifications are skipped if the key file is missing
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(
            os.path.join(os.path.dirname(__file__), "..", "serviceAccountKey.json")
        )
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://iot-kiosk-pos-default-rtdb.europe-west1.firebasedatabase.app"
        })
    except Exception as e:
        print("[FCM] Disabled (no serviceAccountKey.json):", e)

# def send_order_ready_notification(token, order_number):
#     try:
#         message = messaging.Message(
#             notification=messaging.Notification(
#                 title="Denisa's Special ?",
#                 body=f"Order #{order_number} is ready! Come pick it up ?",
#             ),
#             token=token,
#         )
#         response = messaging.send(message)
#         print(f"[FCM] Notification sent: {response}")
#         return True
#     except Exception as e:
#         print(f"[FCM] Error: {e}")
#         return False

def send_order_ready_notification(token, order_number):
    try:
        message = messaging.Message(

            notification=messaging.Notification(
                title="Denisa's Special ",
                body=f"Order #{order_number} is ready! Come pick it up ",
            ),

            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title="Denisa's Special ",
                    body=f"Order #{order_number} is ready! Come pick it up ",
                    icon="https://skype-dinner-headband.ngrok-free.dev/static/assets/icon.png",
                ),
            ),

            token=token,
        )

        response = messaging.send(message)

        print(f"[FCM] Notification sent: {response}")

        return True

    except Exception as e:
        print(f"[FCM] Error: {e}")
        return False