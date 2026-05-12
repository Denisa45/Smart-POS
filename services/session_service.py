import time

SESSION_TIMEOUT = 300  # 5 minutes


def get_valid_session(db):
    session = db.child("current_session").get().val()
    if not session:
        return None
    if time.time() - session.get("timestamp", 0) > SESSION_TIMEOUT:
        db.child("current_session").remove()
        return None
    return session


def clear_session(db):
    db.child("current_session").remove()
