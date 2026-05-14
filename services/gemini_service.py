import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_llm_recommendations(member_name, preferences, filtered_menu):
    prompt = f"""
    You are a smart Kiosk Sales Assistant.
    Customer: {member_name}
    Preferences: {json.dumps(preferences)}
    Menu: {json.dumps(filtered_menu)}

    Rules:
    1. Pick top 3 items based on preferences.
    2. If preferences include bonus_points >= 50, suggest using points for a side or drink.
    3. Offer a 10% Welcome Back discount on one specific item if relevant.

    Response format (JSON only, no markdown):
    {{
        "top_ids": ["id1", "id2", "id3"],
        "pitch": "The main message",
        "loyalty_deal": "e.g., Use 50 points for a free Coffee!",
        "discount_applied": {{"item_id": "pizza_margherita", "new_price": 22.5}}
    }}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        print("Gemini Error:", e)

        fallback_ids = list(filtered_menu.keys())[:3]

        return {
            "top_ids": fallback_ids,
            "pitch": "Here are some popular choices for you!"
        }


def get_upsell_pitch(main_item_name, potential_pairs):
    prompt = (
        f"The user just added '{main_item_name}' to their cart. "
        f"Pick the single best matching item from this list: {json.dumps(potential_pairs)}. "
        f"Return JSON only (no markdown): "
        f'{{ "id": "item_id", "name": "item name", "price": 0.0, "pitch": "Short 5-word pitch" }}'
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"Gemini Upsell Error: {e}")
        first = potential_pairs[0]
        return {
            "id": first.get("id", ""),
            "name": first.get("name", ""),
            "price": first.get("price", 0),
            "pitch": "Goes great with that!"
        }
