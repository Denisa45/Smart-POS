from mfrc522 import SimpleMFRC522
import time
from core.state import StateManager, KioskState

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
    debounce_sec = 2

    while True:
        uid = read_card_uid()
        if uid:
            now = time.time()
            if uid != last_uid or (now - last_time > debounce_sec):
                print("[RFID] Card detected:", uid)
                StateManager.set(KioskState.CARD_DETECTED, uid)
                last_uid = uid
                last_time = now
        time.sleep(0.3)
