from services.firebase_config import db
from services.hardware_service import set_ready_led
import time

def listen_orders():
    ref = db.child("orders")
    last_state = False

    while True:
        try:
            orders = ref.get().val() or {}

            # ONLY care about REAL cooking status
            any_ready = any(
                isinstance(o, dict) and o.get("status") == "ready"
                for o in orders.values()
            )

            if any_ready != last_state:
                print("[LED] READY STATE:", any_ready)
                set_ready_led(any_ready)
                last_state = any_ready

        except Exception as e:
            print("[FB ERROR]", e)

        time.sleep(2)
