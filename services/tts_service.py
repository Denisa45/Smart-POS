import os
import time

def announce_order_ready(name, display_number):
    try:
        from gtts import gTTS
        text = f"{name}, your order number {display_number} is ready. Please come pick it up."
        filename = f"/tmp/order_{display_number}.mp3"
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(filename)

        # wake up bluetooth speaker if suspended
        bt_sink = "bluez_output.30_C0_1B_23_A5_94.1"
        os.system(f"pactl set-default-sink {bt_sink} 2>/dev/null")
        os.system(f"pactl set-sink-volume {bt_sink} 100% 2>/dev/null")

        # play - try bluetooth first, fallback to default
        ret = os.system(f"mpg123 -q --audiodevice {bt_sink} {filename} 2>/dev/null")
        if ret != 0:
            os.system(f"mpg123 -q {filename} 2>/dev/null")

        os.remove(filename)
        print(f"[TTS] Announced order {display_number} for {name}")
    except Exception as e:
        print(f"[TTS ERROR] {e}")
