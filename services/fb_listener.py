import time
import threading
from services.firebase_config import db
from services.hardware_service import set_ready_led
from services.fcm_service import send_order_ready_notification
from utils.order_utils import compute_order_status
from core.state import StateManager, KioskState
from services.tts_service import announce_order_ready
from datetime import datetime

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
    notified_orders = set()
    reset_scheduled = set()

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
                    real_order_id = o.get("order_id", order_id)

                    # announce only once
                    if real_order_id not in notified_orders:

                        notified_orders.add(real_order_id)

                        # ---------------- FCM ----------------
                        token_data = db.child("fcm_tokens").child(real_order_id).get().val()

                        if not token_data:
                            token_data = db.child("fcm_tokens").child("latest").get().val()

                        if token_data and token_data.get("token"):

                            send_order_ready_notification(
                                token_data["token"],
                                o.get("display_number", "?")
                            )

                        # ---------------- TTS ----------------
                        order_user_id = o.get("user_id", "")
                        customer_name = (
                            order_user_id.capitalize()
                            if order_user_id
                            else "Customer"
                        )

                        print(
                            f"[TTS] Announcing order "
                            f"{o.get('display_number')} "
                            f"for {customer_name}"
                        )

                        announce_order_ready(
                            customer_name,
                            o.get("display_number", "?")
                        )

                    # ---------------- AUTO RESET ----------------
                    if real_order_id not in reset_scheduled:

                        created_at = o.get("created_at", "")

                        try:
                            order_time = datetime.fromisoformat(created_at)

                            age_seconds = (
                                datetime.now() - order_time
                            ).total_seconds()

                            if age_seconds < 600:

                                reset_scheduled.add(real_order_id)

                                def auto_reset(oid=real_order_id):
                                    time.sleep(30)
                                    StateManager.reset()
                                    print(
                                        f"[STATE] Auto-reset after order {oid} ready"
                                    )

                                threading.Thread(
                                    target=auto_reset,
                                    daemon=True
                                ).start()

                            else:
                                reset_scheduled.add(real_order_id)

                        except:
                            reset_scheduled.add(real_order_id)

                created_at = o.get("created_at", "")
                try:
                    order_time = datetime.fromisoformat(created_at)
                    age_seconds = (datetime.now() - order_time).total_seconds()

                    # ignore old ready orders
                    if age_seconds > 120:
                        continue

                except:
                    continue
            if any_ready != last_state:

                print("[LED] Ready state:", any_ready)

                set_ready_led(any_ready)

                last_state = any_ready

        except Exception as e:
            print("[ORDER LISTENER ERROR]", e)

        time.sleep(2)
# -------------------------
# SESSION LISTENER
# -------------------------
def listen_session():
    print("[LISTENER] Session started")
    last_ts = None
    while True:
        try:
            session = db.child("current_session").get().val()
            if session and session.get("status") in ("active", "ready"):
                ts = session.get("timestamp")
                if ts != last_ts:
                    last_ts = ts
                    user_id      = session.get("user_id")
                    card_uid     = session.get("card_uid", "")
                    bonus_points = session.get("bonus_points", 0)
                    print(f"[SESSION] Face login ? {user_id} | card={card_uid} | points={bonus_points}")
                    StateManager.set(KioskState.LOGGED_IN, user=user_id)
                    if _on_face_login:
                        _on_face_login(user_id)
        except Exception as e:
            print("[SESSION LISTENER ERROR]", e)
        time.sleep(1)