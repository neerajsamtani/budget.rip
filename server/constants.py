import os

from dotenv import load_dotenv

from helpers import iso_8601_to_posix

load_dotenv()

# Test mode flag - set by conftest.py before any imports
TESTING = os.getenv("TESTING", "false").lower() == "true"

LIMIT = 1000
BATCH_SIZE = 1000

# Stripe customer configuration - used when creating new customers
STRIPE_CUSTOMER_EMAIL = os.getenv("STRIPE_CUSTOMER_EMAIL", "")
STRIPE_CUSTOMER_NAME = os.getenv("STRIPE_CUSTOMER_NAME", "")
MOVING_DATE = "2022-08-03T00:00:00Z"
MOVING_DATE_POSIX = iso_8601_to_posix(MOVING_DATE)
GATED_USERS = ["neerajjsamtani@gmail.com"]
USER_FIRST_NAME = "Neeraj"
PARTIES_TO_IGNORE = ["Pink Palace Babes", "Nyusha", "John Jonah"]
STRIPE_API_KEY = os.getenv("STRIPE_LIVE_API_SECRET_KEY")
STRIPE_CUSTOMER_ID = os.getenv("STRIPE_CUSTOMER_ID")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_SSL_MODE = os.getenv("DATABASE_SSL_MODE", "prefer")


def get_database_display_url():
    """Returns a safe-to-log database URL with masked password."""
    user = DATABASE_USERNAME or "(unset)"
    host = DATABASE_HOST or "(unset)"
    name = DATABASE_NAME or "(unset)"
    return f"postgresql://{user}:***@{host}:{DATABASE_PORT}/{name}"


VENMO_ACCESS_TOKEN = os.getenv("VENMO_ACCESS_TOKEN")
SPLITWISE_CONSUMER_KEY = os.getenv("SPLITWISE_CONSUMER_KEY")
SPLITWISE_CONSUMER_SECRET = os.getenv("SPLITWISE_CONSUMER_SECRET")
SPLITWISE_API_KEY = os.getenv("SPLITWISE_API_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_COOKIE_DOMAIN = os.getenv("JWT_COOKIE_DOMAIN")
# CORS configuration - comma-separated list of allowed origins
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://dev.localhost:5173").split(",")
# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
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
