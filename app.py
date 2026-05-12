from flask import Flask, render_template, request, jsonify, url_for

from services.firebase_config import db

from services.card_service import process_card_payment

from services.rfid_reader import read_card_uid

from services.session_service import get_valid_session

from services.hardware_service import set_ready_led

from datetime import datetime

import uuid

import time



from data import MENU_ITEMS, PRODUCTS, PREP_TIMES



from services.fb_listener import listen_orders

import threading



#threading.Thread(target=listen_orders, daemon=True).start()
from core.startup import start_background_services




app = Flask(__name__, static_folder="assets", static_url_path="/assets")





# -------------------------

# ORDER STATUS LOGIC (OK here)

# -------------------------

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





# -------------------------

# ROUTES

# -------------------------

@app.route("/")

def start():

    return render_template("start.html")





@app.route("/menu")

def menu():

    return render_template("menu.html", menu_items=MENU_ITEMS)





@app.route("/checkout")

def checkout():

    return render_template("checkout.html")





# -------------------------

# DASHBOARD

# -------------------------

@app.route("/dashboard")

def dashboard():

    readings = db.child("orders").get().val()

    orders_list = []



    stats = {

        "total_orders": 0,

        "total_revenue": 0,

        "ready_orders": 0,

        "card_payments": 0

    }



    if readings:

        for key, order_data in readings.items():

            status, remaining = get_order_status_and_remaining(

                order_data.get("created_at", ""),

                order_data.get("estimated_time", 0)

            )



            order = {

                "id": key,

                "display_number": order_data.get("display_number", 0),

                "products": order_data.get("products", {}),

                "total": order_data.get("total", 0),

                "status": status,

                "remaining_time": remaining,

                "payment_method": order_data.get("payment_method", "Unknown"),

                "time": order_data.get("time", "Unknown")

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





# -------------------------

# SINGLE ORDER VIEW

# -------------------------

@app.route("/order/<order_id>")

def client_order(order_id):

    readings = db.child("orders").get().val()



    if readings:

        for key, order_data in readings.items():

            if order_data.get("order_id") == order_id:



                status, remaining = get_order_status_and_remaining(

                    order_data.get("created_at", ""),

                    order_data.get("estimated_time", 0)

                )



                set_ready_led(status == "ready")



                return render_template("client_order.html", order={

                    "id": key,

                    "order_id": order_id,

                    "display_number": order_data.get("display_number"),

                    "products": order_data.get("products"),

                    "total": order_data.get("total"),

                    "status": status,

                    "remaining_time": remaining,

                    "payment_method": order_data.get("payment_method"),

                    "payment_status": order_data.get("payment_status"),

                    "time": order_data.get("time")

                })



    set_ready_led(False)

    return "Order not found", 404





# -------------------------

# PLACE ORDER

# -------------------------

@app.route("/place_order", methods=["POST"])

def place_order():

    try:

        selected_products = {}

        total = 0

        estimated_time = 0



        for key in request.form:

            if key.startswith("quantity_"):

                product = key.replace("quantity_", "")

                qty = int(request.form.get(key, 0))



                if qty > 0 and product in PRODUCTS:

                    selected_products[product] = qty

                    total += PRODUCTS[product] * qty

                    estimated_time += PREP_TIMES.get(product, 0) * qty



        if not selected_products:

            return jsonify({"success": False, "error": "No products selected"}), 400



        display_number = len(db.child("orders").get().val() or {}) + 1



        order_id = str(uuid.uuid4())[:8]

        created_at = datetime.now().isoformat()



        payment_method = request.form.get("payment_method", "Card")

        payment_status = "paid" if payment_method == "Cash" else "waiting"



        order_data = {

            "order_id": order_id,

            "display_number": display_number,

            "products": selected_products,

            "total": total,

            "estimated_time": estimated_time,

            "payment_method": payment_method,

            "payment_status": payment_status,

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

        return jsonify({"success": False, "error": str(e)}), 500





# -------------------------

# CARD PAYMENT PAGE

# -------------------------
# ~ def rfid_loop():
    # ~ print("[RFID] Loop started")

    # ~ while True:
        # ~ try:
            # ~ uid = read_card_uid()

            # ~ if uid:
                # ~ print("[RFID] Card detected:", uid)

                # ~ # store last scanned card in Firebase
                # ~ db.child("last_card").set({
                    # ~ "uid": uid,
                    # ~ "timestamp": time.time()
                # ~ })

                # ~ # optional LED blink
                # ~ set_ready_led(True)
                # ~ time.sleep(0.2)
                # ~ set_ready_led(False)

                # ~ time.sleep(2)  # debounce (VERY important)

        # ~ except Exception as e:
            # ~ print("[RFID ERROR]", e)

        # ~ time.sleep(0.5)
        
        
@app.route("/card_payment/<order_id>")

def card_payment_page(order_id):

    return render_template("card_payment.html", order_id=order_id)





# -------------------------

# CARD PAYMENT CHECK

# -------------------------

@app.route("/check_card_payment/<order_id>", methods=["POST"])

def check_card_payment(order_id):

    try:

        orders = db.child("orders").get().val()



        target_key = None

        target_order = None



        for key, order in (orders or {}).items():

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

                "redirect_url": url_for("client_order", order_id=order_id)

            })



        # SESSION + CARD FLOW

        session = get_valid_session(db)



        uid = session["card_uid"] if session else read_card_uid()



        if not uid:

            return jsonify({"success": False, "error": "No card detected"}), 400



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

            "redirect_url": url_for("client_order", order_id=order_id)

        })



    except Exception as e:

        import traceback

        traceback.print_exc()

        return jsonify({"success": False, "error": str(e)}), 500



@app.route("/face_login", methods=["POST"])

def face_login():

    print("FACE LOGIN HIT:")

    try:

        data = request.get_json() or {}

        user_id = data.get("user_id")



        if not user_id:

            return jsonify({"success": False, "error": "Missing user_id"}), 400



        user = db.child("members").child(user_id).get().val()



        # ---------------- GUEST ----------------

        if not user:

            db.child("current_session").set({

                "user_id": None,

                "type": "guest",

                "timestamp": time.time()

            })



            set_ready_led(True)



            return jsonify({

                "success": True,

                "type": "guest",

                "next_step": "create_account_or_guest"

            })



        # ---------------- MEMBER ----------------

        session = {

            "user_id": user_id,

            "card_uid": user["card_uid"],

            "type": "member",

            "timestamp": time.time()

        }



        db.child("current_session").set(session)

        set_ready_led(True)



        return jsonify({

            "success": True,

            "type": "member",

            "user_id": user_id,

            "card_uid": user["card_uid"],

            "bonus_points": user.get("bonus_points", 0),

            "next_step": "show_menu"

        })



    except Exception as e:

        return jsonify({"success": False, "error": str(e)}), 500

    

@app.route("/get_state")

def get_state():

    state = db.child("current_state").get().val()

    return jsonify(state or {"state": "waiting_face"})

# -------------------------

# RUN

# -------------------------

if __name__ == "__main__":
    #threading.Thread(target=listen_orders, daemon=True).start()
    #threading.Thread(target=rfid_loop, daemon=True).start()   # 👈 ADD THIS
    start_background_services()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )
