import time
from services.firebase_config import db


class KioskState:
    WAITING_FACE = "waiting_face"
    CARD_DETECTED = "card_detected"
    LOGGED_IN = "logged_in"
    ORDERING = "ordering"
    PAYMENT = "payment"
    DONE = "done"


class StateManager:
    current_state = KioskState.WAITING_FACE
    current_user = None

    @classmethod
    def set(cls, new_state, user=None):
        cls.current_state = new_state
        if user is not None:
            cls.current_user = user
        print(f"[STATE] → {new_state} | user={cls.current_user}")
        cls._sync()

    @classmethod
    def reset(cls):
        cls.current_state = KioskState.WAITING_FACE
        cls.current_user = None
        cls._sync()

    @classmethod
    def _sync(cls):
        try:
            db.child("current_state").set({
                "state": cls.current_state,
                "user": cls.current_user,
                "timestamp": time.time()
            })
        except Exception as e:
            print("[STATE SYNC ERROR]", e)
