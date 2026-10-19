# Smart POS

Smart POS is a self-service kiosk project built with Python, Tkinter, Flask, and Firebase.

## Features
- product ordering interface
- cart and checkout
- Firebase order storage
- kitchen display page
- client order tracking page
- automatic order status: pending -> preparing -> ready

## Project structure
- `kiosk_gui.py` - customer kiosk interface
- `app.py` - Flask dashboard and tracking pages
- `data.py` - products and preparation times
- `firebase_config.py` - Firebase connection
- `order_logic.py` - order calculations and order data builder
- `templates/` - Flask HTML pages

## Run
```bash
python kiosk_gui.py
python app.py

## Run the web part without the Raspberry Pi (no RFID / LEDs)
The RFID reader (`mfrc522`) and LEDs (`gpiozero`) are optional. On a normal laptop:

```bash
pip install flask pyrebase4 firebase-admin python-dotenv google-genai gtts
python app.py
```

Then open:
- `http://localhost:5000/` - the kiosk
- `http://localhost:5000/simulate_card` - pick or type a card UID and press **Tap card**.
  This does exactly what tapping the real card does (member login on the start
  screen, payment on the card payment page).

Without the Pi the app prints `[RFID] Reader not available` and `[LED SKIPPED]` and keeps going.
Push notifications need `serviceAccountKey.json`; without it they are skipped.
Pay with **Cash** to skip the card step entirely.
