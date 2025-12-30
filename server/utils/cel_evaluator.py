"""
CEL (Common Expression Language) evaluator for event hints.

Uses the cel-python library for expression evaluation.

Supports two modes:
1. Single-item expressions: Evaluated against each line item (any match = success)
2. Aggregate expressions: Evaluated against the entire collection of line items

Single-item syntax (standard CEL):
    description.contains("Spotify")
    amount > 100 && payment_method == "Chase"

Aggregate syntax (detected by function names):
    sum(amount) == 0
    count() > 2
    all_match(description.contains("Uber"))
    any_match(payment_method == "Venmo")
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import Any

import celpy
from celpy import celtypes

logger = logging.getLogger(__name__)

# Security limits
MAX_EXPRESSION_LENGTH = 500
MAX_NESTING_DEPTH = 10
EVALUATION_TIMEOUT_SECONDS = 2.0


class CELValidationError(Exception):
    """Raised when a CEL expression is invalid."""

    pass


# Pattern to detect aggregate expressions
AGGREGATE_PATTERN = re.compile(r"\b(sum|count|avg|min_val|max_val|all_match|any_match)\s*\(")

# Declarations for line item fields
LINE_ITEM_DECLS = {
    "description": celtypes.StringType,
    "amount": celtypes.DoubleType,
    "payment_method": celtypes.StringType,
    "responsible_party": celtypes.StringType,
}


def _to_cel_value(value: Any, lowercase_strings: bool = False) -> Any:
    """Convert a Python value to a CEL-compatible value."""
    if value is None:
        return celtypes.StringType("")
    if isinstance(value, bool):
        return celtypes.BoolType(value)
    if isinstance(value, (int, float)):
        return celtypes.DoubleType(float(value))
    if isinstance(value, str):
        if lowercase_strings:
            return celtypes.StringType(value.lower())
        return celtypes.StringType(value)
    return celtypes.StringType(str(value))


def _build_line_item_context(item: dict) -> dict:
    """Build a CEL evaluation context from a line item dict.

    String values are lowercased for case-insensitive matching.
    """
    return {
        "description": _to_cel_value(item.get("description", ""), lowercase_strings=True),
        "amount": _to_cel_value(item.get("amount", 0)),
        "payment_method": _to_cel_value(item.get("payment_method", ""), lowercase_strings=True),
        "responsible_party": _to_cel_value(item.get("responsible_party", ""), lowercase_strings=True),
    }


def _lowercase_string_literals(expression: str) -> str:
    """Lowercase all string literals in a CEL expression for case-insensitive matching."""

    # Match double-quoted strings and lowercase their contents
    def lowercase_match(match: re.Match) -> str:
        return '"' + match.group(1).lower() + '"'

    return re.sub(r'"([^"]*)"', lowercase_match, expression)


def _evaluate_single_expression(expression: str, line_items: list[dict]) -> bool:
    """
    Evaluate a single-item expression against line items.
    Returns True if ANY line item matches the expression.
    """
    try:
        # Lowercase string literals for case-insensitive matching
        expression = _lowercase_string_literals(expression)
        env = celpy.Environment(annotations=LINE_ITEM_DECLS)
        ast = env.compile(expression)
        prgm = env.program(ast)

        for item in line_items:
            context = _build_line_item_context(item)
            try:
                result = prgm.evaluate(context)
                if result:
                    return True
            except Exception as e:
                logger.warning(
                    f"CEL evaluation failed for line item: {e}",
                    extra={"expression": expression, "item_description": item.get("description", "")[:50]},
                )
                continue

        return False
    except Exception as e:
        raise CELValidationError(f"Failed to evaluate expression: {e}") from e


def _evaluate_single_item(expression: str, item: dict) -> bool:
    """Evaluate an expression against a single line item."""
    try:
        # Lowercase string literals for case-insensitive matching
        expression = _lowercase_string_literals(expression)
        env = celpy.Environment(annotations=LINE_ITEM_DECLS)
        ast = env.compile(expression)
        prgm = env.program(ast)
        context = _build_line_item_context(item)
        result = prgm.evaluate(context)
        return bool(result)
    except Exception as e:
        logger.warning(
            f"CEL single item evaluation failed: {e}",
            extra={"expression": expression, "item_description": item.get("description", "")[:50]},
        )
        return False


def _evaluate_aggregate_expression(expression: str, line_items: list[dict]) -> bool:
    """
    Evaluate an aggregate expression against the collection of line items.

    Supports:
    - sum(amount) == 0
    - count() > 2
    - all_match(description.contains("Uber"))
    - any_match(payment_method == "Venmo")
    """
    # Pre-compute aggregate values
    amounts = [float(item.get("amount", 0)) for item in line_items]
    total_sum = sum(amounts)
    item_count = len(line_items)
    avg_amount = total_sum / item_count if item_count > 0 else 0
    min_amount = min(amounts) if amounts else 0
    max_amount = max(amounts) if amounts else 0

    # Handle all_match() and any_match() specially
    all_match = re.match(r"all_match\s*\(\s*(.+)\s*\)$", expression.strip())
    if all_match:
        inner_expr = all_match.group(1)
        return all(_evaluate_single_item(inner_expr, item) for item in line_items)

    any_match = re.match(r"any_match\s*\(\s*(.+)\s*\)$", expression.strip())
    if any_match:
        inner_expr = any_match.group(1)
        return any(_evaluate_single_item(inner_expr, item) for item in line_items)

    # Build context with aggregate values as CEL types
    # All values are DoubleType for consistent type comparison
    context = {
        "sum_amount": celtypes.DoubleType(total_sum),
        "count_items": celtypes.DoubleType(float(item_count)),
        "avg_amount": celtypes.DoubleType(avg_amount),
        "min_amount": celtypes.DoubleType(min_amount),
        "max_amount": celtypes.DoubleType(max_amount),
    }

    # Replace aggregate function calls with variable references
    processed = expression
    processed = re.sub(r"\bsum\s*\(\s*amount\s*\)", "sum_amount", processed)
    processed = re.sub(r"\bcount\s*\(\s*\)", "count_items", processed)
    processed = re.sub(r"\bavg\s*\(\s*amount\s*\)", "avg_amount", processed)
    processed = re.sub(r"\bmin_val\s*\(\s*amount\s*\)", "min_amount", processed)
    processed = re.sub(r"\bmax_val\s*\(\s*amount\s*\)", "max_amount", processed)

    # Also convert integer literals to floats for type consistency
    # Match integer literals that are not part of a float (not followed by .)
    processed = re.sub(r"\b(\d+)(?!\.\d)", r"\1.0", processed)

    # Evaluate the processed expression
    try:
        decls = {
            "sum_amount": celtypes.DoubleType,
            "count_items": celtypes.DoubleType,
            "avg_amount": celtypes.DoubleType,
            "min_amount": celtypes.DoubleType,
            "max_amount": celtypes.DoubleType,
        }
        env = celpy.Environment(annotations=decls)
        ast = env.compile(processed)
        prgm = env.program(ast)
        result = prgm.evaluate(context)
        return bool(result)
    except Exception as e:
        raise CELValidationError(f"Failed to evaluate aggregate expression: {e}") from e


class CELEvaluator:
    """Evaluates CEL expressions against line item data."""

    def __init__(self, expression: str):
        self.expression = expression.strip()
        self.is_aggregate = bool(AGGREGATE_PATTERN.search(self.expression))

    def evaluate(self, line_items: list[dict]) -> bool:
        """
        Evaluate expression against line items.

        For single-item expressions: returns True if ANY line item matches.
        For aggregate expressions: evaluates against the entire collection.

        Uses a timeout to prevent long-running evaluations.
        """
        if not line_items:
            return False

        def _do_evaluate() -> bool:
            if self.is_aggregate:
                return _evaluate_aggregate_expression(self.expression, line_items)
            else:
                return _evaluate_single_expression(self.expression, line_items)

        # Run evaluation with timeout to prevent DoS from complex expressions
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_do_evaluate)
                return future.result(timeout=EVALUATION_TIMEOUT_SECONDS)
        except FuturesTimeoutError:
            logger.warning(
                f"CEL evaluation timed out after {EVALUATION_TIMEOUT_SECONDS}s",
                extra={"expression": self.expression[:100]},
            )
            raise CELValidationError(f"Expression evaluation timed out (max {EVALUATION_TIMEOUT_SECONDS}s)")

    @classmethod
    def validate(cls, expression: str) -> tuple[bool, str | None]:
        """
        Validate a CEL expression syntax.

        Returns (is_valid, error_message).
        """
        if not expression or not expression.strip():
            return False, "Expression cannot be empty"

        expression = expression.strip()

        # Security: Check expression length
        if len(expression) > MAX_EXPRESSION_LENGTH:
            return False, f"Expression too long (max {MAX_EXPRESSION_LENGTH} characters)"

        # Security: Check nesting depth (count parentheses)
        max_depth = 0
        current_depth = 0
        for char in expression:
            if char == "(":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ")":
                current_depth -= 1
        if max_depth > MAX_NESTING_DEPTH:
            return False, f"Expression too deeply nested (max {MAX_NESTING_DEPTH} levels)"

        # Check for aggregate expressions with inner conditions
        all_match = re.match(r"all_match\s*\(\s*(.+)\s*\)$", expression)
        if all_match:
            inner = all_match.group(1)
            return cls._validate_single_expression(inner)

        any_match = re.match(r"any_match\s*\(\s*(.+)\s*\)$", expression)
        if any_match:
            inner = any_match.group(1)
            return cls._validate_single_expression(inner)

        # Check for numeric aggregate expressions
        if AGGREGATE_PATTERN.search(expression):
            return cls._validate_aggregate_expression(expression)

        # Single-item expression
        return cls._validate_single_expression(expression)

    @classmethod
    def _validate_single_expression(cls, expression: str) -> tuple[bool, str | None]:
        """Validate a single-item expression by trying to compile it."""
        try:
            env = celpy.Environment(annotations=LINE_ITEM_DECLS)
            env.compile(expression)
            return True, None
        except Exception as e:
            return False, str(e)

    @classmethod
    def _validate_aggregate_expression(cls, expression: str) -> tuple[bool, str | None]:
        """Validate an aggregate expression."""
        # Replace aggregate functions with variable references
        processed = expression
        processed = re.sub(r"\bsum\s*\(\s*amount\s*\)", "sum_amount", processed)
        processed = re.sub(r"\bcount\s*\(\s*\)", "count_items", processed)
        processed = re.sub(r"\bavg\s*\(\s*amount\s*\)", "avg_amount", processed)
        processed = re.sub(r"\bmin_val\s*\(\s*amount\s*\)", "min_amount", processed)
        processed = re.sub(r"\bmax_val\s*\(\s*amount\s*\)", "max_amount", processed)

        # Convert integer literals to floats for type consistency
        processed = re.sub(r"\b(\d+)(?!\.\d)", r"\1.0", processed)

        try:
            decls = {
                "sum_amount": celtypes.DoubleType,
                "count_items": celtypes.DoubleType,
                "avg_amount": celtypes.DoubleType,
                "min_amount": celtypes.DoubleType,
                "max_amount": celtypes.DoubleType,
            }
            env = celpy.Environment(annotations=decls)
            env.compile(processed)
            return True, None
        except Exception as e:
            return False, str(e)


def evaluate_hints(hints: list[dict], line_items: list[dict]) -> dict | None:
    """
    Evaluate a list of hints against line items.

    Returns the first matching hint's prefill data, or None if no match.

    Args:
        hints: List of hint dicts with 'cel_expression', 'prefill_name', 'prefill_category', etc.
        line_items: List of line item dicts with 'description', 'amount', 'payment_method', etc.

    Returns:
        Dict with 'name', 'category', 'matched_hint_id', 'matched_hint_name' or None.
    """
    for hint in hints:
        if not hint.get("is_active", True):
            continue

        try:
            evaluator = CELEvaluator(hint["cel_expression"])
            if evaluator.evaluate(line_items):
                return {
                    "name": hint["prefill_name"],
                    "category": hint.get("prefill_category"),
                    "matched_hint_id": hint.get("id"),
                    "matched_hint_name": hint.get("name"),
                }
        except Exception as e:
            logger.warning(
                f"Hint evaluation failed for hint '{hint.get('name', 'unknown')}': {e}",
                extra={"hint_id": hint.get("id"), "expression": hint.get("cel_expression", "")[:100]},
            )
            continue

    return None
