import threading
from services.fb_listener import listen_orders, listen_session, register_face_callback
from services.rfid_reader import rfid_loop


def start_background_services():
    # Import here to avoid circular imports at module load time
    from routes.session import _handle_face_login

    print("[SYSTEM] Starting background services...")

    register_face_callback(_handle_face_login)

    threading.Thread(target=listen_orders, daemon=True).start()
    threading.Thread(target=listen_session, daemon=True).start()
    threading.Thread(target=rfid_loop, daemon=True).start()

    print("[SYSTEM] Ready.")
