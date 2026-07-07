from script import calculate_dynamic_loyalty_matrix_rewards


def test_gold_customer_gets_correct_lifetime_value():
    customers = [{"tier": "Gold", "region": "North", "lifetime_value": 0}]
    calculate_dynamic_loyalty_matrix_rewards(customers)
    # Gold = 550.75, North multiplier = 1.15
    assert customers[0]["lifetime_value"] == round(550.75 * 1.15, 2)
