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
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/test_db") # Change to LIVE_MONGO_URI if you want to use the live database
VENMO_ACCESS_TOKEN = os.getenv("VENMO_ACCESS_TOKEN")
SPLITWISE_CONSUMER_KEY = os.getenv("SPLITWISE_CONSUMER_KEY")
SPLITWISE_CONSUMER_SECRET = os.getenv("SPLITWISE_CONSUMER_SECRET")
SPLITWISE_API_KEY = os.getenv("SPLITWISE_API_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "testSecretKey123")
JWT_COOKIE_DOMAIN = os.getenv("JWT_COOKIE_DOMAIN")
SMALLEST_EPOCH_TIME = float(0)
LARGEST_EPOCH_TIME = float(9999999999)
