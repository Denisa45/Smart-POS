from flask import Blueprint, render_template
from services.firebase_config import db
from services.hardware_service import set_ready_led
from utils.order_utils import compute_order_status
from services.firebase_service import get_products
from services.session_service import get_valid_session
from flask import jsonify

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def start():
    products=get_products() or {}
    return render_template("start.html", menu_items=products)

@pages_bp.route("/menu")
def menu():
    products = db.child("products").get().val()

    product_list = []

    for key, product in products.items():
        product["id"] = key
        product_list.append(product)

    categories = sorted(list(set(
        p.get("category", "other")
        for p in product_list
    )))

    print(categories)

    return render_template(
        "menu.html",
        products=product_list,
        categories=categories
    )
    

@pages_bp.route("/checkout")
def checkout():
    session = get_valid_session(db)
    member = None
    bonus_points = 0
    if session:
        # try by user_id (name) first, then by card_uid
        user_id = session.get("user_id")
        uid = session.get("card_uid")
        
        if user_id:
            member = db.child("members").child(user_id).get().val()
        
        if not member and uid:
            member = db.child("members").child(uid).get().val()
        
        if member:
            bonus_points = member.get("bonus_points", 0)

    return render_template(
        "checkout.html",
        member=member,
        bonus_points=bonus_points
    )

from flask import request, jsonify

@pages_bp.route("/checkout_preview", methods=["POST"])
def checkout_preview():
    try:
        data = request.get_json()
        cart = data.get("cart", {})
        use_points = data.get("use_points", False)

        # calculate total from cart
        total = sum(item["price"] * item["quantity"] for item in cart.values())

        discount = 0
        if use_points:
            session = get_valid_session(db)
            if session:
                user_id = session.get("user_id")
                uid = session.get("card_uid")

                member = None
                if user_id:
                    member = db.child("members").child(user_id).get().val()
                if not member and uid:
                    member = db.child("members").child(uid).get().val()

                if member:
                    points = member.get("bonus_points", 0)
                    discount = min(points // 10, 25)
        final_total = max(0, total - discount)

        return jsonify({
            "success": True,
            "total": total,
            "discount": discount,
            "final_total": final_total
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
        
@pages_bp.route("/card_payment/<order_id>")
def card_payment_page(order_id):
    return render_template("card_payment.html", order_id=order_id)


@pages_bp.route("/order/<order_id>")
def client_order(order_id):
    orders = db.child("orders").get().val() or {}

    for key, data in orders.items():
        if data.get("order_id") == order_id:
            status, remaining = compute_order_status(
                data.get("created_at", ""),
                data.get("estimated_time", 0)
            )
            set_ready_led(status == "ready")
            return render_template("client_order.html", order={
                "id": key,
                "order_id": order_id,
                "display_number": data.get("display_number"),
                "products": data.get("products"),
                "total": data.get("total"),
                "status": status,
                "remaining_time": remaining,
                "payment_method": data.get("payment_method"),
                "payment_status": data.get("payment_status"),
                "time": data.get("time")
            })

    set_ready_led(False)
    return "Order not found", 404
from flask import send_from_directory
import os

@pages_bp.route('/firebase-messaging-sw.js')
def serve_sw():
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), '..', 'static'),
        'firebase-messaging-sw.js',
        mimetype='application/javascript'
    )
@pages_bp.route("/request_enrollment", methods=["POST"])
def request_enrollment():

    db.child("kiosk_command").set({
        "action": "enroll"
    })

    return jsonify({"success": True})
@pages_bp.route("/guest_login", methods=["POST"])
def guest_login():

    db.child("current_session").set({
        "user_id": "guest",
        "card_uid": "",
        "bonus_points": 0,
        "type": "guest",
        "status": "active"
    })

    db.child("current_state").set({
        "state": "logged_in"
    })

    return jsonify({"success": True})
