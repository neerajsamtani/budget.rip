import logging
from typing import Any, Dict, List, Optional

import requests  # Still needed for Authorization endpoint (not yet in SDK)
import stripe
from apiflask import APIBlueprint, abort
from flask_jwt_extended import jwt_required

from constants import BATCH_SIZE, STRIPE_API_KEY, STRIPE_CUSTOMER_EMAIL, STRIPE_CUSTOMER_ID, STRIPE_CUSTOMER_NAME
from dao import (
    get_all_bank_accounts,
    get_transactions,
)
from helpers import cents_to_dollars, flip_amount
from models.database import SessionLocal
from resources.line_item import LineItem
from resources.schemas.stripe import (
    AccountsAndBalancesResponse,
    CreateAccountsIn,
    CreateAccountsResponse,
    ErrorResponse,
    FcSessionResponse,
    GetAccountsResponse,
    RefreshAccountResponse,
    RefreshResponse,
    RelinkResponse,
    SubscribeStatusResponse,
    SubscribeToAccountIn,
)
from utils.pg_bulk_ops import (
    bulk_upsert_bank_accounts,
    bulk_upsert_line_items,
    bulk_upsert_transactions,
)

logger = logging.getLogger(__name__)

stripe_blueprint = APIBlueprint("stripe", __name__)

_SECURITY = [{"jwtCookie": []}]
_ERROR_RESPONSES = {
    400: {"description": "Bad request", "schema": ErrorResponse},
    404: {"description": "Not found", "schema": ErrorResponse},
}

if STRIPE_API_KEY is None:
    raise Exception("Stripe API Key is not set")
if STRIPE_CUSTOMER_ID is None:
    raise Exception("Stripe Customer ID is not set")

stripe.api_version = "2022-08-01; financial_connections_transactions_beta=v1; financial_connections_relink_api_beta=v1"

# Initialize StripeClient for service-based API access
stripe_client = stripe.StripeClient(api_key=STRIPE_API_KEY)


def check_can_relink(account: stripe.financial_connections.Account) -> bool:
    """Check if inactive account can be relinked. Active accounts return False (don't need relink)."""
    if account.get("status") == "active":
        return False

    if account.get("status") == "inactive":
        try:
            auth_id = account.get("authorization")
            if not auth_id:
                return False

            response = requests.get(
                f"https://api.stripe.com/v1/financial_connections/authorizations/{auth_id}",
                headers={"Stripe-Version": "2022-08-01; financial_connections_relink_api_beta=v1"},
                auth=(STRIPE_API_KEY, ""),
            )
            authorization = response.json()

            # Account closed at institution - can't relink even if auth is still active
            if authorization.get("status") == "active":
                return False

            if authorization.get("status") == "inactive":
                status_details = authorization.get("status_details", {})
                inactive_details = status_details.get("inactive", {})
                return inactive_details.get("action") == "relink_required"

            return False
        except Exception as e:
            logger.error(f"Error checking relink status for account {account.get('id')}: {e}")
            return False  # Default to False on error - safer than allowing broken relinks

    return False


def refresh_account_balances(account_ids: Optional[List[str]] = None) -> int:
    """
    Fetch and store latest balance for Stripe accounts (best-effort operation).

    Solves N+1 problem: Previously fetched balances via N individual Stripe API
    calls during page load. Now pre-fetches and stores on account records.

    Best-effort: Balance refresh failures are logged but don't break parent operations
    (account/transaction refresh). Balances are supplementary data.

    Args:
        account_ids: Optional list of specific account IDs to refresh. If None, refreshes all accounts.

    Returns:
        Count of accounts updated with balance info
    """
    from datetime import datetime, timezone

    if account_ids:
        all_accounts = get_all_bank_accounts(None)
        accounts = [acc for acc in all_accounts if acc["id"] in account_ids]
    else:
        accounts = get_all_bank_accounts(None)

    updated_count = 0

    for account in accounts:
        account_id = account["id"]

        try:
            logger.info(f"Fetching latest balance for account {account_id}")

            # Fetch latest balance only (limit=1)
            balances = stripe_client.v1.financial_connections.accounts.inferred_balances.list(
                account=account_id,
                params={"limit": 1},
            )

            if balances.data:
                balance_data = balances.data[0]
                # Stripe inferred balances support multiple currencies
                currency = next(iter(balance_data.current.keys()))
                balance_cents = balance_data.current[currency]

                account["currency"] = currency
                account["latest_balance"] = balance_cents / 100  # Convert from cents
                account["balance_as_of"] = datetime.fromtimestamp(balance_data.as_of, tz=timezone.utc)

                with SessionLocal.begin() as db:
                    bulk_upsert_bank_accounts(db, [account])

                updated_count += 1
                logger.info(f"Updated balance for account {account_id}: {balance_cents / 100} {currency}")

        except Exception as e:
            logger.error(f"Error fetching balance for account {account_id}: {e}")
            # Continue with other accounts even if one fails

    return updated_count


