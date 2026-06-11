from flask import Blueprint, render_template, request, jsonify, redirect
from services.firebase_config import db
import time

enroll_bp = Blueprint("enroll", __name__)

@enroll_bp.route("/enroll")
def enroll():
    card_uid = request.args.get("card_uid", "")
    return render_template("enroll.html", card_uid=card_uid)

@enroll_bp.route("/enroll/save", methods=["POST"])
def enroll_save():
    try:
        data = request.get_json()
        card_uid = data.get("card_uid")
        name = data.get("name", "").strip().lower()

        if not card_uid or not name:
            return jsonify({"success": False, "error": "Missing name or card"}), 400

        profile = {
            "name": name,
            "card_uid": card_uid,
            "total_orders": 0,
            "history": {},
            "preferences": {
                "diet": data.get("diet", "none"),
                "favorite_category": data.get("favorite_category", "any"),
                "spicy": data.get("spicy", False),
                "budget_range": {
                    "min": int(data.get("budget_min", 10)),
                    "max": int(data.get("budget_max", 30))
                }
            }
        }

        db.child("members").child(name).set(profile)
        db.child("cards").child(card_uid).set({"member_id": name})

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enroll_bp.route("/enroll/submit", methods=["POST"])
def enroll_submit():
    try:
        data = request.get_json() or {}
        name = data.get("name", "").strip().lower()
        if not name:
            return jsonify({"success": False, "error": "Name required"}), 400

        profile = {
            "name": name,
            "card_uid": "",
            "bonus_points": 0,
            "total_orders": 0,
            "history": {},
            "preferences": {
                "diet": data.get("diet", ["non_vegetarian"]),
                "favorite_category": data.get("favorite_category", "any"),
                "budget_range": {
                    "min": int(data.get("budget_min", 10)),
                    "max": int(data.get("budget_max", 50))
                }
            }
        }

        # save member profile
        db.child("members").child(name).set(profile)

        # set enrollment_request so laptop recognizer knows who to capture
        db.child("enrollment_request").set({
            "name": name,
            "status": "pending",
            "timestamp": time.time()
        })

        print(f"[ENROLL] Profile saved and enrollment requested for: {name}")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enroll_bp.route("/enroll/reset", methods=["POST"])
def enroll_reset():
    """Clear stale enrollment state before starting new enrollment."""
    db.child("enrollment_request").remove()
    db.child("kiosk_command").remove()
    return jsonify({"success": True})

@enroll_bp.route("/enroll/complete", methods=["POST"])
def enroll_complete():
    """Called by Pi after enrollment done — clears session so waiting screen shows."""
    import time as _t
    db.child("current_session").remove()
    db.child("current_state").set({
        "state": "waiting_face",
        "user": None,
        "timestamp": _t.time()
    })
    db.child("enrollment_request").remove()
    return jsonify({"success": True})
