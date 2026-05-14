from flask import Blueprint, request, jsonify
import time

from services.firebase_config import db
from services.hardware_service import set_ready_led
from services.session_service import clear_session
from core.state import StateManager, KioskState

session_bp = Blueprint("session", __name__)


@session_bp.route("/face_login", methods=["POST"])
def face_login():
    try:
        data = request.get_json() or {}
        user_id = data.get("user_id")
        _handle_face_login(user_id)
        session = db.child("current_session").get().val() or {}
        return jsonify({"success": True, "session": session})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _handle_face_login(user_id):
    if not user_id:
        db.child("current_session").set({
            "user_id": None, "type": "guest",
            "status": "ready", "timestamp": time.time()
        })
        StateManager.set(KioskState.LOGGED_IN, user="guest")
        set_ready_led(True)
        print("[SESSION] Guest login")
        return

    member = db.child("members").child(user_id).get().val()

    if not member:
        db.child("current_session").set({
            "user_id": user_id, "type": "guest",
            "status": "ready", "timestamp": time.time()
        })
        StateManager.set(KioskState.LOGGED_IN, user="guest")
        set_ready_led(True)
        print(f"[SESSION] {user_id} not in members → guest")
        return

    db.child("current_session").set({
        "user_id": user_id,
        "card_uid": str(member["card_uid"]),
        "type": "member",
        "status": "ready",
        "bonus_points": member.get("bonus_points", 0),
        "preferences": member.get("preferences", {}),
        "timestamp": time.time()
    })
    StateManager.set(KioskState.LOGGED_IN, user=user_id)
    set_ready_led(True)
    print(f"[SESSION] Member logged in: {user_id} | card={member['card_uid']}")


@session_bp.route("/get_state")
def get_state():
    state = db.child("current_state").get().val() or {}
    session = db.child("current_session").get().val() or {}
    return jsonify({
        "state": state.get("state", KioskState.WAITING_FACE),
        "user": state.get("user"),
        "session_type": session.get("type"),
        "card_uid": session.get("card_uid"),
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
    from services.gemini_service import get_llm_recommendations

    session = db.child("current_session").get().val()
    if not session or session.get("type") != "member":
        return jsonify({"success": False, "recommendations": []})

    user_id = session.get("user_id")
    prefs = session.get("preferences", {})
    all_products = db.child("products").get().val() or {}

    member = db.child(f"members/{user_id}").get().val() or {}
    member_name = member.get("name", user_id)

    def is_allowed(product, user_diet):
        product_diet = product.get("diet", [])
        if not user_diet:
            return True
        if "vegetarian" in user_diet and "non_vegetarian" in product_diet:
            return False
        return True

    safe_menu = {
        p_id: {
            "name": p.get("name"),
            "price": p.get("price"),
            "category": p.get("category"),
            "meal_type": p.get("meal_type"),
            "diet": p.get("diet")
        }
        for p_id, p in all_products.items()
        if is_allowed(p, prefs.get("diet", []))
    }

    try:
        ll_data = get_llm_recommendations(member_name, prefs, safe_menu)
    except Exception as e:
        print("LLM error:", e)
        ll_data = {"top_ids": [], "pitch": "Welcome back!"}

    final_recs = []
    for p_id in ll_data.get("top_ids", []):
        if p_id in all_products:
            final_recs.append(all_products[p_id])

    return jsonify({
        "success": True,
        "pitch": ll_data.get("pitch", "Welcome back!"),
        "recommendations": final_recs
    })


# ← Previously this was incorrectly indented INSIDE get_recommendations
@session_bp.route("/get_upsell", methods=["POST"])
def get_upsell():
    from services.gemini_service import get_upsell_pitch

    data = request.get_json()
    last_item_id = data.get("item_id")

    all_products = db.child("products").get().val() or {}
    session = db.child("current_session").get().val() or {}

    product = all_products.get(last_item_id)
    if not product or "pairs_with" not in product:
        return jsonify({"success": False})

    user_diet = session.get("preferences", {}).get("diet", [])
    potential_pairs = []

    for pair_name in product["pairs_with"]:
        pair_id = pair_name.lower().replace(" ", "_")
        pair_info = all_products.get(pair_id)
        if pair_info:
            p_diet = pair_info.get("diet", [])
            if "vegetarian" in user_diet and "non_vegetarian" in p_diet:
                continue
            # Pass the id along so Gemini can echo it back
            potential_pairs.append({**pair_info, "id": pair_id})

    if not potential_pairs:
        return jsonify({"success": False})

    suggestion = get_upsell_pitch(product["name"], potential_pairs)
    return jsonify({"success": True, "suggestion": suggestion})
