class KioskState:
    IDLE = "idle"
    CARD_DETECTED = "card_detected"
    USER_AUTHENTICATED = "user_authenticated"
    MENU = "menu"
    PAYMENT = "payment"


class StateManager:
    def __init__(self):
        self.state = KioskState.IDLE
        self.user = None

    def set(self, state, user=None):
        self.state = state
        self.user = user
        print(f"[STATE] {state} | user={user}")

    def get(self):
        return {
            "state": self.state,
            "user": self.user
        }

state=StateManager()
