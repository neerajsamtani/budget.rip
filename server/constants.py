import os

import stripe

from helpers import iso_8601_to_posix

# TODO: Better abstraction and handling of dates

LIMIT = 1000
MOVING_DATE = "2022-08-03T00:00:00Z"
MOVING_DATE_POSIX = iso_8601_to_posix(MOVING_DATE)
USER_FIRST_NAME = "Neeraj"
PARTIES_TO_IGNORE = ["Pink Palace Babes", "Nyusha", "John Jonah"]
STRIPE_API_KEY = os.getenv("STRIPE_LIVE_API_SECRET_KEY")
stripe.api_key = STRIPE_API_KEY
STRIPE_CUSTOMER_ID = os.getenv("STRIPE_CUSTOMER_ID")
MONGODB_URI = os.getenv("MONGODB_URI")
VENMO_ACCESS_TOKEN = os.getenv("VENMO_ACCESS_TOKEN")
SPLITWISE_CONSUMER_KEY = os.getenv("SPLITWISE_CONSUMER_KEY")
SPLITWISE_CONSUMER_SECRET = os.getenv("SPLITWISE_CONSUMER_SECRET")
SPLITWISE_API_KEY = os.getenv("SPLITWISE_API_KEY")
