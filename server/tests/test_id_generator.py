# tests/test_id_generator.py
import pytest
from utils.id_generator import generate_id
from ulid import ULID
import time

def test_generate_id_format():
    """Test that generated IDs have the correct format"""
    id = generate_id("evt")

    # Should have prefix_ulid format
    assert id.startswith("evt_")

    # ULID portion should be 26 characters
    ulid_part = id.split("_", 1)[1]
    assert len(ulid_part) == 26

    # Should be valid ULID
    ULID.from_str(ulid_part)  # Will raise if invalid

def test_generate_id_different_prefixes():
    """Test ID generation with different prefixes"""
    prefixes = ["evt", "li", "cat", "pm", "party", "tag", "txn", "eli", "etag"]

    for prefix in prefixes:
        id = generate_id(prefix)
        assert id.startswith(f"{prefix}_")

        # Extract and validate ULID
        ulid_part = id.split("_", 1)[1]
        assert len(ulid_part) == 26
        ULID.from_str(ulid_part)

def test_generate_id_uniqueness():
    """Test that rapidly generated IDs are unique"""
    ids = set()
    num_ids = 1000

    for _ in range(num_ids):
        id = generate_id("test")
        ids.add(id)

    # All IDs should be unique
    assert len(ids) == num_ids

def test_generate_id_sortability():
    """Test that ULIDs are lexicographically sortable by creation time"""
    id1 = generate_id("evt")
    time.sleep(0.001)  # Small delay to ensure different timestamp
    id2 = generate_id("evt")
    time.sleep(0.001)
    id3 = generate_id("evt")

    # Extract ULID portions
    ulid1 = id1.split("_", 1)[1]
    ulid2 = id2.split("_", 1)[1]
    ulid3 = id3.split("_", 1)[1]

    # Should be sortable
    assert ulid1 < ulid2 < ulid3

def test_generate_id_timestamp_extraction():
    """Test that we can extract timestamps from ULIDs"""
    before = time.time()
    id = generate_id("evt")
    after = time.time()

    # Extract ULID and get timestamp
    ulid_part = id.split("_", 1)[1]
    ulid_obj = ULID.from_str(ulid_part)
    timestamp = ulid_obj.timestamp

    # ULID timestamps have millisecond precision (48-bit timestamp)
    # So we need to check within a reasonable range
    # Timestamp should be close to the time of generation
    assert abs(timestamp - before) < 1.0  # Within 1 second

def test_generate_id_empty_prefix():
    """Test ID generation with empty prefix"""
    id = generate_id("")

    # Should start with underscore
    assert id.startswith("_")

    # ULID should still be valid
    ulid_part = id.split("_", 1)[1]
    assert len(ulid_part) == 26
    ULID.from_str(ulid_part)

def test_generate_id_special_characters_in_prefix():
    """Test ID generation with special characters in prefix"""
    # This documents current behavior - may want to add validation
    special_prefixes = ["evt-test", "evt.test", "evt/test"]

    for prefix in special_prefixes:
        id = generate_id(prefix)
        assert id.startswith(f"{prefix}_")

        # ULID should still be valid
        ulid_part = id.split("_", 1)[1]
        ULID.from_str(ulid_part)

def test_generate_id_monotonicity():
    """Test that ULIDs maintain monotonicity within the same millisecond"""
    # Generate multiple IDs rapidly (likely within same millisecond)
    ids = [generate_id("evt") for _ in range(100)]

    # Extract ULID portions
    ulids = [id.split("_", 1)[1] for id in ids]

    # Should all be unique and sortable
    assert len(set(ulids)) == len(ulids)
    assert ulids == sorted(ulids)

def test_generate_id_string_length():
    """Test total ID length for various prefixes"""
    test_cases = [
        ("evt", 3 + 1 + 26),  # prefix + underscore + ULID
        ("li", 2 + 1 + 26),
        ("cat", 3 + 1 + 26),
        ("party", 5 + 1 + 26),
    ]

    for prefix, expected_length in test_cases:
        id = generate_id(prefix)
        assert len(id) == expected_length
