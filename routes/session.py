from flask import Blueprint, request, jsonify
import time

from services.firebase_config import db
from services.hardware_service import set_ready_led
from services.session_service import clear_session
from core.state import StateManager, KioskState

session_bp = Blueprint("session", __name__)


@session_bp.route("/face_login", methods=["POST"])
def face_login():
    """
    Called by the laptop face recognition script via Firebase listener.
    The laptop writes to current_session in Firebase, which triggers
    on_face_login() in startup.py — this HTTP route is kept only as a
    fallback for direct POST (e.g. testing from curl or Postman).
    """
    try:
        data = request.get_json() or {}
        user_id = data.get("user_id")

        _handle_face_login(user_id)

        session = db.child("current_session").get().val() or {}
        return jsonify({"success": True, "session": session})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _handle_face_login(user_id):
    """
    Shared logic used by both the HTTP route and the Firebase listener callback.
    Looks up the member, enriches the session, updates kiosk state.
    """
    if not user_id:
        db.child("current_session").set({
            "user_id": None,
            "type": "guest",
            "status": "ready",
            "timestamp": time.time()
        })
        StateManager.set(KioskState.LOGGED_IN, user="guest")
        set_ready_led(True)
        print("[SESSION] Guest login")
        return

    member = db.child("members").child(user_id).get().val()

    if not member:
        # Face recognized but not registered — treat as guest
        db.child("current_session").set({
            "user_id": user_id,
            "type": "guest",
            "status": "ready",
            "timestamp": time.time()
        })
        StateManager.set(KioskState.LOGGED_IN, user="guest")
        set_ready_led(True)
        print(f"[SESSION] {user_id} not in members → guest")
        return

    # Full member — store everything needed for suggestions + payment
    db.child("current_session").set({
        "user_id": user_id,
        "card_uid": str(member["card_uid"]),
        "type": "member",
        "status": "ready",
        "bonus_points": member.get("bonus_points", 0),
        "timestamp": time.time()
    })
    StateManager.set(KioskState.LOGGED_IN, user=user_id)
    set_ready_led(True)
    print(f"[SESSION] Member logged in: {user_id} | card={member['card_uid']}")


@session_bp.route("/get_state")
def get_state():
    """
    Frontend polls this every second on start.html to know when
    face login completed and it should redirect to /menu.
    """
    state = db.child("current_state").get().val() or {}
    session = db.child("current_session").get().val() or {}
    return jsonify({
        "state": state.get("state", KioskState.WAITING_FACE),
        "user": state.get("user"),
        "session_type": session.get("type"),        # "member" | "guest"
        "card_uid": session.get("card_uid"),         # for suggestions later
        "bonus_points": session.get("bonus_points", 0)
    })


@session_bp.route("/logout", methods=["POST"])
def logout():
    clear_session(db)
    StateManager.reset()
    set_ready_led(False)
    return jsonify({"success": True})


@session_bp.route("/get_recommendations")
def get_recommendations():
    """
    Called by start.html after face login.
    Returns member name + top products based on their order history.
    """
    from utils.recommendations import get_recommendations as compute_recs

    session = db.child("current_session").get().val()
    if not session or session.get("type") != "member":
        return jsonify({"success": False, "recommendations": []})

    card_uid = session.get("card_uid")
    user_id = session.get("user_id")

    orders = db.child("orders").get().val() or {}
    recs = compute_recs(orders, card_uid, top_n=3)

    return jsonify({
        "success": True,
        "user_id": user_id,
        "card_uid": card_uid,
        "bonus_points": session.get("bonus_points", 0),
        "recommendations": recs  # [{"name": "Coffee", "times": 5}, ...]
    })
