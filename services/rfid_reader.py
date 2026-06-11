from mfrc522 import SimpleMFRC522
import time
from core.state import StateManager, KioskState
from services.firebase_config import db

reader = SimpleMFRC522()

def read_card_uid():
    try:
        card_id, text = reader.read_no_block()
        if card_id:
            return str(card_id)
        return None
    except Exception as e:
        print("RFID error:", e)
        return None

def rfid_loop():
    print("[RFID] Loop started")
    last_uid = None
    last_time = 0
    debounce_sec = 10  # don't re-trigger same card for 10 seconds

    while True:
        uid = read_card_uid()
        if uid:
            now = time.time()
            if uid == last_uid and (now - last_time < debounce_sec):
                time.sleep(0.3)
                continue  # same card still in range, ignore

            # check current state � only login from waiting screen
            current_state = db.child("current_state").get().val() or {}
            state_val = current_state.get("state", "waiting_face")

            print(f"[RFID] Card detected: {uid} (state={state_val})")
            db.child("last_card").set({"uid": uid, "timestamp": now})

            if state_val in ("waiting_face", "choose_login"):
                # login flow
                card_data = db.child("cards").child(uid).get().val() or {}
                member_id = card_data.get("member_id")

                if member_id:
                    member = db.child("members").child(member_id).get().val() or {}
                    db.child("current_session").set({
                        "user_id": member_id,
                        "card_uid": uid,
                        "bonus_points": member.get("bonus_points", 0),
                        "type": "member",
                        "status": "active",
                        "timestamp": now
                    })
                    StateManager.set(KioskState.LOGGED_IN, user=member_id)
                    print(f"[RFID] Member login: {member_id}")
                else:
                    db.child("current_session").set({
                        "user_id": "guest",
                        "card_uid": uid,
                        "bonus_points": 0,
                        "type": "guest",
                        "status": "active",
                        "timestamp": now
                    })
                    StateManager.set(KioskState.LOGGED_IN, user="guest")
                    print(f"[RFID] Unknown card {uid} - guest with card")
            else:
                # during session - just update last_card for payment, don't change login
                print(f"[RFID] Card stored for payment: {uid}")

            last_uid = uid
            last_time = now

        time.sleep(0.3)
