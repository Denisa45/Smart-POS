import cv2
import firebase_admin
from firebase_admin import credentials, db
from deepface import DeepFace

# ---------------- FIREBASE INIT ----------------
cred = credentials.Certificate(
    r"C:\Users\DELL\Desktop\Facultate\iot-kiosk-project\serviceAccountKey.json"
)

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://iot-kiosk-pos-default-rtdb.europe-west1.firebasedatabase.app/"
})

# ---------------- INPUT USER ----------------
user_id = input("Enter user name : ").strip()
card_uid = input("Enter card UID: ").strip()

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0)

print("\n📸 Press SPACE to capture face for enrollment")

embedding = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Enroll Face - Press SPACE", frame)

    key = cv2.waitKey(1) & 0xFF

    # SPACE = capture
    if key == 32:
        try:
            print("🔄 Extracting embedding...")

            embedding_obj = DeepFace.represent(
                img_path=frame,
                model_name="Facenet512",
                enforce_detection=True
            )

            embedding = embedding_obj[0]["embedding"]

            print("✅ Face captured!")
            break

        except Exception as e:
            print("❌ No face detected. Try again.", e)

    # Q = quit
    if key == ord("q"):
        cap.release()
        cv2.destroyAllWindows()
        exit()

cap.release()
cv2.destroyAllWindows()

# ---------------- SAVE TO FIREBASE ----------------
if embedding is not None:
    db.reference(f"members/{user_id}").set({
        "card_uid": card_uid,
        "embedding": embedding
    })

    print("\n🔥 Saved to Firebase!")
    print("USER:", user_id)
    print("CARD:", card_uid)

else:
    print("❌ No embedding generated")