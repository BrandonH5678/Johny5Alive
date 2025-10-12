from test_code import calculate_total

def test_calculate_total():
    items = [
        {'quantity': 2, 'price': 10.0},
        {'quantity': 3, 'price': 5.0}
    ]
    assert calculate_total(items) == 35.0

def test_calculate_total_empty():
    assert calculate_total([]) == 0.0
