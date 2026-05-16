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