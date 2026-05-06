import os
import cv2
from deepface import DeepFace
# Ensure you have firebase_admin initialized in your main app
from firebase_admin import firestore 

db = firestore.client()

def pos_face_login(frame):
    try:
        # Use Facenet512 for speed (faster than VGG-Face)
        results = DeepFace.find(img_path=frame, 
                                db_path="members", 
                                model_name="Facenet512",
                                enforce_detection=True)
        
        if len(results) > 0 and not results[0].empty:
            # 1. Get name from file (e.g., 'denisa')
            match_path = results[0]['identity'][0]
            customer_id = os.path.basename(match_path).split(".")[0]
            
            # 2. Fetch data from your existing Firebase
            customer_ref = db.collection('users').document(customer_id)
            doc = customer_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return {"name": customer_id, "points": data.get('points', 0), "orders": data.get('orders', [])}
                
        return None
    except Exception as e:
        print(f"Login Error: {e}")
        return None
import os
import cv2
from deepface import DeepFace
from services.facial_recognition.firebase_config_fr import db  # Import your existing connection

def recognize_and_fetch():
    # ... your facial recognition code ...
    customer_id = "denisa" # The name found by the camera
    
    # Use your existing 'db' to get the orders
    customer_ref = db.collection('users').document(customer_id)
    doc = customer_ref.get()
    
    if doc.exists:
        print(f"Data for {customer_id}: {doc.to_dict()}")
    else:
        print(f"No data found for {customer_id}")