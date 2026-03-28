from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
from card_service import add_balance

def read_card_uid():
    reader = SimpleMFRC522()
    try:
        card_id, text = reader.read()
        return str(card_id)
    finally:
        GPIO.cleanup()
  