def _build_fc_session(relink_auth: Optional[str] = None) -> FcSessionResponse:
    """Core session creation logic shared by create_fc_session_api and relink_account_api."""
    try:
        try:
            customer: stripe.Customer = stripe.Customer.retrieve(STRIPE_CUSTOMER_ID)
        except stripe.InvalidRequestError:
            logger.info("Creating a new customer...")
            customer: stripe.Customer = stripe.Customer.create(email=STRIPE_CUSTOMER_EMAIL, name=STRIPE_CUSTOMER_NAME)

        session_params: Dict[str, Any] = {
            "account_holder": {"type": "customer", "customer": customer["id"]},
            "permissions": ["transactions", "balances"],
        }

        if relink_auth:
            session_params["relink_options"] = {"authorization": relink_auth}

        session = stripe.financial_connections.Session.create(**session_params)
        return FcSessionResponse(clientSecret=session["client_secret"])
    except Exception as e:
        abort(500, message=str(e))


@stripe_blueprint.get("/api/refresh/stripe")
@stripe_blueprint.output(RefreshResponse)
@stripe_blueprint.doc(security=_SECURITY)
@jwt_required()
def refresh_stripe_api():
    refresh_stripe()
    return RefreshResponse(message="Refreshed Stripe Connection")


@stripe_blueprint.post("/api/create-fc-session")
@stripe_blueprint.output(FcSessionResponse)
@stripe_blueprint.doc(security=_SECURITY, responses=_ERROR_RESPONSES)
@jwt_required()
def create_fc_session_api():
    return _build_fc_session()


@stripe_blueprint.post("/api/create_accounts")
@stripe_blueprint.input(CreateAccountsIn, arg_name="body")
@stripe_blueprint.output(CreateAccountsResponse, status_code=201)
@stripe_blueprint.doc(security=_SECURITY, responses=_ERROR_RESPONSES)
@jwt_required()
def create_accounts_api(body: CreateAccountsIn):
    new_accounts = body.root
    if len(new_accounts) == 0:
        abort(400, message="Failed to Create Accounts: No Accounts Submitted")

    with SessionLocal.begin() as db:
        bulk_upsert_bank_accounts(db, new_accounts)

    return CreateAccountsResponse(data=new_accounts), 201


@stripe_blueprint.get("/api/get_accounts/<session_id>")
@stripe_blueprint.output(GetAccountsResponse)
@stripe_blueprint.doc(security=_SECURITY, responses=_ERROR_RESPONSES)
@jwt_required()
def get_accounts_api(session_id: str):
    try:
        session: stripe.financial_connections.Session = stripe.financial_connections.Session.retrieve(session_id)
        accounts: List[Dict[str, Any]] = session["accounts"]

        with SessionLocal.begin() as db:
            bulk_upsert_bank_accounts(db, accounts)

        return GetAccountsResponse(accounts=accounts)
    except Exception as e:
        abort(500, message=str(e))


@stripe_blueprint.get("/api/accounts_and_balances")
@stripe_blueprint.output(AccountsAndBalancesResponse)
@stripe_blueprint.doc(security=_SECURITY)
@jwt_required()
def get_accounts_and_balances_api():
    """
    Get bank accounts with their latest balances.

    Balances are pre-fetched and stored on account records via refresh_account_balances()
    to avoid N+1 query problem (previously made one Stripe API call per account).
    """
    accounts: List[Dict[str, Any]] = get_all_bank_accounts(None)
    accounts_and_balances: Dict[str, Dict[str, Any]] = {}

    for account in accounts:
        account_id: str = account["id"]
        account_name: str = f"{account['institution_name']} {account['display_name']} {account['last4']}"

        if "can_relink" not in account:
            account["can_relink"] = check_can_relink(account)

        balance = account.get("latest_balance", 0)
        as_of_dt = account.get("balance_as_of")
        as_of = int(as_of_dt.timestamp()) if as_of_dt else None
        currency = account.get("currency", "usd")

        accounts_and_balances[account_id] = {
            "id": account_id,
            "name": account_name,
            "balance": balance,
            "currency": currency,
            "as_of": as_of,
            "status": account["status"],
            "can_relink": account["can_relink"],
        }

    return AccountsAndBalancesResponse(accounts_and_balances)


@stripe_blueprint.post("/api/subscribe_to_account")
@stripe_blueprint.input(SubscribeToAccountIn, arg_name="body")
@stripe_blueprint.output(SubscribeStatusResponse)
@stripe_blueprint.doc(security=_SECURITY, responses=_ERROR_RESPONSES)
@jwt_required()
def subscribe_to_account_api(body: SubscribeToAccountIn):
    try:
        response = stripe.financial_connections.Account.subscribe(
            body.account_id, features=["transactions", "inferred_balances"]
        )
        refresh_status: str = response.get("transaction_refresh", {}).get("status", "unknown")
        return SubscribeStatusResponse(status=str(refresh_status))
    except Exception as e:
        abort(500, message=str(e))


