# server/utils/id_generator.py
from ulid import ULID

def generate_id(prefix: str) -> str:
    """
    Generate Stripe-style ID using ULID for sortability.

    Example: evt_01ARZ3NDEKTSV4RRFFQ69G5FAV

    ULID = 48-bit timestamp + 80-bit randomness
    - Lexicographically sortable by creation time
    - Monotonic: IDs generated in same millisecond increment by 1
    - 26 characters (base32 encoded)
    - Better PostgreSQL performance (sequential inserts)
    - Can extract timestamp if needed

    Note: python-ulid 3.1.0 has built-in monotonic support. When multiple
    ULIDs are generated within the same millisecond, the randomness portion
    is automatically incremented to maintain sort order.

    Args:
        prefix: Stripe-style prefix (evt, li, cat, pm, party, tag, txn, eli, etag)

    Returns:
        String ID in format: {prefix}_{ulid}

    Usage:
        event_id = generate_id("evt")   # evt_01JA8QM9TNWQ3BK42G5YZH3K0P
        line_item_id = generate_id("li") # li_01JA8QMA1XPRT2DS93F7VN6K1Q
        category_id = generate_id("cat") # cat_01JA8QMA1XPRT2DS93F7VN6K1Q
    """
    return f"{prefix}_{ULID()}"
