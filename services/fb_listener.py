import time
from services.firebase_config import db
from services.hardware_service import set_ready_led
from utils.order_utils import compute_order_status

_on_face_login = None


def register_face_callback(fn):
    global _on_face_login
    _on_face_login = fn


# -------------------------
# ORDER LISTENER — LED only on when an order is ready
# -------------------------

def listen_orders():
    print("[LISTENER] Orders started")
    last_state = False

    while True:
        try:
            orders = db.child("orders").get().val() or {}
            any_ready = False

            for o in orders.values():
                if not isinstance(o, dict):
                    continue

                # Some orders have explicit status field, others need computing
                if o.get("status") == "ready":
                    any_ready = True
                    break

                created_at = o.get("created_at")
                estimated = o.get("estimated_time", 0)
                if created_at:
                    status, _ = compute_order_status(created_at, estimated)
                    if status == "ready":
                        any_ready = True
                        break

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
