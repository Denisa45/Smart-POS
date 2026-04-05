from flask import Flask, render_template
from firebase_config import db
from datetime import datetime

app = Flask(__name__)
def get_order_status_and_remaining(created_at, estimated_time):
    try:
        created_time = datetime.fromisoformat(created_at)
        elapsed = int((datetime.now() - created_time).total_seconds())

        remaining = max(0, estimated_time - elapsed)

        if elapsed < 5:
            status = "pending"
        elif elapsed < estimated_time:
            status = "preparing"
        else:
            status = "ready"

        return status, remaining

    except Exception:
        return "unknown", 0
@app.route("/")
def home():
    readings = db.child("orders").get().val()
    orders_list = []

    total_orders = 0
    total_revenue = 0
    ready_orders = 0
    card_payments = 0

    if readings:
        for firebase_key, order_data in readings.items():
            estimated_time = order_data.get("estimated_time", 0)
            created_at = order_data.get("created_at", "")

            status, remaining_time = get_order_status_and_remaining(created_at, estimated_time)

            order = {
                "id": firebase_key,
                "display_number": order_data.get("display_number", 0),
                "products": order_data.get("products", {}),
                "total": order_data.get("total", 0),
                "estimated_time": estimated_time,
                "remaining_time": remaining_time,
                "status": status,
                "payment_method": order_data.get("payment_method", "Unknown"),
                "time": order_data.get("time", "Unknown")
            }

            orders_list.append(order)

            total_orders += 1
            total_revenue += order["total"]

            if status == "ready":
                ready_orders += 1

            if order["payment_method"] == "Card":
                card_payments += 1

        orders_list.reverse()

    stats = {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "ready_orders": ready_orders,
        "card_payments": card_payments
    }

    return render_template("index.html", orders=orders_list, stats=stats)

@app.route("/order/<order_id>")
def client_order(order_id):
    readings = db.child("orders").get().val()

    if readings:
        for firebase_key, order_data in readings.items():
            if order_data.get("order_id") == order_id:
                estimated_time = order_data.get("estimated_time", 0)
                created_at = order_data.get("created_at", "")
                status, remaining_time = get_order_status_and_remaining(created_at, estimated_time)

                order = {
                    "id": firebase_key,
                    "order_id": order_data.get("order_id", "Unknown"),
                    "display_number": order_data.get("display_number", 0),
                    "products": order_data.get("products", {}),
                    "total": order_data.get("total", 0),
                    "estimated_time": estimated_time,
                    "remaining_time": remaining_time,
                    "status": status,
                    "payment_method": order_data.get("payment_method", "Unknown"),
                    "time": order_data.get("time", "Unknown")
                }

                return render_template("client_order.html", order=order)

    return "Order not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
