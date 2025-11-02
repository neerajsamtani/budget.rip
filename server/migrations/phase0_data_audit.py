#!/usr/bin/env python3
"""
Phase 0: Pre-Migration Data Audit

This script validates MongoDB data quality before migration to MySQL.
It checks for:
- Missing required fields
- Invalid data types
- Broken references (categories, payment methods, line items)
- Orphaned records
- Data consistency issues

Run from server directory:
    python migrations/phase0_data_audit.py

The audit must pass with zero errors before proceeding to Phase 1.
"""

import os
import sys
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Set

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pymongo import MongoClient

# Import constants
from constants import CATEGORIES, MONGO_URI


class DataAudit:
    """Comprehensive MongoDB data quality audit"""

    def __init__(self):
        self.client = MongoClient(MONGO_URI)

        # Extract database name from URI, with fallback to environment variable or default
        # Parse database name from URI (everything after last '/')
        db_name_from_uri = MONGO_URI.split("/")[-1] if "/" in MONGO_URI else ""

        # Use database name from URI if present, otherwise check env var, otherwise use default
        db_name = (
            db_name_from_uri
            if db_name_from_uri
            else os.getenv("MONGO_DB_NAME", "flask_db")
        )

        print(f"Database name: {db_name}")
        self.db = self.client[db_name]

        # Track validation errors
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, Any] = {}

        # Valid reference data
        self.valid_categories = set(CATEGORIES)
        self.payment_methods: Set[str] = set()
        self.line_item_ids: Set[str] = set()
        self.event_ids: Set[str] = set()

        print(f"Connected to database: {db_name}")
        print(f"MongoDB URI: {MONGO_URI}")
        print("=" * 80)

    def run_audit(self) -> bool:
        """Run all audit checks. Returns True if all checks pass."""
        print("\n🔍 Starting Phase 0: Pre-Migration Data Audit")
        print("=" * 80)

        # Step 1: Audit reference data
        print("\n📋 Step 1: Auditing Reference Data")
        print("-" * 80)
        self._audit_categories()
        self._audit_payment_methods()

        # Step 2: Audit raw transaction data
        print("\n📦 Step 2: Auditing Raw Transaction Data")
        print("-" * 80)
        self._audit_raw_transactions()

        # Step 3: Audit line items
        print("\n📝 Step 3: Auditing Line Items")
        print("-" * 80)
        self._audit_line_items()

        # Step 4: Audit events
        print("\n🎯 Step 4: Auditing Events")
        print("-" * 80)
        self._audit_events()

        # Step 5: Check for orphaned records
        print("\n🔗 Step 5: Checking for Orphaned Records")
        print("-" * 80)
        self._check_orphaned_records()

        # Step 6: Check for duplicates
        print("\n🔄 Step 6: Checking for Duplicates")
        print("-" * 80)
        self._check_duplicates()

        # Step 7: Validate data consistency
        print("\n⚖️ Step 7: Validating Data Consistency")
        print("-" * 80)
        self._validate_data_consistency()

        # Step 8: Business logic validation
        print("\n🧠 Step 8: Business Logic Validation")
        print("-" * 80)
        self._validate_business_logic()

        # Step 9: Collection structure validation
        print("\n🏗️ Step 9: Collection Structure Validation")
        print("-" * 80)
        self._validate_collection_structure()

        # Step 10: Data quality metrics
        print("\n📊 Step 10: Data Quality Metrics")
        print("-" * 80)
        self._analyze_data_quality()

        # Display summary
        self._print_summary()

        return len(self.errors) == 0

    def _audit_categories(self):
        """Validate category reference data"""
        print("\n✓ Categories (from constants.py)")
        print(f"  Valid categories: {len(self.valid_categories)}")
        for cat in sorted(self.valid_categories):
            print(f"    - {cat}")
        self.stats["categories"] = len(self.valid_categories)

    def _audit_payment_methods(self):
        """Extract and validate payment methods from line items"""
        print("\n✓ Payment Methods (extracted from line_items)")
        line_items = list(self.db.line_items.find({}, {"payment_method": 1}))

        for item in line_items:
            if "payment_method" in item and item["payment_method"]:
                self.payment_methods.add(item["payment_method"])

        print(f"  Found {len(self.payment_methods)} unique payment methods:")
        for pm in sorted(self.payment_methods):
            print(f"    - {pm}")

        if not self.payment_methods:
            self.warnings.append("No payment methods found in line_items collection")

        self.stats["payment_methods"] = len(self.payment_methods)

    def _audit_raw_transactions(self):
        """Audit raw transaction collections"""
        sources = [
            ("venmo_raw_data", "Venmo"),
            ("splitwise_raw_data", "Splitwise"),
            ("stripe_raw_transaction_data", "Stripe"),
            ("cash_raw_data", "Cash"),
        ]

        source_stats = {}

        for collection_name, source_label in sources:
            count = self.db[collection_name].count_documents({})
            source_stats[source_label] = count
            print(f"  {source_label}: {count:,} transactions")

            if count > 0:
                # Sample check - verify first document has expected structure
                sample = self.db[collection_name].find_one()
                if not sample:
                    self.warnings.append(
                        f"{source_label}: Collection reports count but no documents found"
                    )
                elif "_id" not in sample:
                    self.errors.append(
                        f"{source_label}: Sample document missing _id field"
                    )

        self.stats["raw_transactions"] = source_stats
        print(f"\n  Total raw transactions: {sum(source_stats.values()):,}")

    def _audit_line_items(self):
        """Comprehensive line item validation"""
        collection = self.db.line_items
        total_count = collection.count_documents({})
        print(f"\n  Total line items: {total_count:,}")

        if total_count == 0:
            self.warnings.append("No line items found in database")
            return

        # Track statistics
        missing_fields = defaultdict(int)
        invalid_types = defaultdict(int)
        invalid_references = defaultdict(int)
        categorized_count = 0
        uncategorized_count = 0

        # Validate each line item
        for item in collection.find({}):
            item_id = item.get("_id", "UNKNOWN")

            # Store valid line item IDs for reference checking
            if "id" in item:
                self.line_item_ids.add(item["id"])
            elif "_id" in item:
                self.line_item_ids.add(str(item["_id"]))

            # Required fields validation
            required_fields = {
                "id": str,
                "date": (int, float),
                "amount": (int, float, Decimal),
                "description": str,
                "payment_method": str,
                "responsible_party": str,
            }

            for field, expected_type in required_fields.items():
                if field not in item or item[field] is None or item[field] == "":
                    missing_fields[field] += 1
                    self.errors.append(
                        f"Line item {item_id}: Missing or empty required field '{field}'"
                    )
                elif not isinstance(item[field], expected_type):
                    invalid_types[field] += 1
                    self.errors.append(
                        f"Line item {item_id}: Field '{field}' has invalid type. "
                        f"Expected {expected_type}, got {type(item[field])}"
                    )

            # Validate date is reasonable (after year 2000, before year 2100)
            if "date" in item and isinstance(item["date"], (int, float)):
                date_val = float(item["date"])
                if date_val < 946684800:  # Jan 1, 2000
                    self.warnings.append(
                        f"Line item {item_id}: Date {date_val} is before year 2000"
                    )
                elif date_val > 4102444800:  # Jan 1, 2100
                    self.warnings.append(
                        f"Line item {item_id}: Date {date_val} is after year 2100"
                    )

            # Validate amount is numeric and not zero
            if "amount" in item:
                try:
                    amount = float(item["amount"])
                    if amount == 0:
                        self.warnings.append(f"Line item {item_id}: Amount is zero")
                except (ValueError, TypeError):
                    self.errors.append(
                        f"Line item {item_id}: Amount '{item['amount']}' cannot be converted to float"
                    )

            # Validate payment method reference
            if "payment_method" in item and item["payment_method"]:
                if item["payment_method"] not in self.payment_methods:
                    # This shouldn't happen since we extracted from line_items
                    # But check anyway for consistency
                    invalid_references["payment_method"] += 1

            # Track categorization status
            if "event_id" in item and item["event_id"]:
                categorized_count += 1
            else:
                uncategorized_count += 1

        # Print statistics
        print(f"  Categorized: {categorized_count:,}")
        print(f"  Uncategorized: {uncategorized_count:,}")

        if missing_fields:
            print("\n  ⚠️  Missing Fields Summary:")
            for field, count in missing_fields.items():
                print(f"    - {field}: {count} line items")

        if invalid_types:
            print("\n  ⚠️  Invalid Type Summary:")
            for field, count in invalid_types.items():
                print(f"    - {field}: {count} line items")

        self.stats["line_items"] = {
            "total": total_count,
            "categorized": categorized_count,
            "uncategorized": uncategorized_count,
            "errors": len(self.errors),
        }

    def _audit_events(self):
        """Comprehensive event validation"""
        collection = self.db.events
        total_count = collection.count_documents({})
        print(f"\n  Total events: {total_count:,}")

        if total_count == 0:
            self.warnings.append("No events found in database")
            self.stats["events"] = {"total": 0}
            return

        # Track statistics
        missing_fields = defaultdict(int)
        invalid_types = defaultdict(int)
        invalid_references = defaultdict(int)
        broken_line_item_refs = 0
        total_line_item_refs = 0

        # Validate each event
        for event in collection.find({}):
            event_id = event.get("_id", "UNKNOWN")

            # Store valid event IDs for reference checking
            if "id" in event:
                self.event_ids.add(event["id"])
            elif "_id" in event:
                self.event_ids.add(str(event["_id"]))

            # Required fields validation
            required_fields = {
                "id": str,
                "date": (int, float),
                "name": str,
                "category": str,
                "amount": (int, float, Decimal),
                "line_items": list,
                "is_duplicate_transaction": bool,
            }

            for field, expected_type in required_fields.items():
                if field not in event:
                    missing_fields[field] += 1
                    self.errors.append(
                        f"Event {event_id}: Missing required field '{field}'"
                    )
                elif field == "line_items":
                    # Special handling for line_items (required list, can be empty but must exist)
                    if not isinstance(event[field], list):
                        invalid_types[field] += 1
                        self.errors.append(
                            f"Event {event_id}: Field 'line_items' must be a list, got {type(event[field])}"
                        )
                elif not isinstance(event[field], expected_type):
                    invalid_types[field] += 1
                    self.errors.append(
                        f"Event {event_id}: Field '{field}' has invalid type. "
                        f"Expected {expected_type}, got {type(event[field])}"
                    )

            # Validate category reference
            if "category" in event:
                if event["category"] not in self.valid_categories:
                    invalid_references["category"] += 1
                    self.errors.append(
                        f"Event {event_id}: Invalid category '{event['category']}'. "
                        f"Must be one of: {', '.join(sorted(self.valid_categories))}"
                    )

            # Validate line_items references
            if "line_items" in event and isinstance(event["line_items"], list):
                if len(event["line_items"]) == 0:
                    self.errors.append(
                        f"Event {event_id}: Empty line_items array (events must have at least one line item)"
                    )

                for line_item_id in event["line_items"]:
                    total_line_item_refs += 1
                    # Line items may use string IDs or ObjectId format
                    if (
                        line_item_id not in self.line_item_ids
                        and str(line_item_id) not in self.line_item_ids
                    ):
                        broken_line_item_refs += 1
                        self.errors.append(
                            f"Event {event_id}: References non-existent line item '{line_item_id}'"
                        )

            # Validate tags (optional field)
            if "tags" in event:
                if not isinstance(event["tags"], list):
                    invalid_types["tags"] += 1
                    self.warnings.append(
                        f"Event {event_id}: Field 'tags' should be a list, got {type(event['tags'])}"
                    )

        # Print statistics
        if missing_fields:
            print("\n  ⚠️  Missing Fields Summary:")
            for field, count in missing_fields.items():
                print(f"    - {field}: {count} events")

        if invalid_types:
            print("\n  ⚠️  Invalid Type Summary:")
            for field, count in invalid_types.items():
                print(f"    - {field}: {count} events")

        if invalid_references:
            print("\n  ⚠️  Invalid References Summary:")
            for field, count in invalid_references.items():
                print(f"    - {field}: {count} events")

        if broken_line_item_refs > 0:
            print(
                f"\n  ⚠️  Broken Line Item References: {broken_line_item_refs}/{total_line_item_refs}"
            )

        self.stats["events"] = {
            "total": total_count,
            "broken_line_item_refs": broken_line_item_refs,
            "total_line_item_refs": total_line_item_refs,
        }

    def _check_orphaned_records(self):
        """Check for orphaned line items and other inconsistencies"""
        print("\n  Checking for data inconsistencies...")

        # Check for line items with event_id that don't exist
        orphaned_line_items = 0
        for item in self.db.line_items.find({"event_id": {"$exists": True}}):
            event_id = item.get("event_id")
            if (
                event_id
                and event_id not in self.event_ids
                and str(event_id) not in self.event_ids
            ):
                orphaned_line_items += 1
                self.errors.append(
                    f"Line item {item.get('_id')}: References non-existent event '{event_id}'"
                )

        if orphaned_line_items > 0:
            print(f"  ⚠️  Orphaned line items: {orphaned_line_items}")
        else:
            print("  ✓ No orphaned line items found")

        self.stats["orphaned_line_items"] = orphaned_line_items

    def _check_duplicates(self):
        """Check for duplicate line items and events"""
        print("\n  Checking for duplicate records...")

        # Check for duplicate line item IDs
        line_item_ids = []
        duplicate_line_item_ids = set()

        for item in self.db.line_items.find({}, {"id": 1, "_id": 1}):
            item_id = item.get("id") or str(item.get("_id"))
            if item_id in line_item_ids:
                duplicate_line_item_ids.add(item_id)
            else:
                line_item_ids.append(item_id)

        if duplicate_line_item_ids:
            self.errors.append(
                f"Duplicate line item IDs found: {len(duplicate_line_item_ids)}"
            )
            for dup_id in list(duplicate_line_item_ids)[:100]:  # Show first 100
                self.errors.append(f"  - Duplicate line item ID: {dup_id}")
            if len(duplicate_line_item_ids) > 100:
                self.errors.append(
                    f"  ... and {len(duplicate_line_item_ids) - 100} more"
                )
        else:
            print("  ✓ No duplicate line item IDs found")

        # Check for duplicate event IDs
        event_ids = []
        duplicate_event_ids = set()

        for event in self.db.events.find({}, {"id": 1, "_id": 1}):
            event_id = event.get("id") or str(event.get("_id"))
            if event_id in event_ids:
                duplicate_event_ids.add(event_id)
            else:
                event_ids.append(event_id)

        if duplicate_event_ids:
            self.errors.append(f"Duplicate event IDs found: {len(duplicate_event_ids)}")
            for dup_id in list(duplicate_event_ids)[:100]:  # Show first 100
                self.errors.append(f"  - Duplicate event ID: {dup_id}")
            if len(duplicate_event_ids) > 100:
                self.errors.append(f"  ... and {len(duplicate_event_ids) - 100} more")
        else:
            print("  ✓ No duplicate event IDs found")

        # Check for potential duplicate line items (same date, amount, description)
        potential_duplicates = 0
        line_item_signatures = {}

        for item in self.db.line_items.find({}):
            signature = (
                item.get("date"),
                item.get("amount"),
                item.get("description", "").strip().lower(),
            )
            if signature in line_item_signatures and item.get("description") not in (
                "MTA*NYCT PAYGO           NEW YORK     NY",
                "MTA*NYCT PAYGO",
            ):
                potential_duplicates += 1
                self.warnings.append(
                    f"Potential duplicate line items: {item.get('_id')} and {line_item_signatures[signature]}. {item.get('description')} {item.get('payment_method')}"
                )
            else:
                line_item_signatures[signature] = item.get("_id")

        if potential_duplicates > 0:
            print(f"  ⚠️  Potential duplicate line items: {potential_duplicates}")
        else:
            print("  ✓ No potential duplicate line items found")

        self.stats["duplicate_line_item_ids"] = len(duplicate_line_item_ids)
        self.stats["duplicate_event_ids"] = len(duplicate_event_ids)
        self.stats["potential_duplicate_line_items"] = potential_duplicates

    def _validate_data_consistency(self):
        """Validate data consistency between events and line items"""
        print("\n  Validating event-line item consistency...")

        inconsistent_events = 0
        total_events_checked = 0

        for event in self.db.events.find({}):
            total_events_checked += 1
            event_id = event.get("_id")
            event_amount = event.get("amount", 0)
            line_item_ids = event.get("line_items", [])

            if not line_item_ids:
                self.errors.append(f"Event {event_id}: No line items associated")
                inconsistent_events += 1
                continue

            # Calculate total from line items
            line_item_total = 0
            for line_item_id in line_item_ids:
                line_item = self.db.line_items.find_one(
                    {"$or": [{"id": line_item_id}, {"_id": line_item_id}]}
                )
                if line_item:
                    line_item_total += float(line_item.get("amount", 0))
                else:
                    self.errors.append(
                        f"Event {event_id}: Line item {line_item_id} not found"
                    )

            # Check if event amount matches line item total
            event_amount_to_check = event_amount
            if event.get("is_duplicate_transaction", True):
                event_amount_to_check = event_amount * 2

            if (
                abs(event_amount_to_check - line_item_total) > 0.01
            ):  # Allow for small floating point differences
                self.warnings.append(
                    f"Event {event_id}: Amount mismatch - Event: {event_amount}, Line items total: {line_item_total}. Event: {event.get('description')} {event.get('payment_method')}"
                )
                inconsistent_events += 1

        if inconsistent_events == 0:
            print("  ✓ All events have consistent amounts with their line items")
        else:
            print(
                f"  ⚠️  {inconsistent_events}/{total_events_checked} events have inconsistencies"
            )

        self.stats["inconsistent_events"] = inconsistent_events
        self.stats["total_events_checked"] = total_events_checked

    def _validate_business_logic(self):
        """Validate business logic rules"""
        print("\n  Validating business logic...")

        future_dates = 0
        zero_amounts = 0
        invalid_duplicate_flags = 0
        current_time = datetime.now().timestamp()

        # Check for future dates in line items
        for item in self.db.line_items.find({}):
            if "date" in item and isinstance(item["date"], (int, float)):
                if item["date"] > current_time:
                    future_dates += 1
                    self.warnings.append(
                        f"Line item {item.get('_id')}: Future date {item['date']}"
                    )

            # Check for zero amounts
            if "amount" in item:
                try:
                    amount = float(item["amount"])
                    if amount == 0:
                        zero_amounts += 1
                        self.warnings.append(
                            f"Line item {item.get('_id')}: Zero amount transaction"
                        )
                except (ValueError, TypeError):
                    pass  # Already handled in _audit_line_items

        # Check for future dates in events
        for event in self.db.events.find({}):
            if "date" in event and isinstance(event["date"], (int, float)):
                if event["date"] > current_time:
                    future_dates += 1
                    self.warnings.append(
                        f"Event {event.get('_id')}: Future date {event['date']}"
                    )

            # Validate duplicate transaction flag
            if "is_duplicate_transaction" in event:
                if not isinstance(event["is_duplicate_transaction"], bool):
                    invalid_duplicate_flags += 1
                    self.errors.append(
                        f"Event {event.get('_id')}: is_duplicate_transaction must be boolean, got {type(event['is_duplicate_transaction'])}"
                    )

        print(f"  Future dates: {future_dates}")
        print(f"  Zero amounts: {zero_amounts}")
        print(f"  Invalid duplicate flags: {invalid_duplicate_flags}")

        self.stats["future_dates"] = future_dates
        self.stats["zero_amounts"] = zero_amounts
        self.stats["invalid_duplicate_flags"] = invalid_duplicate_flags

    def _validate_collection_structure(self):
        """Validate collection existence and structure"""
        print("\n  Validating collection structure...")

        expected_collections = [
            "venmo_raw_data",
            "splitwise_raw_data",
            "cash_raw_data",
            "stripe_raw_transaction_data",
            "stripe_raw_account_data",
            "line_items",
            "events",
            "accounts",
            "users",
        ]

        existing_collections = self.db.list_collection_names()
        missing_collections = []

        for collection in expected_collections:
            if collection not in existing_collections:
                missing_collections.append(collection)
                self.warnings.append(f"Missing collection: {collection}")

        if not missing_collections:
            print("  ✓ All expected collections exist")
        else:
            print(f"  ⚠️  Missing collections: {len(missing_collections)}")
            for coll in missing_collections:
                print(f"    - {coll}")

        # Check for unexpected collections
        unexpected_collections = [
            coll for coll in existing_collections if coll not in expected_collections
        ]
        if unexpected_collections:
            print(f"  ℹ️  Unexpected collections found: {len(unexpected_collections)}")
            for coll in unexpected_collections:
                print(f"    - {coll}")

        self.stats["missing_collections"] = len(missing_collections)
        self.stats["unexpected_collections"] = len(unexpected_collections)

    def _analyze_data_quality(self):
        """Analyze data quality metrics and distributions"""
        print("\n  Analyzing data quality metrics...")

        # Analyze amount distribution
        amounts = []
        for item in self.db.line_items.find({}, {"amount": 1}):
            if "amount" in item:
                try:
                    amounts.append(float(item["amount"]))
                except (ValueError, TypeError):
                    pass

        if amounts:
            amounts.sort()
            total_amount = sum(amounts)
            avg_amount = total_amount / len(amounts)
            median_amount = amounts[len(amounts) // 2]
            min_amount = amounts[0]
            max_amount = amounts[-1]

            print("  Amount Statistics:")
            print(f"    Total: ${total_amount:,.2f}")
            print(f"    Average: ${avg_amount:.2f}")
            print(f"    Median: ${median_amount:.2f}")
            print(f"    Range: ${min_amount:.2f} - ${max_amount:.2f}")

            # Check for unusual patterns
            if max_amount > avg_amount * 10:
                self.warnings.append(f"Large transaction detected: ${max_amount:.2f}")

            if min_amount < -1000:  # Large negative amounts
                self.warnings.append(f"Large negative transaction: ${min_amount:.2f}")

            self.stats["amount_stats"] = {
                "total": total_amount,
                "average": avg_amount,
                "median": median_amount,
                "min": min_amount,
                "max": max_amount,
                "count": len(amounts),
            }

        # Analyze category distribution
        category_counts = defaultdict(int)
        for event in self.db.events.find({}, {"category": 1}):
            if "category" in event:
                category_counts[event["category"]] += 1

        if category_counts:
            print("  Category Distribution:")
            for category, count in sorted(
                category_counts.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"    {category}: {count}")

            # Check for categories with very few events
            total_events = sum(category_counts.values())
            for category, count in category_counts.items():
                if (
                    count < 3 and total_events > 50
                ):  # Less than 3 events in a large dataset
                    self.warnings.append(
                        f"Category '{category}' has only {count} events"
                    )

            self.stats["category_distribution"] = dict(category_counts)

        # Analyze date distribution
        dates = []
        for item in self.db.line_items.find({}, {"date": 1}):
            if "date" in item and isinstance(item["date"], (int, float)):
                dates.append(item["date"])

        if dates:
            dates.sort()
            oldest_date = datetime.fromtimestamp(dates[0])
            newest_date = datetime.fromtimestamp(dates[-1])
            date_span = (dates[-1] - dates[0]) / (365.25 * 24 * 3600)  # Years

            print("  Date Range:")
            print(f"    Oldest: {oldest_date.strftime('%Y-%m-%d')}")
            print(f"    Newest: {newest_date.strftime('%Y-%m-%d')}")
            print(f"    Span: {date_span:.1f} years")

            self.stats["date_range"] = {
                "oldest": dates[0],
                "newest": dates[-1],
                "span_years": date_span,
            }

    def _print_summary(self):
        """Print audit summary and results"""
        print("\n" + "=" * 80)
        print("📊 AUDIT SUMMARY")
        print("=" * 80)

        # Print statistics
        print("\n📈 Database Statistics:")
        print(f"  Categories: {self.stats.get('categories', 0)}")
        print(f"  Payment Methods: {self.stats.get('payment_methods', 0)}")

        raw_txn = self.stats.get("raw_transactions", {})
        if raw_txn:
            print("  Raw Transactions:")
            for source, count in raw_txn.items():
                print(f"    - {source}: {count:,}")

        line_items = self.stats.get("line_items", {})
        if line_items:
            print(f"  Line Items: {line_items.get('total', 0):,}")
            print(f"    - Categorized: {line_items.get('categorized', 0):,}")
            print(f"    - Uncategorized: {line_items.get('uncategorized', 0):,}")

        events = self.stats.get("events", {})
        if events:
            print(f"  Events: {events.get('total', 0):,}")

        orphaned = self.stats.get("orphaned_line_items", 0)
        if orphaned:
            print(f"  Orphaned Line Items: {orphaned}")

        # Print new validation results
        duplicates = self.stats.get("duplicate_line_item_ids", 0) + self.stats.get(
            "duplicate_event_ids", 0
        )
        if duplicates:
            print(f"  Duplicate IDs: {duplicates}")

        inconsistent = self.stats.get("inconsistent_events", 0)
        if inconsistent:
            print(f"  Inconsistent Events: {inconsistent}")

        future_dates = self.stats.get("future_dates", 0)
        if future_dates:
            print(f"  Future Dates: {future_dates}")

        zero_amounts = self.stats.get("zero_amounts", 0)
        if zero_amounts:
            print(f"  Zero Amounts: {zero_amounts}")

        missing_collections = self.stats.get("missing_collections", 0)
        if missing_collections:
            print(f"  Missing Collections: {missing_collections}")

        # Print errors and warnings
        print("\n🚨 Validation Results:")
        print(f"  Errors: {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings[:100], 1):
                print(f"  {i}. {warning}")
            if len(self.warnings) > 100:
                print(f"  ... and {len(self.warnings) - 100} more warnings")

        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for i, error in enumerate(self.errors[:100], 1):
                print(f"  {i}. {error}")
            if len(self.errors) > 100:
                print(f"  ... and {len(self.errors) - 100} more errors")

        # Final verdict
        print("\n" + "=" * 80)
        if len(self.errors) == 0:
            print("✅ AUDIT PASSED - Data is ready for migration!")
            print("=" * 80)
            print("\nNext steps:")
            print(
                "1. Create MongoDB backup: mongodump --db flask_db --out /backup/pre_migration_$(date +%Y%m%d_%H%M%S)"
            )
            print("2. Proceed to Phase 1: Setup MySQL")
        else:
            print("❌ AUDIT FAILED - Please fix errors before proceeding")
            print("=" * 80)
            print("\nNext steps:")
            print("1. Review errors above")
            print("2. Create and run migrations/phase0_data_cleanup.py to fix issues")
            print("3. Re-run this audit script to verify fixes")
            print("4. Repeat until audit passes with zero errors")
        print()


def main():
    """Main entry point"""
    try:
        audit = DataAudit()
        success = audit.run_audit()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error during audit: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
