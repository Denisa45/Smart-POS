from gpiozero import LED

GPIO_AVAILABLE = True

try:
    green_led = LED(17)
    print("[GPIO] LED initialized on GPIO17")
except Exception as e:
    green_led = None
    GPIO_AVAILABLE = False
    print("[GPIO ERROR]", e)


def set_ready_led(state: bool):
    print("[LED STATE]", state)

    if not GPIO_AVAILABLE or green_led is None:
        print("[LED SKIPPED] GPIO not available")
        return

    try:
        if state:
            green_led.on()
            print("[LED] ON")
        else:
            green_led.off()
            print("[LED] OFF")

    except Exception as e:
        print("[LED ERROR]", e)
