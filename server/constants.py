from helpers import iso_8601_to_posix
import stripe, os
from enum import Enum

# TODO: Better abstraction and handling of dates

LIMIT = 1000
MOVING_DATE = "2022-08-03T00:00:00Z"
MOVING_DATE_POSIX = iso_8601_to_posix(MOVING_DATE)
USER_FIRST_NAME = "Neeraj"
PARTIES_TO_IGNORE = ["Pink Palace Babes", "Nyusha", "John Jonah"]
STRIPE_API_KEY =os.getenv('STRIPE_TEST_API_SECRET_KEY')
stripe.api_key = STRIPE_API_KEY
STRIPE_CUSTOMER_ID =os.getenv('STRIPE_CUSTOMER_ID')

class Payment_Method(Enum):
    INVALID = 1
    ALL = 2
    VENMO = 3
    SPLITWISE = 4
    STRIPE = 5
