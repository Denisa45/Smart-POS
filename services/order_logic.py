from datetime import datetime


def calculate_total(order, products):
    return sum(products[p] * q for p, q in order.items())


def calculate_prep_time(order, prep_times):
    return sum(prep_times[p] * q for p, q in order.items())


def build_order_data(order, products, prep_times, payment_method, db):
    total = calculate_total(order, products)
    estimated_time = calculate_prep_time(order, prep_times)

    now = datetime.now()
    order_id = now.strftime("ORD%Y%m%d%H%M%S")

    # 🔥 get number of existing orders
    existing_orders = db.child("orders").get().val()
    if existing_orders:
        display_number = len(existing_orders) + 1
    else:
        display_number = 1

    return {
        "order_id": order_id,
        "display_number": display_number,
        "products": order.copy(),
        "total": total,
        "estimated_time": estimated_time,
        "time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "created_at": now.isoformat(),
        "status": "pending",
        "payment_method": payment_method
    }
