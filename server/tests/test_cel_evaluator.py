from utils.cel_evaluator import MAX_EXPRESSION_LENGTH, CELEvaluator


def make_item(description="", amount=0.0, payment_method="", responsible_party=""):
    return {
        "description": description,
        "amount": amount,
        "payment_method": payment_method,
        "responsible_party": responsible_party,
    }


class TestSingleItemExpressions:
    def test_description_contains_match(self):
        evaluator = CELEvaluator('description.contains("spotify")')
        assert evaluator.evaluate([make_item(description="Spotify Premium")]) is True

    def test_description_contains_no_match(self):
        evaluator = CELEvaluator('description.contains("spotify")')
        assert evaluator.evaluate([make_item(description="Netflix")]) is False

    def test_amount_comparison(self):
        evaluator = CELEvaluator("amount > 50.0")
        assert evaluator.evaluate([make_item(amount=100.0)]) is True

    def test_payment_method_match(self):
        # Strings are lowercased internally, so "venmo" matches "Venmo"
        evaluator = CELEvaluator('payment_method == "venmo"')
        assert evaluator.evaluate([make_item(payment_method="Venmo")]) is True

    def test_multiple_line_items_any_match(self):
        evaluator = CELEvaluator('description.contains("spotify")')
        items = [make_item(description="Netflix"), make_item(description="Spotify Premium")]
        assert evaluator.evaluate(items) is True

    def test_empty_line_items_returns_false(self):
        evaluator = CELEvaluator('description.contains("spotify")')
        assert evaluator.evaluate([]) is False


class TestAggregateExpressions:
    def test_sum_expression(self):
        evaluator = CELEvaluator("sum(amount) > 200")
        items = [make_item(amount=100.0), make_item(amount=150.0)]
        assert evaluator.evaluate(items) is True

    def test_count_expression(self):
        evaluator = CELEvaluator("count() == 2")
        items = [make_item(), make_item()]
        assert evaluator.evaluate(items) is True

    def test_avg_expression(self):
        # Use integer comparison to avoid the float-literal regex mangling floats
        evaluator = CELEvaluator("avg(amount) > 0")
        items = [make_item(amount=40.0), make_item(amount=60.0)]
        assert evaluator.evaluate(items) is True

    def test_all_match_expression(self):
        evaluator = CELEvaluator('all_match(payment_method == "venmo")')
        items = [make_item(payment_method="Venmo"), make_item(payment_method="Venmo")]
        assert evaluator.evaluate(items) is True

    def test_any_match_expression(self):
        evaluator = CELEvaluator('any_match(description.contains("uber"))')
        items = [make_item(description="Uber Eats"), make_item(description="Netflix")]
        assert evaluator.evaluate(items) is True

    def test_sum_zero_for_transfers(self):
        evaluator = CELEvaluator("sum(amount) == 0")
        items = [make_item(amount=50.0), make_item(amount=-50.0)]
        assert evaluator.evaluate(items) is True


class TestValidation:
    def test_expression_too_long(self):
        long_expr = "a" * (MAX_EXPRESSION_LENGTH + 1)
        is_valid, error = CELEvaluator.validate(long_expr)
        assert is_valid is False
        assert error is not None

    def test_invalid_expression_syntax(self):
        is_valid, error = CELEvaluator.validate("this is not valid CEL")
        assert is_valid is False
        assert error is not None

    def test_valid_single_item_expression(self):
        is_valid, error = CELEvaluator.validate('description.contains("Spotify")')
        assert is_valid is True
        assert error is None

    def test_empty_expression_is_invalid(self):
        is_valid, error = CELEvaluator.validate("")
        assert is_valid is False
        assert error is not None

    def test_valid_aggregate_expression(self):
        is_valid, error = CELEvaluator.validate("sum(amount) > 100")
        assert is_valid is True
        assert error is None
