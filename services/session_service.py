import time

SESSION_TIMEOUT = 300


def get_valid_session(db):
    session = db.child("current_session").get().val()
    if not session:
        return None

    if time.time() - session.get("timestamp", 0) > SESSION_TIMEOUT:
        clear_session(db)
        return None

    return session


def clear_session(db):
    db.child("current_session").remove()

    db.child("current_state").set({
        "state": "waiting_face",
        "timestamp": time.time()
    })

    print("[SESSION] Cleared")