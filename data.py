MENU_ITEMS = [
    {
        "name": "Classic Ham Sandwich",
        "price": 18,
        "prep_time": 12,
        "emoji": "🥪",
        "description": "Ham, cheese, lettuce, tomato."
    },
    {
        "name": "Chicken Sandwich",
        "price": 20,
        "prep_time": 14,
        "emoji": "🥪",
        "description": "Chicken, salad, creamy sauce."
    },
    {
        "name": "Turkey Sandwich",
        "price": 21,
        "prep_time": 14,
        "emoji": "🥪",
        "description": "Turkey, cheese, fresh vegetables."
    },
    {
        "name": "Veggie Sandwich",
        "price": 17,
        "prep_time": 10,
        "emoji": "🥪",
        "description": "Salad, tomato, cucumber, cheese."
    },
    {
        "name": "Toast Sandwich",
        "price": 16,
        "prep_time": 9,
        "emoji": "🍞",
        "description": "Warm toasted bread with ham and cheese."
    },
    {
        "name": "Cheese Burger",
        "price": 22,
        "prep_time": 20,
        "emoji": "🍔",
        "description": "Burger, cheddar, lettuce, sauce."
    },
    {
        "name": "French Fries",
        "price": 10,
        "prep_time": 8,
        "emoji": "🍟",
        "description": "Golden crispy fries."
    },
    {
        "name": "Cola",
        "price": 8,
        "prep_time": 2,
        "emoji": "🥤",
        "description": "Cold fizzy drink."
    },
    {
        "name": "Water",
        "price": 5,
        "prep_time": 1,
        "emoji": "💧",
        "description": "Still water."
    },
    {
        "name": "Ice Cream",
        "price": 7,
        "prep_time": 3,
        "emoji": "🍨",
        "description": "Sweet cold dessert."
    },
    {
        "name": "Coffee",
        "price": 9,
        "prep_time": 4,
        "emoji": "☕",
        "description": "Fresh hot coffee."
    }
]

PRODUCTS = {item["name"]: item["price"] for item in MENU_ITEMS}
PREP_TIMES = {item["name"]: item["prep_time"] for item in MENU_ITEMS}