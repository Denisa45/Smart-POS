import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
def get_llm_recommendations(member_name, preferences, filtered_menu):
    prompt = f"""
    You are a smart kiosk assistant.

    Customer: {member_name}
    Preferences: {json.dumps(preferences)}
    Menu: {json.dumps(filtered_menu)}

    Rules:
    1. Pick top 3 items based on preferences.
    2. Suggest loyalty rewards (BUT do NOT calculate numbers).
    3. Offer friendly welcome-back message if relevant.

    IMPORTANT:
    - Do NOT change prices
    - Do NOT calculate discounts
    - Only suggest ideas

    Return JSON ONLY:
    {{
        "top_ids": ["id1", "id2", "id3"],
        "pitch": "short marketing message",
        "loyalty_deal": "example: You have enough points for a free drink"
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

        return {
            "top_ids": list(filtered_menu.keys())[:3],
            "pitch": "Here are popular choices for you!",
            "loyalty_deal": "Check your points for possible rewards!"
        }

def get_upsell_pitch(main_item_name, potential_pairs):
    prompt = f"""
    The user added '{main_item_name}' to cart.

    From this list:
    {json.dumps(potential_pairs)}

    Choose ONE best match.

    Rules:
    - Do NOT invent new items
    - Do NOT change prices
    - Only pick from list

    Return JSON:
    {{
        "id": "item_id",
        "name": "item name",
        "price": 0,
        "pitch": "short 3�6 word marketing line"
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
        print(f"Gemini Upsell Error: {e}")

        first = potential_pairs[0]
        return {
            "id": first.get("id", ""),
            "name": first.get("name", ""),
            "price": first.get("price", 0),
            "pitch": "Perfect with your order!"
        }

def get_discount_offer(member_name, preferences, cart_total, bonus_points):
    prompt = f"""
    You are a smart kiosk loyalty system.
    Customer: {member_name}
    Preferences: {json.dumps(preferences)}
    Cart total: {cart_total} lei
    Loyalty points: {bonus_points}

    Decide ONE discount offer from these options only:
    - {{"offer_type": "percentage", "value": 10, "condition": "always", "reason": "short friendly message"}}
    - {{"offer_type": "percentage", "value": 15, "condition": "order_above_40", "reason": "short friendly message"}}
    - {{"offer_type": "fixed", "value": 5, "condition": "always", "reason": "short friendly message"}}
    - {{"offer_type": "none", "value": 0, "condition": "none", "reason": "short friendly message"}}

    Rules:
    - Only offer percentage 15% if cart_total > 40
    - Be generous for returning customers with preferences set
    - Keep reason under 10 words
    - Return JSON ONLY, no extra text

    Return exactly:
    {{
        "offer_type": "percentage" or "fixed" or "none",
        "value": number,
        "condition": "always" or "order_above_40" or "none",
        "reason": "short message"
    }}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        clean = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        print(f"Gemini Discount Error: {e}")
        return {"offer_type": "none", "value": 0, "condition": "none", "reason": ""}