import time

def create_session(db, card_uid):
    session = {
        "card_uid": card_uid,
        "timestamp": time.time()
    }
    db.child("current_session").set(session)
    return session


def get_valid_session(db, timeout=10):
    session = db.child("current_session").get().val()

    if not session:
        return None

    if time.time() - session.get("timestamp", 0) > timeout:
        db.child("current_session").delete()
        return None

    return session


def clear_session(db):
    db.child("current_session").delete()