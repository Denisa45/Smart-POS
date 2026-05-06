import cv2
import numpy as np
import time
import requests
from deepface import DeepFace
import firebase_admin
from firebase_admin import credentials, db

# ---------------- FIREBASE INIT ----------------
cred = credentials.Certificate(
    r"C:\Users\DELL\Desktop\Facultate\iot-kiosk-project\serviceAccountKey.json"
)

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://iot-kiosk-pos-default-rtdb.europe-west1.firebasedatabase.app/"
})

# ---------------- LOAD MEMBERS ----------------
print("🔄 Loading members...")

members_ref = db.reference("members").get()

known_faces = {}

if members_ref:
    for user_id, data in members_ref.items():
        if "embedding" in data:
            known_faces[user_id] = {
                "embedding": np.array(data["embedding"]),
                "card_uid": data.get("card_uid")
            }

print(f"✅ Loaded {len(known_faces)} users")


# ---------------- UTILS ----------------
def cosine_distance(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))


def find_best_match(embedding):
    best_user = None
    best_dist = 999

    for user_id, data in known_faces.items():
        dist = cosine_distance(embedding, data["embedding"])

        if dist < best_dist:
            best_dist = dist
            best_user = user_id

    if best_dist < 0.55:
        return best_user, best_dist

    return None, best_dist


# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0)

print("🚀 Face recognition running... (press Q to quit)")


# ---------------- CONTROL SYSTEM ----------------
SCAN_COOLDOWN = 2
last_scan_time = 0

LOCK_TIME = 5
last_user = None
last_user_time = 0


# ---------------- MAIN LOOP ----------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Face Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    # cooldown (avoid heavy CPU usage)
    if time.time() - last_scan_time < SCAN_COOLDOWN:
        continue

    last_scan_time = time.time()

    try:
        # ---------------- FACE EMBEDDING ----------------
        embedding_obj = DeepFace.represent(
            img_path=frame,
            model_name="Facenet512",
            enforce_detection=False
        )

        embedding = embedding_obj[0]["embedding"]

        # ---------------- MATCH ----------------
        user_id, dist = find_best_match(embedding)

        if not user_id:
            print("❌ No match")
            continue

        # ---------------- ANTI-SPAM LOCK ----------------
        now = time.time()

        if user_id == last_user and (now - last_user_time) < LOCK_TIME:
            continue

        last_user = user_id
        last_user_time = now

        card_uid = known_faces[user_id]["card_uid"]

        print("✅ FOUND:", user_id)
        print("💳 CARD:", card_uid)
        print("📏 DIST:", round(dist, 3))

        # ---------------- SEND TO FLASK ----------------
        try:
            response = requests.post(
                "http://127.0.0.1:5000/face_login",
                json={
                    "user_id": user_id,
                    "card_uid": card_uid,
                    "confidence": float(dist)
                },
                timeout=2
            )

            print("📡 FLASK:", response.json())

        except Exception as e:
            print("❌ Flask error:", e)

    except Exception as e:
        print("⚠️ AI error:", e)

cap.release()
cv2.destroyAllWindows()