from gpiozero import LED

GPIO_AVAILABLE = True
last_state = None  # track last state to avoid toggling on every request

try:
    green_led = LED(17)
    yellow_led = LED(27)
    print("[GPIO] LEDs initialized on GPIO17 (green) and GPIO27 (yellow)")
except Exception as e:
    green_led = None
    yellow_led = None
    GPIO_AVAILABLE = False
    print("[GPIO ERROR]", e)


def set_ready_led(state: bool):
    global last_state
    if not GPIO_AVAILABLE or green_led is None or yellow_led is None:
        print("[LED SKIPPED] GPIO not available")
        return
    if state == last_state:
        return  # ? no change, don't touch the LEDs
    last_state = state
    try:
        if state:
            yellow_led.off()
            green_led.on()
            print("[LED] Green ON, Yellow OFF")
        else:
            green_led.off()
            yellow_led.on()
            print("[LED] Yellow ON, Green OFF")
    except Exception as e:
        print("[LED ERROR]", e)