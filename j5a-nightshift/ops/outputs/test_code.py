def calculate_total(items: list[dict]) -> float:
    """Calculate total from items with quantity and price."""
    total = 0.0
    for item in items:
        total += item.get('quantity', 0) * item.get('price', 0.0)
    return total
