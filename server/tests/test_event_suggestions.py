from datetime import UTC, datetime

from models.sql_models import Category, Event, EventHint, EventLineItem, EventSuggestion, LineItem, PaymentMethod, Transaction
from utils.event_suggestions import generate_event_suggestions


def create_matching_line_item_and_hint(pg_session, *, category: bool = True):
    payment_method = pg_session.query(PaymentMethod).first()
    subscription = pg_session.query(Category).filter_by(user_id="user_id", name="Subscription").first()
    transaction = Transaction(
        id="txn_suggestion",
        source="manual",
        source_id="suggestion_source",
        source_data={},
        transaction_date=datetime.now(UTC),
    )
    line_item = LineItem(
        id="li_suggestion",
        transaction_id=transaction.id,
        date=datetime.now(UTC),
        description="Spotify Premium",
        amount=12.99,
        payment_method_id=payment_method.id,
    )
    hint = EventHint(
        id="eh_suggestion",
        user_id="user_id",
        name="Spotify purchases",
        cel_expression='description.contains("Spotify")',
        prefill_name="Spotify",
        prefill_category_id=subscription.id if category else None,
        display_order=0,
        is_active=True,
    )
    pg_session.add_all([transaction, line_item, hint])
    pg_session.commit()
    return line_item, subscription


def test_refresh_generation_materializes_matching_categorized_hint(pg_session, test_client, jwt_token):
    line_item, _ = create_matching_line_item_and_hint(pg_session)

    assert generate_event_suggestions("user_id") == 1

    response = test_client.get(
        "/api/line_items?only_line_items_to_review=true",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    suggestion = next(item for item in response.get_json()["data"] if item["id"] == line_item.id)["event_suggestion"]
    assert suggestion["name"] == "Spotify"
    assert suggestion["category"] == "Subscription"
    assert suggestion["matched_hint_name"] == "Spotify purchases"


def test_hint_without_category_does_not_create_quick_suggestion(pg_session):
    create_matching_line_item_and_hint(pg_session, category=False)

    assert generate_event_suggestions("user_id") == 0
    assert pg_session.query(EventSuggestion).count() == 0


def test_rejected_suggestion_is_not_regenerated(pg_session, test_client, jwt_token):
    create_matching_line_item_and_hint(pg_session)
    generate_event_suggestions("user_id")
    suggestion = pg_session.query(EventSuggestion).one()

    response = test_client.post(
        f"/api/event-suggestions/{suggestion.id}/reject",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )

    pg_session.expire_all()
    assert response.status_code == 204
    assert pg_session.query(EventSuggestion).one().rejected_at is not None
    assert generate_event_suggestions("user_id") == 0


def test_accepting_suggestion_with_edited_title_creates_event_and_deletes_suggestion(pg_session, test_client, jwt_token):
    line_item, _ = create_matching_line_item_and_hint(pg_session)
    generate_event_suggestions("user_id")
    suggestion = pg_session.query(EventSuggestion).one()

    response = test_client.post(
        f"/api/event-suggestions/{suggestion.id}/accept",
        json={"name": "My Spotify subscription"},
        headers={"Authorization": f"Bearer {jwt_token}"},
    )

    pg_session.expire_all()
    assert response.status_code == 201
    assert response.get_json()["name"] == "My Spotify subscription"
    event = pg_session.query(Event).one()
    assert event.description == "My Spotify subscription"
    assert pg_session.query(EventLineItem).filter_by(event_id=event.id, line_item_id=line_item.id).one()
    assert pg_session.query(EventSuggestion).count() == 0


def test_normal_event_creation_also_deletes_suggestion(pg_session, test_client, jwt_token):
    line_item, _ = create_matching_line_item_and_hint(pg_session)
    generate_event_suggestions("user_id")

    response = test_client.post(
        "/api/events",
        json={
            "name": "Created normally",
            "category": "Subscription",
            "line_items": [line_item.id],
        },
        headers={"Authorization": f"Bearer {jwt_token}"},
    )

    pg_session.expire_all()
    assert response.status_code == 201
    assert pg_session.query(EventSuggestion).count() == 0
