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
