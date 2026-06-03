import cv2
import os
import time
import firebase_admin
from firebase_admin import credentials, db as fdb

SERVICE_ACCOUNT = "serviceAccountKey.json"
FIREBASE_URL = "https://iot-kiosk-pos-default-rtdb.europe-west1.firebasedatabase.app/"
MEMBERS_FOLDER = "members"

if not firebase_admin._apps:
    firebase_admin.initialize_app(
        credentials.Certificate(SERVICE_ACCOUNT),
        {"databaseURL": FIREBASE_URL}
    )

def delete_deepface_cache():
    for f in os.listdir(MEMBERS_FOLDER):
        if f.endswith(".pkl"):
            os.remove(os.path.join(MEMBERS_FOLDER, f))
            print(f"[CACHE] Deleted {f}")

def capture_photos(name, count=3):
    folder = os.path.join(MEMBERS_FOLDER, name)
    os.makedirs(folder, exist_ok=True)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera")
        return False

    print(f"[CAM] Taking {count} photos for '{name}'")
    print("Press SPACE to capture, Q to quit")

    captured = 0
    while captured < count:
        ret, frame = cap.read()
        if not ret:
            continue

        display = frame.copy()
        cv2.putText(
            display,
            f"Photo {captured+1}/{count} — press SPACE",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9, (0, 200, 0), 2
        )
        cv2.imshow("Enrollment", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(" "):
            path = os.path.join(folder, f"{captured+1}.jpeg")
            cv2.imwrite(path, frame)
            print(f"[SAVED] {path}")
            captured += 1
            time.sleep(0.5)
        elif key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return captured == count


def ask_diet():
    print("\nDiet preference:")
    print("  1 - No restrictions (eats everything)")
    print("  2 - Vegetarian only")
    choice = input("Choose (1/2): ").strip()
    return ["vegetarian"] if choice == "2" else ["vegetarian", "non_vegetarian"]


def ask_liked_categories():
    print("\nFavourite food categories (your menu has these):")
    categories = ["main", "pizza", "salad", "breakfast", "side", "drink", "dessert", "sauce"]
    for i, c in enumerate(categories, 1):
        print(f"  {i} - {c}")
    print("Enter numbers separated by commas (e.g. 1,3):")
    raw = input("> ").strip()
    selected = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(categories):
                selected.append(categories[idx])
    return selected if selected else ["main"]


def ask_favorite_items():
    print("\nFavourite specific items (optional — press Enter to skip):")
    items = {
        "1": "pizza_margherita",
        "2": "pizza_pepperoni",
        "3": "cheese_burger",
        "4": "chicken_sandwich",
        "5": "veggie_sandwich",
        "6": "turkey_sandwich",
        "7": "caesar_salad",
        "8": "greek_salad",
        "9": "halloumi_salad",
        "10": "pancakes",
        "11": "croissant",
        "12": "ice_cream",
    }
    for k, v in items.items():
        print(f"  {k} - {v.replace('_', ' ').title()}")
    print("Enter numbers separated by commas (or press Enter to skip):")
    raw = input("> ").strip()
    if not raw:
        return []
    selected = []
    for part in raw.split(","):
        part = part.strip()
        if part in items:
            selected.append(items[part])
    return selected


def ask_spicy_level():
    print("\nSpicy food tolerance:")
    print("  1 - None (avoids spicy)")
    print("  2 - Low (mild only)")
    print("  3 - High (loves spicy)")
    choice = input("Choose (1/2/3): ").strip()
    return {"1": "none", "2": "low", "3": "high"}.get(choice, "none")

def ask_budget():
    print("\nMax budget per meal (lei):")
    print("  Budget options: Water 5, Croissant 8, Cola 8")
    print("  Mid range: Veggie Sandwich 17, Greek Salad 18")
    print("  Premium: Pizza Pepperoni 28, Halloumi Salad 21")
    try:
        budget_max = int(input("Max budget (lei, e.g. 30): ").strip() or 30)
    except ValueError:
        budget_max = 30
    return budget_max


def save_to_firebase(name, card_uid, diet, liked_categories, favorite_items, budget_max):
    profile = {
        "name": name,
        "card_uid": card_uid,
        "bonus_points": 0,
        "history": {},
        "total_orders": 0,
        "preferences": {
            "diet": diet,
            "liked_categories": liked_categories,
            "favorite_items": favorite_items,
            "budget_max": budget_max
        }
    }
    fdb.reference(f"members/{name}").set(profile)
    fdb.reference(f"cards/{card_uid}").set({"member_id": name})
    print(f"[FIREBASE] Profile saved for {name}")

def main():
    print("=== KIOSK ENROLLMENT ===")
    name = input("Enter username (lowercase, no spaces): ").strip().lower()
    card_uid = input("Enter card UID (scan or type): ").strip()

    diet             = ask_diet()
    liked_categories = ask_liked_categories()
    favorite_items   = ask_favorite_items()
    spicy_level      = ask_spicy_level()
    budget_max = ask_budget()

    ok = capture_photos(name, count=3)
    if not ok:
        print("[ABORTED] Not enough photos captured")
        return

    delete_deepface_cache()
    save_to_firebase(
        name, card_uid,
        diet, liked_categories, favorite_items,
        budget_max
    )
    print(f"\n[DONE] {name} enrolled successfully!")
    print(f"Photos saved to: members/{name}/")


if __name__ == "__main__":
    main()