@stripe_blueprint.get("/api/refresh_account/<account_id>")
@stripe_blueprint.output(RefreshAccountResponse)
@stripe_blueprint.doc()
def refresh_account_api(account_id: str):
    try:
        logger.info(f"Refreshing {account_id}")
        account: stripe.financial_connections.Account = stripe.financial_connections.Account.retrieve(account_id)
        account["can_relink"] = check_can_relink(account)

        with SessionLocal.begin() as db:
            bulk_upsert_bank_accounts(db, [account])

        return RefreshAccountResponse(data="success")
    except Exception as e:
        abort(500, message=str(e))


@stripe_blueprint.post("/api/relink_account/<account_id>")
@stripe_blueprint.output(RelinkResponse)
@stripe_blueprint.doc(security=_SECURITY, responses=_ERROR_RESPONSES)
@jwt_required()
def relink_account_api(account_id: str):
    try:
        logger.info(f"Relinking {account_id}")
        account: stripe.financial_connections.Account = stripe.financial_connections.Account.retrieve(account_id)

        if not check_can_relink(account):
            return RelinkResponse(relink_required=False)

        session = _build_fc_session(account["authorization"])
        return RelinkResponse(clientSecret=session.clientSecret)
    except Exception as e:
        abort(500, message=str(e))


@stripe_blueprint.get("/api/refresh_transactions/<account_id>")
@stripe_blueprint.output(RefreshResponse)
@stripe_blueprint.doc()
def refresh_transactions_api(account_id: str):
    logger.info(f"Getting Transactions for {account_id}")
    # TODO: This gets all transactions ever. We should only get those that we don't have
    try:
        has_more: bool = True
        starting_after = ""
        all_transactions: List[Dict[str, Any]] = []
        stripe.api_key = STRIPE_API_KEY
        stripe.api_version = "2022-08-01; financial_connections_transactions_beta=v1"

        while has_more:
            transactions_list_params = {
                "account": account_id,
                "limit": 100,
            }
            if starting_after:
                transactions_list_params["starting_after"] = starting_after

            transactions_list_object = stripe.financial_connections.Transaction.list(**transactions_list_params)

            transactions = transactions_list_object.data

            for transaction in transactions:
                if transaction.status == "posted":
                    all_transactions.append(transaction)
                elif transaction.status == "pending":
                    logger.info(
                        f"Pending Transaction: {transaction.description} | "
                        + f"{cents_to_dollars(flip_amount(transaction.amount))}"
                    )

            has_more = transactions_list_object.has_more
            starting_after = transactions[-1].id if transactions else ""

        if all_transactions:
            with SessionLocal.begin() as db:
                bulk_upsert_transactions(db, all_transactions, source="stripe_api")

        # Best-effort: fetch latest balance for this account (won't fail transaction refresh)
        refresh_account_balances(account_ids=[account_id])

        return RefreshResponse(message="Refreshed Stripe Connection for Given Account")

    except Exception as e:
        abort(500, message=str(e))


def refresh_stripe() -> None:
    logger.info("Refreshing Stripe Data")
    bank_accounts: List[Dict[str, Any]] = get_all_bank_accounts(None)
    for account in bank_accounts:
        refresh_account_api(account["id"])
        refresh_transactions_api(account["id"])
    stripe_to_line_items()
    # Best-effort: refresh balances for all accounts after transactions updated
    refresh_account_balances()


def stripe_to_line_items() -> None:
    """
    Convert Stripe transactions to line items with optimized database operations.

    Optimizations:
    1. Pre-fetch all accounts and create a lookup dictionary to avoid repeated database calls
    2. Use bulk upsert operations instead of individual upserts
    3. Process transactions in batches to handle large datasets efficiently
    """
    all_bank_accounts: List[Dict[str, Any]] = get_all_bank_accounts(None)
    bank_account_lookup: Dict[str, Dict[str, Any]] = {account["id"]: account for account in all_bank_accounts}

    stripe_raw_data: List[Dict[str, Any]] = get_transactions("stripe_api", None)

    line_items_batch: List[LineItem] = []

    for stripe_transaction in stripe_raw_data:
        # Use memoized account lookup instead of database call
        stripe_account: Optional[Dict[str, Any]] = bank_account_lookup.get(stripe_transaction["account"])

        if stripe_account:
            payment_method: str = stripe_account["display_name"]
        else:
            payment_method = "Stripe"

        line_item = LineItem(
            stripe_transaction["transacted_at"],
            stripe_transaction["description"],
            payment_method,
            stripe_transaction["description"],
            flip_amount(stripe_transaction["amount"]) / 100,
            source_id=str(stripe_transaction["source_id"]),
        )

        line_items_batch.append(line_item)

        if len(line_items_batch) >= BATCH_SIZE:
            with SessionLocal.begin() as db:
                bulk_upsert_line_items(db, line_items_batch, source="stripe_api")
            line_items_batch = []

    if line_items_batch:
        with SessionLocal.begin() as db:
            bulk_upsert_line_items(db, line_items_batch, source="stripe_api")
