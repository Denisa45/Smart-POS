from flask import Blueprint, request, jsonify, url_for, render_template
from datetime import datetime
import uuid

from services.firebase_config import db
from services.card_service import process_card_payment
from services.session_service import get_valid_session
from services.hardware_service import set_ready_led
from services.firebase_service import get_products
from utils.order_utils import compute_order_status
orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/place_order", methods=["POST"])
def place_order():
    try:
        products = get_products() or {}

        selected_products = {}
        total = 0
        estimated_time = 0
        total_bonus = 0

        for key in request.form:
            if key.startswith("quantity_"):
                product_id = key.replace("quantity_", "")
                qty = int(request.form.get(key, 0))

                if qty > 0 and product_id in products:
                    item = products[product_id]

                    selected_products[product_id] = qty

                    total += item["price"] * qty
                    estimated_time += item["prep_time"] * qty
                    total_bonus += item.get("bonus_points", 0) * qty

        if not selected_products:
            return jsonify({"success": False, "error": "No products selected"}), 400

        existing = db.child("orders").get().val() or {}
        display_number = len(existing) + 1
        order_id = str(uuid.uuid4())[:8]
        now = datetime.now()

        payment_method = request.form.get("payment_method", "Card")
        payment_status = "paid" if payment_method == "Cash" else "waiting"

        order_data = {
            "order_id": order_id,
            "display_number": display_number,
            "products": selected_products,
            "total": total,
            "estimated_time": estimated_time,
            "earned_points": total_bonus,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "created_at": now.isoformat(),
            "time": now.strftime("%Y-%m-%d %H:%M:%S")
        }

        db.child("orders").push(order_data)
        redirect = (
            url_for("pages.card_payment_page", order_id=order_id)
            if payment_method == "Card"
            else url_for("pages.client_order", order_id=order_id)
        )

        return jsonify({
            "success": True,
            "order_id": order_id,
            "redirect_url": redirect
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
        

@orders_bp.route("/check_card_payment/<order_id>", methods=["POST"])
def check_card_payment(order_id):
    try:
        orders = db.child("orders").get().val() or {}
        target_key = None
        target_order = None

        for key, order in orders.items():
            if order.get("order_id") == order_id:
                target_key = key
                target_order = order
                break

        if not target_order:
            return jsonify({"success": False, "error": "Order not found"}), 404

        if target_order.get("payment_status") == "paid":
            return jsonify({
                "success": True,
                "paid": True,
                "redirect_url": url_for("pages.client_order", order_id=order_id)
            })

        session = get_valid_session(db)
        if not session:
            return jsonify({"success": False, "error": "No active session — tap your card"}), 400

        uid = session.get("card_uid")
        if not uid:
            return jsonify({"success": False, "error": "No card linked to this session"}), 400

        ok, message, new_balance = process_card_payment(uid, target_order["total"])
        if not ok:
            return jsonify({"success": False, "error": message}), 400

        db.child("orders").child(target_key).update({
            "payment_status": "paid",
            "card_uid": uid
        })

        return jsonify({
            "success": True,
            "paid": True,
            "message": message,
            "new_balance": new_balance,
            "redirect_url": url_for("pages.client_order", order_id=order_id)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
@orders_bp.route("/track/<order_id>")
def track_order(order_id):
    orders = db.child("orders").get().val()
    order = None
    for key, data in (orders or {}).items():
        if data.get("order_id") == order_id:
            order = data
            order["key"] = key
            break

    if not order:
        return "Order not found", 404

    # compute status and remaining time
    status, remaining = compute_order_status(
        order.get("created_at", ""),
        order.get("estimated_time", 0)
    )
    order["status"] = status
    order["remaining_time"] = remaining

    points = 0
    card_uid = order.get("card_uid")
    if card_uid:
        member = db.child("members").child(card_uid).get().val()
        points = (member or {}).get("bonus_points", 0)

    return render_template("mobile_track.html",
        order=order,
        order_id=order_id,
        points=points
    )

@orders_bp.route("/api/order_status/<order_id>")
def order_status_api(order_id):
    orders = db.child("orders").get().val()
    for key, data in (orders or {}).items():
        if data.get("order_id") == order_id:
            status, remaining = compute_order_status(
                data.get("created_at", ""),
                data.get("estimated_time", 0)
            )
            return jsonify({"status": status, "remaining": remaining})
    return jsonify({"status": "unknown"}), 404

@orders_bp.route("/save_fcm_token", methods=["POST"])
def save_fcm_token():
    data = request.get_json()
    order_id = data.get("order_id")
    token = data.get("token")
    if order_id and token:
        db.child("fcm_tokens").child(order_id).set({"token": token})
        return jsonify({"success": True})
    return jsonify({"success": False}), 400