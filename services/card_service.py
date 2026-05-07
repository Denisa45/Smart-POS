from services.firebase_config import db

def get_card(uid):
    return db.child("cards").child(str(uid)).get().val()

def get_balance(uid):
    card = get_card(uid)
    if card:
        return card.get("balance", 0)
    return None

def has_sufficient_funds(uid, amount):
    balance = get_balance(uid)
    if balance is None:
        return False, "Card inexistent"
    elif balance < amount:
        return False, "Fonduri insuficiente"
    return True, "OK"

def deduct_balance(uid, amount):
    card= get_card(uid)
    if not card:
        return None
    
    balance = card.get("balance",0)

    if(balance<amount):
        return None
    
    new_balance=balance-amount

    db.child("cards").child(str(uid)).update({"balance":new_balance})

    return new_balance 

def process_card_payment(uid, amount):
    card = get_card(uid)

    if not card:
        return False, "Card necunoscut", None

    balance = card.get("balance", 0)

    if balance < amount:
        return False, "Fonduri insuficiente", balance

    new_balance = deduct_balance(uid, amount)

    if new_balance is None:
        return False, "Eroare tranzacție", None

    return True, "Tranzacție efectuată", new_balance

def add_balance(uid, amount):
    card = get_card(uid)

    if not card:
        db.child("cards").child(str(uid)).set({
            "balance": amount
        })
        return True, "Card creat și încărcat", amount

    balance = card.get("balance", 0)
    new_balance = balance + amount

    db.child("cards").child(str(uid)).update({"balance": new_balance})

    return True, "Sold actualizat", new_balance
