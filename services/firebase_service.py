from services.firebase_config import db

def get_products():
    return db.child("products").get().val()

def get_product(product_id):
    return db.child(f"products/{product_id}").get().val()

def get_members():
    return db.child("members").get().val()

def get_member(user_id):
    return db.child(f"members/{user_id}").get().val()

def find_member_by_card(card_uid):
    members = get_members() or {}

    for user_id, data in members.items():
        if data.get("card_uid") == card_uid:
            return user_id, data

    return None, None
def get_orders():
    return db.child("orders").get().val()

def get_order(order_id):
    return db.child(f"orders/{order_id}").get().val()

def save_order(order):
    return db.child("orders").push(order)

def update_member(user_id, data):
    return db.child(f"members/{user_id}").update(data)

def update_points(user_id, points):
    ref = db.child(f"members/{user_id}/points")
    current = ref.get().val() or 0
    ref.set(current + points)