from flask import Flask, render_template, request, redirect, url_for, jsonify
from services.firebase_config import db
from services.card_service import process_card_payment
from datetime import datetime
import uuid
from data import MENU_ITEMS, PRODUCTS, PREP_TIMES

app = Flask(__name__, static_folder="assets", static_url_path="/assets")

# GPIO / LED setup
try:
    from gpiozero import LED
    green_led = LED(17)   # change pin if needed
    GPIO_AVAILABLE = True
except Exception:
    green_led = None
    GPIO_AVAILABLE = False


def set_ready_led(is_ready):
    if GPIO_AVAILABLE and green_led:
        if is_ready:
            green_led.on()
        else:
            green_led.off()


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
def start():
    return render_template("start.html")


@app.route("/menu")
def menu():
    return render_template("menu.html", menu_items=MENU_ITEMS)

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")


@app.route("/dashboard")
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
                    "payment_status": order_data.get("payment_status", "Unknown"),
                    "time": order_data.get("time", "Unknown")
                }
                set_ready_led(status == "ready")
                return render_template("client_order.html", order=order)
    set_ready_led(False)
    return "Order not found", 404
@app.route("/place_order", methods=["POST"])
def place_order():
    try:
        selected_products = {}
        total = 0
        estimated_time = 0

        for key in request.form:
            if key.startswith("quantity_"):
                product_name = key.replace("quantity_", "")
                quantity = int(request.form.get(key, 0))

                if quantity > 0 and product_name in PRODUCTS:
                    selected_products[product_name] = quantity
                    total += PRODUCTS[product_name] * quantity
                    estimated_time += PREP_TIMES.get(product_name, 0) * quantity

        payment_method = request.form.get("payment_method", "Card")

        if not selected_products:
            return jsonify({"success": False, "error": "No products selected"}), 400

        readings = db.child("orders").get().val()
        display_number = 1

        if readings:
            max_display = 0
            for _, order_data in readings.items():
                current_display = order_data.get("display_number", 0)
                if current_display > max_display:
                    max_display = current_display
            display_number = max_display + 1

        order_id = str(uuid.uuid4())[:8]
        created_at = datetime.now().isoformat()

        payment_status = "paid" if payment_method == "Cash" else "waiting"

        order_data = {
            "order_id": order_id,
            "display_number": display_number,
            "products": selected_products,
            "total": total,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "estimated_time": estimated_time,
            "created_at": created_at,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        db.child("orders").push(order_data)
        set_ready_led(False)

        if payment_method == "Card":
            return jsonify({
                "success": True,
                "order_id": order_id,
                "redirect_url": url_for("card_payment_page", order_id=order_id)
            })

        return jsonify({
            "success": True,
            "order_id": order_id,
            "redirect_url": url_for("client_order", order_id=order_id)
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500    return jsonify({"success": False, "error": str(e)}), 500
 @app.route("/card_payment/<order_id>")
def card_payment_page(order_id):
    return render_template("card_payment.html", order_id=order_id)


@app.route("/check_card_payment/<order_id>", methods=["POST"])
def check_card_payment(order_id):
    try:
        readings = db.child("orders").get().val()
        target_key = None
        target_order = None

        if readings:
            for firebase_key, order_data in readings.items():
                if order_data.get("order_id") == order_id:
                    target_key = firebase_key
                    target_order = order_data
                    break

        if not target_order:
            return jsonify({"success": False, "error": "Order not found"}), 404

        if target_order.get("payment_status") == "paid":
            return jsonify({
                "success": True,
                "paid": True,
                "redirect_url": url_for("client_order", order_id=order_id)
            })

        uid = read_card_uid()

        if not uid:
            return jsonify({"success": False, "error": "No card detected"}), 400

        total = target_order.get("total", 0)
        ok, message, new_balance = process_card_payment(uid, total)

        if not ok:
            return jsonify({
                "success": False,
                "error": message,
                "balance": new_balance
            }), 400

        db.child("orders").child(target_key).update({
            "payment_status": "paid",
            "card_uid": uid
        })

        return jsonify({
            "success": True,
            "paid": True,
            "message": message,
            "new_balance": new_balance,
            "redirect_url": url_for("client_order", order_id=order_id)
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)