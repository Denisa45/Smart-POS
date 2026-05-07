from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

print("Place card near reader...")

while True:
    try:
        id, text = reader.read()
        print("CARD DETECTED:", id)
    except Exception as e:
        print("ERROR:", e)
