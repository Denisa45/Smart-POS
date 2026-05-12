from flask import Blueprint, render_template
from services.firebase_config import db
from utils.order_utils import compute_order_status

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    readings = db.child("orders").get().val() or {}
    orders_list = []
    stats = {
        "total_orders": 0,
        "total_revenue": 0,
        "ready_orders": 0,
        "card_payments": 0
    }

    for key, data in readings.items():
        status, remaining = compute_order_status(
            data.get("created_at", ""),
            data.get("estimated_time", 0)
        )
        order = {
            "id": key,
            "display_number": data.get("display_number", 0),
            "products": data.get("products", {}),
            "total": data.get("total", 0),
            "status": status,
            "remaining_time": remaining,
            "payment_method": data.get("payment_method", "Unknown"),
            "time": data.get("time", "Unknown")
        }
        orders_list.append(order)
        stats["total_orders"] += 1
        stats["total_revenue"] += order["total"]
        if status == "ready":
            stats["ready_orders"] += 1
        if order["payment_method"] == "Card":
            stats["card_payments"] += 1

    orders_list.reverse()
    return render_template("index.html", orders=orders_list, stats=stats)
