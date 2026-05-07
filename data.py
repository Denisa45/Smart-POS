MENU_ITEMS = [
    {
        "name": "Cheese Burger",
        "price": 22,
        "prep_time": 20,
        "image": "cheese_burger.png"
    },
    {
        "name": "Chicken Sandwich",
        "price": 20,
        "prep_time": 14,
        "image": "chicken_sandwich.png"
    },
    {
        "name": "Classic Ham Sandwich",
        "price": 18,
        "prep_time": 12,
        "image": "classic_ham_sandwich.png"
    },
    {
        "name": "Coffee",
        "price": 9,
        "prep_time": 4,
        "image": "coffe.png"
    },
    {
        "name": "Cola",
        "price": 8,
        "prep_time": 2,
        "image": "cola.png"
    },
    {
        "name": "French Fries",
        "price": 10,
        "prep_time": 8,
        "image": "french_fries.png"
    },
    {
        "name": "Ice Cream",
        "price": 7,
        "prep_time": 3,
        "image": "ice_cream.png"
    },
    {
        "name": "Sandwich",
        "price": 19,
        "prep_time": 12,
        "image": "sandwich.png"
    },
    {
        "name": "Toast Sandwich",
        "price": 16,
        "prep_time": 9,
        "image": "toast_sandwich.png"
    },
    {
        "name": "Turkey Sandwich",
        "price": 21,
        "prep_time": 14,
        "image": "turkey_sandwich.png"
    },
    {
        "name": "Veggie Sandwich",
        "price": 17,
        "prep_time": 10,
        "image": "veggie_sandwich.png"
    },
    {
        "name": "Water",
        "price": 5,
        "prep_time": 1,
        "image": "water.png"
    }
]

PRODUCTS = {item["name"]: item["price"] for item in MENU_ITEMS}
PREP_TIMES = {item["name"]: item["prep_time"] for item in MENU_ITEMS}