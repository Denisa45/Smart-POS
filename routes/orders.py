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
 
        # 1. Build cart from request
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
 
        # 2. Order basics
        existing = db.child("orders").get().val() or {}
        display_number = len(existing) + 1
        order_id = str(uuid.uuid4())[:8]
        now = datetime.now()
 
        payment_method = request.form.get("payment_method", "Card")
        use_points = request.form.get("use_points") == "1"
        payment_status = "paid" if payment_method == "Cash" else "waiting"
 
        # 3. LOYALTY DISCOUNT
        discount_used = 0
        uid = None
        user_id = None
        current_points = 0
 
        session = get_valid_session(db)
        if session:
            uid = session.get("card_uid")
            user_id = session.get("user_id")
        if not uid:
            import time as _time
            last_card = db.child("last_card").get().val() or {}
            card_ts = last_card.get("timestamp", 0)
            if _time.time() - card_ts < 120:
                uid = last_card.get("uid")
        # only block if card payment and no card found
        if not uid and payment_method != "Cash":
            return jsonify({"success": False, "error": "Please tap your card to pay"}), 400
 
        if use_points and session:
            member = None
            if user_id:
                member = db.child("members").child(user_id).get().val()
            if not member and uid:
                member = db.child("members").child(uid).get().val()
            if member:
                current_points = member.get("bonus_points", 0)
                discount_used = min(current_points // 10, 25)
                total -= discount_used
                points_to_remove = discount_used * 10
                member_key = user_id if user_id else uid
                db.child("members").child(member_key).update({
                    "bonus_points": max(0, current_points - points_to_remove)
                })
 
        # 4. GEMINI DISCOUNT (from checkout offer)
        gemini_data = None
        gemini_discount = int(request.form.get("gemini_discount", 0))
        gemini_discount = min(gemini_discount, 25)
        total -= gemini_discount
 
        try:
            from services.gemini_service import get_llm_recommendations
            member_name = user_id or uid or "Guest"
            gemini_data = get_llm_recommendations(
                member_name=member_name,
                preferences={"points": current_points, "discount_used": discount_used},
                filtered_menu=products
            )
        except Exception as e:
            print("Gemini error:", e)
 
        # 5. SAVE ORDER
        order_data = {
            "order_id": order_id,
            "display_number": display_number,
            "products": selected_products,
            "total": total,
            "estimated_time": estimated_time,
            "earned_points": total_bonus,
            "discount_used": discount_used,
            "gemini_discount": gemini_discount,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "card_uid": uid,        # always save card_uid
            "user_id": user_id,    # always save user_id
            "created_at": now.isoformat(),
            "time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "gemini": gemini_data
        }
 
        db.child("orders").push(order_data)
 
        # 6. CASH ORDERS — add points immediately (no card payment step)
        if payment_method == "Cash" and session:
            member_key = user_id if user_id else uid
            if member_key:
                member = db.child("members").child(member_key).get().val() or {}
                current_pts = member.get("bonus_points", 0)
                db.child("members").child(member_key).update({
                    "bonus_points": current_pts + total_bonus
                })
                print(f"[LOYALTY] Cash order — added {total_bonus} points to {member_key}")
 
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
 
         
@orders_bp.route("/checkout_preview", methods=["POST"])
def checkout_preview():
    try:
        data = request.get_json()

        cart = data.get("cart", {})
        use_points = data.get("use_points", False)

        products = get_products() or {}

        total = 0
        estimated_time = 0

        for product_id, qty in cart.items():
            if product_id in products:
                item = products[product_id]
                total += item["price"] * qty
                estimated_time += item["prep_time"] * qty

        session = get_valid_session(db)
        uid = session.get("card_uid") if session else None

        discount = 0
        points_after = 0

        if use_points and uid:
            member = db.child("members").child(uid).get().val() or {}
            points = member.get("bonus_points", 0)

            discount = min(points // 10, 25)
            discount = min(discount, total)

            points_after = max(0, points - (discount * 10))

        return jsonify({
            "success": True,
            "total": total,
            "discount": discount,
            "final_total": max(0, total - discount),
            "points_after": points_after
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
        uid = session.get("card_uid") if session else None
        if not uid:
            import time as _time
            last_card = db.child("last_card").get().val() or {}
            if _time.time() - last_card.get("timestamp", 0) < 300:
                uid = last_card.get("uid")
        if not uid:
            return jsonify({"success": False, "error": "Please tap your card to pay"}), 400

        ok, message, new_balance = process_card_payment(uid, target_order["total"])
        if not ok:
            return jsonify({"success": False, "error": message}), 400

        db.child("orders").child(target_key).update({
            "payment_status": "paid",
            "card_uid": uid,
            "status": "ready"
        })
        # announce order ready immediately after payment
        try:
            from services.tts_service import announce_order_ready
            from services.fcm_service import send_order_ready_notification
            session = get_valid_session(db)
            user_id = session.get("user_id", "guest") if session else "guest"
            customer_name = user_id.capitalize() if user_id and user_id != "guest" else "Customer"
            display_num = target_order.get("display_number", "?")
            print(f"[TTS] Announcing order {display_num} ready for {customer_name}")
            announce_order_ready(customer_name, display_num)
            # send push notification
            token_data = db.child("fcm_tokens").child(order_id).get().val()
            if not token_data:
                token_data = db.child("fcm_tokens").child("latest").get().val()
            if token_data and token_data.get("token"):
                send_order_ready_notification(token_data["token"], display_num)
                print(f"[FCM] Push sent for order {display_num}")
        except Exception as tts_e:
            print(f"[TTS/FCM ERROR] {tts_e}")
        member = db.child("members").child(uid).get().val() or {}

        current_points = member.get("bonus_points", 0)

        earned_points = target_order.get("earned_points", 0)

        db.child("members").child(uid).update({
            "bonus_points": current_points + earned_points
        })

        print(f"[LOYALTY] Added {earned_points} points to {uid}")

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
    earned_points = order.get("earned_points", 0)
    total_points = 0

    # try user_id first (fastest)
    order_user_id = order.get("user_id")
    if order_user_id:
        member = db.child("members").child(order_user_id).get().val()
        if member:
            total_points = member.get("bonus_points", 0)

    # fallback: search by card_uid
    if total_points == 0:
        card_uid = order.get("card_uid")
        if card_uid:
            all_members = db.child("members").get().val() or {}
            for name, mdata in all_members.items():
                if isinstance(mdata, dict) and str(mdata.get("card_uid", "")) == str(card_uid):
                    total_points = mdata.get("bonus_points", 0)
                    break
    return render_template(
    "mobile_track.html",
    order=order,
    order_id=order_id,
    earned_points=earned_points,
    total_points=total_points
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
        # also save as latest so it's always findable
        db.child("fcm_tokens").child("latest").set({"token": token})
        return jsonify({"success": True})
    return jsonify({"success": False}), 400
