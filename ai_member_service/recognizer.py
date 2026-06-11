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

import enroll

# ── Config ────────────────────────────────────────────────────────────────────
MEMBERS_FOLDER    = "members"
SERVICE_ACCOUNT   = "serviceAccountKey.json"
FIREBASE_URL      = "https://iot-kiosk-pos-default-rtdb.europe-west1.firebasedatabase.app/"
COOLDOWN_SEC      = 15    # min seconds between same-user triggers
NO_FACE_TIMEOUT   = 999   # effectively disabled
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
    print("[KIOSK] Order in progress â€” pausing recognition...", end="", flush=True)
    while True:
        # exit if new enrollment command arrives â€” don't block it
        cmd = fdb.reference("kiosk_command").get() or {}
        if cmd.get("action") == "enroll":
            print(" interrupted by enrollment!")
            return
        if not is_order_in_progress():
            reset_kiosk_state()
            print(" done!")
            return
        print(".", end="", flush=True)
        time.sleep(ORDER_POLL_SEC)
        
def run_enrollment(cap, name: str):
    """Release camera, capture face photos, signal done to Firebase."""
    print(f"[KIOSK] Starting enrollment for: {name}")
    cap.release()
    cv2.destroyAllWindows()

    # Signal we're capturing
    fdb.reference("enrollment_request").update({"status": "capturing"})

    # Open camera fresh for capture
    cap2 = cv2.VideoCapture(0)
    if not cap2.isOpened():
        sys.exit("[ERROR] Cannot reopen camera for enrollment")

    os.makedirs(f"members/{name}", exist_ok=True)
    count = 0
    needed = 20

    print(f"[ENROLL] Capturing {needed} photos for {name}... look at the camera!")
    while count < needed:
        ret, frame = cap2.read()
        if not ret:
            time.sleep(0.1)
            continue
        cv2.putText(frame, f"Enrolling {name}: {count}/{needed}",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 0), 2)
        cv2.imshow("Enrollment", frame)
        cv2.waitKey(1)
        path = f"members/{name}/{name}_{count}.jpg"
        cv2.imwrite(path, frame)
        count += 1
        time.sleep(0.1)

    cap2.release()
    cv2.destroyAllWindows()

    # Signal done — Pi will see this via /enrollment_status
    fdb.reference("enrollment_request").set({"status": "done", "name": name})
    print(f"[ENROLL] Done — {name} enrolled with {needed} photos.")

    # Reopen main camera
    new_cap = cv2.VideoCapture(0)
    if not new_cap.isOpened():
        sys.exit("[ERROR] Cannot reopen camera after enrollment")
    reset_kiosk_state()
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


def reset_kiosk_state():
    """Fully reset Firebase so Pi returns to waiting screen."""
    try:
        fdb.reference("current_session").delete()
    except Exception:
        # fallback if delete not supported
        fdb.reference("current_session").set({
            "user_id": None,
            "card_uid": "",
            "bonus_points": 0,
            "type": "none",
            "status": "idle",
            "timestamp": time.time()
        })
    fdb.reference("current_state").set({
        "state": "waiting_face",
        "user": None,
        "timestamp": time.time()
    })
    print("[RESET] Firebase kiosk state reset done")


# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit("[ERROR] Cannot open camera")

    print("[KIOSK] Warming up camera...")
    time.sleep(2)
    print("[KIOSK] Face recognition running. Press Q to quit.")

    last_user            = None
    last_trigger_time    = 0
    last_recognised_time = time.time()
    frame_count          = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        frame_count += 1
        recognised = False

        # check for enrollment command from Pi
        if frame_count % 10 == 0:
            cmd = fdb.reference("kiosk_command").get() or {}
            action = cmd.get("action")
        else:
            action = None
        if action == "enroll":
            print("===================================")
            print("[KIOSK] ENROLL TRIGGER RECEIVED")
            fdb.reference("kiosk_command").set({})
            enroll_data = fdb.reference("enrollment_request").get() or {}
            name = enroll_data.get("name", "unknown")
            print(f"[DEBUG] Enrolling user: {name}")
            print("===================================")
            cap = run_enrollment(cap, name)
            print("[KIOSK] Returned from enrollment")
            last_user            = None
            last_trigger_time    = 0
            last_recognised_time = time.time() + 5
            continue

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
                            fdb.reference("current_state").set({
                                "state": "logged_in",
                                "user": user_id,
                                "timestamp": time.time()
                            })
                            last_user         = user_id
                            last_trigger_time = now
                            wait_for_order_completion()
                            print("[KIOSK] Cooldown — waiting 5s before next recognition...")
                            time.sleep(5)
                            last_user            = None
                            last_trigger_time    = 0
                            last_recognised_time = time.time()

            except Exception as e:
                print(f"[ERROR] {e}")

        if not recognised:
            elapsed = time.time() - last_recognised_time
            cv2.putText(
                frame, "Scanning...",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 100, 255), 2
            )
            if elapsed >= NO_FACE_TIMEOUT:
                last_recognised_time = time.time()
                continue

        cv2.imshow("AI Kiosk", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    while True:
        try:
            main()
        except KeyboardInterrupt:
            print("\n[KIOSK] Stopped by user.")
            break
        except Exception as e:
            print(f"[CRASH] {e} — restarting in 3s...")
            time.sleep(3)