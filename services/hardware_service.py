try:
    from gpiozero import LED
    green_led = LED(17)
    GPIO_AVAILABLE = True
except:
    green_led = None
    GPIO_AVAILABLE = False


def set_ready_led(state: bool):
    if not GPIO_AVAILABLE:
        return

    if state:
        green_led.on()
    else:
        green_led.off()