from flask import Blueprint, render_template
from services.firebase_config import db
from services.hardware_service import set_ready_led
from data import MENU_ITEMS
from utils.order_utils import compute_order_status

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def start():
    return render_template("start.html", menu_items=MENU_ITEMS)


@pages_bp.route("/menu")
def menu():
    return render_template("menu.html", menu_items=MENU_ITEMS)


@pages_bp.route("/checkout")
def checkout():
    return render_template("checkout.html")


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
