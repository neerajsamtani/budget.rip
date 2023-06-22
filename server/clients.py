import stripe
from splitwise import Splitwise
from venmo_api import Client

from constants import (
    SPLITWISE_API_KEY,
    SPLITWISE_CONSUMER_KEY,
    SPLITWISE_CONSUMER_SECRET,
    STRIPE_API_KEY,
    VENMO_ACCESS_TOKEN,
)

venmo_client = Client(access_token=VENMO_ACCESS_TOKEN)
splitwise_client = Splitwise(
    SPLITWISE_CONSUMER_KEY, SPLITWISE_CONSUMER_SECRET, api_key=SPLITWISE_API_KEY
)
stripe.api_key = STRIPE_API_KEY
