import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

GPIO.setwarnings(False)
reader = SimpleMFRC522()

try:
    print("Apropie cardul...")
    card_id, text = reader.read()
    print("Card ID:", card_id)
    print("Text:", text)
finally:
    GPIO.cleanup()
