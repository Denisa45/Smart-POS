import threading

from services.fb_listener import listen_orders
from services.rfid_reader import rfid_loop


def start_background_services():
    print("[SYSTEM] Starting background services...")

    threading.Thread(target=listen_orders, daemon=True).start()
    threading.Thread(target=rfid_loop, daemon=True).start()

    print("[SYSTEM] Background services started.")
