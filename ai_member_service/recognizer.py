"""
Face recognition kiosk script.
- Recognises faces and writes full session to Firebase
- Pauses recognition while an order is in progress
- Triggers enrollment when no face is detected for a timeout
ai_env\Scripts\activate

"""

import os
import sys
import time
import warnings

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
warnings.filterwarnings("ignore")

import tensorflow as tf
tf.get_logger().setLevel("ERROR")

import cv2
import firebase_admin
from firebase_admin import credentials, db as fdb
from deepface import DeepFace
from 
import enroll

# ── Config ────────────────────────────────────────────────────────────────────
MEMBERS_FOLDER    = "members"
SERVICE_ACCOUNT   = "serviceAccountKey.json"
FIREBASE_URL      = "https://iot-kiosk-pos-default-rtdb.europe-west1.firebasedatabase.app/"
COOLDOWN_SEC      = 10    # min seconds between same-user triggers
NO_FACE_TIMEOUT   = 5     # seconds of no recognition before enrollment
ORDER_POLL_SEC    = 2     # how often to check if order is done
# ─────────────────────────────────────────────────────────────────────────────

if not firebase_admin._apps:
    firebase_admin.initialize_app(
        credentials.Certificate(SERVICE_ACCOUNT),
        {"databaseURL": FIREBASE_URL}
    )

session_ref = fdb.reference("current_session")
state_ref   = fdb.reference("current_state")


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_user_id(identity_path: str) -> str:
    parts = identity_path.replace("\\", "/").split("/")
    return parts[1] if len(parts) >= 2 else parts[0]


def write_session(user_id: str):
    """Write a full session with card_uid and bonus_points to Firebase."""
    try:
        member = fdb.reference(f"members/{user_id}").get() or {}
        card_uid     = str(member.get("card_uid", ""))
        bonus_points = member.get("bonus_points", 0)
    except Exception as e:
        print(f"[FIREBASE] Could not fetch member data: {e}")
        card_uid     = ""
        bonus_points = 0

    session_ref.set({
        "user_id":      user_id,
        "card_uid":     card_uid,
        "bonus_points": bonus_points,
        "type":         "member" if card_uid else "guest",
        "status":       "active",
        "timestamp":    time.time()
    })
    print(f"[FIREBASE] Session written → user={user_id} | card={card_uid} | points={bonus_points}")


def is_order_in_progress() -> bool:
    """
    Returns True if the kiosk is still in an active order state.
    Flask resets current_state to waiting_face after logout/completion.
    """
    try:
        state = state_ref.get() or {}
        current_state = state.get("state", "")
        if current_state in ("waiting_face", "idle", ""):
            return False
        session = session_ref.get() or {}
        if not session or not session.get("user_id"):
            return False
        return True
    except Exception as e:
        print(f"[POLL ERROR] {e}")
        return False


def wait_for_order_completion():
    """Block until the order is done and kiosk is back to waiting state."""
    print("[KIOSK] Order in progress — pausing recognition...", end="", flush=True)
    while True:
        if not is_order_in_progress():
            print(" done!")
            return
        print(".", end="", flush=True)
        time.sleep(ORDER_POLL_SEC)


def run_enrollment(cap):
    """Release camera, run enrollment, then reopen camera."""
    print("[KIOSK] No face recognised — launching enrollment...")
    cap.release()
    cv2.destroyAllWindows()
    enroll.main()
    print("[KIOSK] Enrollment finished — resuming recognition.")
    new_cap = cv2.VideoCapture(0)
    if not new_cap.isOpened():
        sys.exit("[ERROR] Cannot reopen camera after enrollment")
    
    return new_cap

def write_guest_session():
    session_ref.set({
        "user_id": "",
        "card_uid": "",
        "bonus_points": 0,
        "type": "guest",
        "status": "active",
        "timestamp": time.time()
    })
    print("[FIREBASE] Guest session created")

# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit("[ERROR] Cannot open camera")

    print("[KIOSK] Face recognition running. Press Q to quit.")

    last_user            = None
    last_trigger_time    = 0
    last_recognised_time = time.time()
    frame_count          = 0  # ADD THIS

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        frame_count += 1
        recognised = False

        # Only run DeepFace every 10 frames so the window stays responsive
        if frame_count % 10 == 0:
            try:
                results = DeepFace.find(
                    img_path          = frame,
                    db_path           = MEMBERS_FOLDER,
                    enforce_detection = False,
                    silent            = True
                )

                if results and len(results[0]) > 0:
                    top = results[0].iloc[0]
                    
                    # ADD confidence threshold — only accept close matches
                    if top["distance"] < 0.4:
                        user_id = extract_user_id(top["identity"])
                        now     = time.time()
                        recognised           = True
                        last_recognised_time = now

                        if user_id == last_user and now - last_trigger_time < COOLDOWN_SEC:
                            pass
                        else:
                            print(f"[RECOGNISED] {user_id}")
                            write_session(user_id)
                            last_user         = user_id
                            last_trigger_time = now
                            wait_for_order_completion()
                            last_user            = None
                            last_trigger_time    = 0
                            last_recognised_time = time.time()

            except Exception as e:
                print(f"[ERROR] {e}")

        if not recognised:
            elapsed   = time.time() - last_recognised_time
            remaining = max(0, NO_FACE_TIMEOUT - elapsed)

            label = (
                f"No face detected... enrolling in {remaining:.0f}s"
                if remaining > 0
                else "Launching enrollment..."
            )
            cv2.putText(
                frame, label,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 100, 255), 2
            )

            if elapsed >= NO_FACE_TIMEOUT:

                state_ref.set({
                    "state": "choose_login"
                })

                print("[KIOSK] Waiting for guest/enroll selection...")

                while True:
                    cmd = fdb.reference("kiosk_command").get() or {}
                    action = cmd.get("action", "")

                    if action == "guest":
                        write_guest_session()

                        fdb.reference("kiosk_command").set({})
                        wait_for_order_completion()

                        last_recognised_time = time.time()
                        break

                    elif action == "enroll":
                        fdb.reference("kiosk_command").set({})

                        cap = run_enrollment(cap)

                        last_recognised_time = time.time()
                        break

                    time.sleep(0.5)

                continue

        cv2.imshow("AI Kiosk", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()