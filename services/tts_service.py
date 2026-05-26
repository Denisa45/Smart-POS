import os
import time

def announce_order_ready(name, display_number):
    try:
        from gtts import gTTS

        text = f"{name}, your order number {display_number} is ready. Please come pick it up."
        filename = f"/tmp/order_{display_number}.mp3"

        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filename)

        # play via paplay through default sink (JBL)
        os.system(f"mpg123 -q --audiodevice bluez_output.30_C0_1B_23_A5_94.1 {filename} 2>/dev/null")
        os.remove(filename)
        print(f"[TTS] Announced order {display_number} for {name}")

    except Exception as e:
        print(f"[TTS ERROR] {e}")