import time
from services.firebase_config import db
from services.hardware_service import set_ready_led
from services.fcm_service import send_order_ready_notification
from utils.order_utils import compute_order_status

_on_face_login = None

def register_face_callback(fn):
    global _on_face_login
    _on_face_login = fn

# -------------------------
# ORDER LISTENER
# -------------------------
def listen_orders():
    print("[LISTENER] Orders started")
    last_state = False
    notified_orders = set()  # track which orders already got a notification

    while True:
        try:
            orders = db.child("orders").get().val() or {}
            any_ready = False

            for order_id, o in orders.items():
                if not isinstance(o, dict):
                    continue

                status = o.get("status")
                if not status:
                    created_at = o.get("created_at")
                    estimated = o.get("estimated_time", 0)
                    if created_at:
                        status, _ = compute_order_status(created_at, estimated)

                if status == "ready":
                    any_ready = True

                    # send FCM notification once per order
                    real_order_id = o.get("order_id", order_id)
                    if real_order_id not in notified_orders:
                        notified_orders.add(real_order_id)
                        token_data = db.child("fcm_tokens").child(real_order_id).get().val()
                        if token_data and token_data.get("token"):
                            send_order_ready_notification(
                                token_data["token"],
                                o.get("display_number", "?")
                            )

            if any_ready != last_state:
                print("[LED] Ready state:", any_ready)
                set_ready_led(any_ready)
                last_state = any_ready

        except Exception as e:
            print("[ORDER LISTENER ERROR]", e)

        time.sleep(2)

# -------------------------
# SESSION LISTENER — face login trigger
# -------------------------

def listen_session():
    print("[LISTENER] Session started")
    last_ts = None

    while True:
        try:
            session = db.child("current_session").get().val()

            if session and session.get("status") == "active":
                ts = session.get("timestamp")
                if ts != last_ts:
                    last_ts = ts
                    user_id = session.get("user_id")
                    print(f"[SESSION] Face login detected → {user_id}")
                    if _on_face_login:
                        _on_face_login(user_id)

        except Exception as e:
            print("[SESSION LISTENER ERROR]", e)

        time.sleep(1)
