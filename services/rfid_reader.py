from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

def read_card_uid():
    try:
        card_id, text = reader.read()
        return str(card_id)
    except Exception as e:
        print("RFID error:", e)
        return None
