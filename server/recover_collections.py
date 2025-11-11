#!/usr/bin/env python3
"""
Collection Recovery Script
==========================

This script helps recover missing collections that may have been accidentally dropped.
"""

import os

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


def check_missing_collections():
    """Check which collections are missing from the production database."""
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["flask_db"]

        # Expected collections based on dao.py
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
            "test_data",
        ]

        existing_collections = db.list_collection_names()
        missing_collections = [coll for coll in expected_collections if coll not in existing_collections]

        print("📊 Database Collection Status:")
        print("Database: flask_db")
        print(f"Existing collections: {len(existing_collections)}")
        print(f"Missing collections: {len(missing_collections)}")
        print()

        if existing_collections:
            print("✅ Existing collections:")
            for coll in sorted(existing_collections):
                count = db[coll].count_documents({})
                print(f"  - {coll} ({count} documents)")

        if missing_collections:
            print("\n❌ Missing collections:")
            for coll in sorted(missing_collections):
                print(f"  - {coll}")

        client.close()
        return missing_collections

    except ConnectionFailure:
        print("❌ Failed to connect to MongoDB")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def create_empty_collections(missing_collections):
    """Create empty collections to restore the database structure."""
    if not missing_collections:
        print("✅ No missing collections to create")
        return

    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["flask_db"]

        print(f"\n🔧 Creating {len(missing_collections)} missing collections...")

        for collection_name in missing_collections:
            # Create collection by inserting and immediately removing a document
            db[collection_name].insert_one({"temp": "initialization"})
            db[collection_name].delete_one({"temp": "initialization"})
            print(f"  ✅ Created: {collection_name}")

        print("\n✅ All missing collections have been created")
        client.close()

    except Exception as e:
        print(f"❌ Error creating collections: {e}")


def check_backup_options():
    """Check for potential backup options."""
    print("\n🔍 Checking for backup options...")

    # Check if there are any dump files
    backup_dirs = ["backups/", "dumps/", "exports/", "../backups/", "../dumps/"]

    found_backups = []
    for backup_dir in backup_dirs:
        if os.path.exists(backup_dir):
            files = [f for f in os.listdir(backup_dir) if f.endswith((".json", ".bson", ".gz", ".csv"))]
            if files:
                found_backups.append((backup_dir, files))

    if found_backups:
        print("📦 Found potential backup files:")
        for backup_dir, files in found_backups:
            print(f"  Directory: {backup_dir}")
            for file in files:
                print(f"    - {file}")
    else:
        print("❌ No backup files found in common locations")

    # Check if there are any export files in the exports directory
    if os.path.exists("exports/"):
        json_files = [f for f in os.listdir("exports/") if f.endswith(".json")]
        csv_files = [f for f in os.listdir("exports/") if f.endswith(".csv")]

        if json_files:
            print("\n📤 Found JSON export files in exports/ directory:")
            for file in json_files:
                print(f"  - {file}")

        if csv_files:
            print("\n📊 Found CSV export files in exports/ directory:")
            for file in csv_files:
                print(f"  - {file}")

            # Check for specific missing collections that have CSV backups
            missing_with_csv = []
            if "cash_raw_data.csv" in csv_files:
                missing_with_csv.append("cash_raw_data")
            if "line_items.csv" in csv_files:
                missing_with_csv.append("line_items")

            if missing_with_csv:
                print(f"\n✅ CSV backup data available for: {', '.join(missing_with_csv)}")
                print("   You can restore this data using mongoimport or a custom script.")


def main():
    print("🚨 Collection Recovery Tool")
    print("=" * 40)

    # Check what's missing
    missing_collections = check_missing_collections()

    if missing_collections:
        print(f"\n⚠️  WARNING: {len(missing_collections)} collections are missing!")
        print("This may indicate data loss. Please check the following:")
        print()
        print("1. Do you have any backup files?")
        print("2. Can you restore from a previous database dump?")
        print("3. Do you have the data in another location?")
        print()

        response = input("Do you want to create empty collections to restore the database structure? (y/N): ")
        if response.lower() == "y":
            create_empty_collections(missing_collections)
        else:
            print("Skipping collection creation")

    # Check for backup options
    check_backup_options()

    print("\n📋 Recovery Recommendations:")
    print("1. If you have MongoDB dumps, restore using: mongorestore --db flask_db dump_directory/")
    print("2. If you have JSON exports, you can import them using mongoimport")
    print(
        "3. For CSV files, use: mongoimport --db flask_db --collection collection_name \
            --type csv --file exports/filename.csv --headerline"
    )
    print("4. Check your application logs for any data export functionality")
    print("5. Consider setting up regular backups to prevent future data loss")
    print()
    print("🔧 To prevent this in the future:")
    print("- Always use separate test databases")
    print("- Set up automated backups")
    print("- Use database transactions where possible")
    print("- Test database operations in isolation")


if __name__ == "__main__":
    main()
