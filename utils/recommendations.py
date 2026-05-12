from collections import Counter


def get_recommendations(orders: dict, card_uid: str, top_n: int = 3) -> list:
    """
    Scans all orders for this card_uid, counts product frequency,
    returns top_n product names sorted by how often they were ordered.
    """
    counter = Counter()

    for order in orders.values():
        if not isinstance(order, dict):
            continue
        if str(order.get("card_uid", "")) != str(card_uid):
            continue
        products = order.get("products", {})
        for product, qty in products.items():
            counter[product] += qty  # weight by quantity too

    # Return top N as list of {"name": ..., "times": ...}
    return [
        {"name": name, "times": count}
        for name, count in counter.most_common(top_n)
    ]
