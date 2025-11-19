import os

from dotenv import load_dotenv

from helpers import iso_8601_to_posix

load_dotenv()

# TODO: Better abstraction and handling of dates

LIMIT = 1000
MOVING_DATE = "2022-08-03T00:00:00Z"
MOVING_DATE_POSIX = iso_8601_to_posix(MOVING_DATE)
GATED_USERS = ["neerajjsamtani@gmail.com"]
USER_FIRST_NAME = "Neeraj"
PARTIES_TO_IGNORE = ["Pink Palace Babes", "Nyusha", "John Jonah"]
STRIPE_API_KEY = os.getenv("STRIPE_LIVE_API_SECRET_KEY")
STRIPE_CUSTOMER_ID = os.getenv("STRIPE_CUSTOMER_ID")
MONGO_URI = os.getenv(
    "MONGO_URI", "mongodb://localhost:27017/test_db"
)  # Change to LIVE_MONGO_URI if you want to use the live database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://budgit_user:password@localhost:5432/budgit")
# Phase 5 migration flag: switch read operations from MongoDB to PostgreSQL
# Default: False (reads from MongoDB), Set to True to read from PostgreSQL
READ_FROM_POSTGRESQL = os.getenv("READ_FROM_POSTGRESQL", "false").lower() == "true"
VENMO_ACCESS_TOKEN = os.getenv("VENMO_ACCESS_TOKEN")
SPLITWISE_CONSUMER_KEY = os.getenv("SPLITWISE_CONSUMER_KEY")
SPLITWISE_CONSUMER_SECRET = os.getenv("SPLITWISE_CONSUMER_SECRET")
SPLITWISE_API_KEY = os.getenv("SPLITWISE_API_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY must be set in environment")
JWT_COOKIE_DOMAIN = os.getenv("JWT_COOKIE_DOMAIN")
# CORS configuration - comma-separated list of allowed origins
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://dev.localhost:5173").split(",")
SMALLEST_EPOCH_TIME = float(0)
LARGEST_EPOCH_TIME = float(9999999999)
# Keep this in sync with the categories on the frontend
CATEGORIES = [
    "All",
    "Alcohol",
    "Dining",
    "Entertainment",
    "Forma",
    "Groceries",
    "Hobbies",
    "Income",
    "Investment",
    "Medical",
    "Rent",
    "Shopping",
    "Subscription",
    "Transfer",
    "Transit",
    "Travel",
]
