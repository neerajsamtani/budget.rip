from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from models.sql_models import (
    Category,
    Event,
    EventHint,
    EventLineItem,
    EventSuggestion,
    LineItem,
    PaymentMethod,
    Transaction,
    User,
)
from utils.event_suggestions import generate_event_suggestions, insert_unless_already_suggested


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


def classify_as_stripe(pg_session, line_item, primary="food_and_drink", detailed="groceries", confidence="high"):
    line_item.transaction.source = "stripe_api"
    line_item.transaction.source_data = {
        "description": "Raw bank text",
        "classifications": [
            {
                "type": "personal_finance",
                "personal_finance": {"primary_label": primary, "detailed_label": detailed, "confidence_level": confidence},
            }
        ],
    }
    pg_session.commit()


@pytest.fixture
def stripe_line_item(pg_session):
    line_item, _ = create_matching_line_item_and_hint(pg_session)
    pg_session.query(EventHint).delete()
    line_item.description = "WHOLEFDS #123"
    line_item.responsible_party = "Whole Foods"
    classify_as_stripe(pg_session, line_item)
    return line_item


def review_suggestions(test_client, jwt_token):
    response = test_client.get(
        "/api/line_items?only_line_items_to_review=true",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    return {item["id"]: item["event_suggestion"] for item in response.get_json()["data"]}


def accept(test_client, jwt_token, suggestion_id, payload):
    return test_client.post(
        f"/api/event-suggestions/{suggestion_id}/accept",
        json=payload,
        headers={"Authorization": f"Bearer {jwt_token}"},
    )


def test_stripe_suggestion_is_materialized_without_any_hints(pg_session, test_client, jwt_token, stripe_line_item):
    groceries = pg_session.query(Category).filter_by(user_id="user_id", name="Groceries").one()

    assert generate_event_suggestions("user_id") == 1

    suggestion = review_suggestions(test_client, jwt_token)[stripe_line_item.id]
    assert suggestion == {
        "id": pg_session.query(EventSuggestion).one().id,
        "name": "Whole Foods",
        "category_id": groceries.id,
        "category": "Groceries",
        "matched_hint_name": None,
        "source": "stripe_personal_finance",
        "source_metadata": {
            "mapping_version": 1,
            "primary_label": "food_and_drink",
            "detailed_label": "groceries",
            "confidence_level": "high",
        },
    }


def test_categorized_hint_wins_over_stripe_category(pg_session, test_client, jwt_token):
    line_item, subscription = create_matching_line_item_and_hint(pg_session)
    classify_as_stripe(pg_session, line_item)

    generate_event_suggestions("user_id")

    suggestion = pg_session.query(EventSuggestion).one()
    assert (suggestion.source, suggestion.category_id, suggestion.suggested_name) == ("event_hint", subscription.id, "Spotify")
    assert suggestion.event_hint_id == "eh_suggestion"
    assert review_suggestions(test_client, jwt_token)[line_item.id]["source_metadata"] == {}


def test_name_only_hint_supplies_title_for_stripe_category(pg_session, test_client, jwt_token):
    line_item, _ = create_matching_line_item_and_hint(pg_session, category=False)
    classify_as_stripe(pg_session, line_item)

    assert generate_event_suggestions("user_id") == 1

    suggestion = review_suggestions(test_client, jwt_token)[line_item.id]
    assert suggestion["name"] == "Spotify"
    assert suggestion["category"] == "Groceries"
    assert suggestion["matched_hint_name"] == "Spotify purchases"
    assert suggestion["source"] == "stripe_personal_finance"
    assert suggestion["source_metadata"]["name_hint_id"] == "eh_suggestion"
    assert pg_session.query(EventSuggestion).one().event_hint_id == "eh_suggestion"


def test_stripe_category_missing_from_users_categories_creates_nothing(pg_session, stripe_line_item):
    pg_session.query(Category).filter_by(user_id="user_id", name="Groceries").delete()
    pg_session.commit()

    assert generate_event_suggestions("user_id") == 0
    assert pg_session.query(EventSuggestion).count() == 0


@pytest.mark.parametrize("rejected", [False, True])
def test_existing_suggestion_snapshot_is_preserved_on_regeneration(pg_session, stripe_line_item, rejected):
    pg_session.add(
        EventSuggestion(
            id="es_existing",
            user_id="user_id",
            line_item_id=stripe_line_item.id,
            suggested_name="Old title",
            rejected_at=datetime.now(UTC) if rejected else None,
        )
    )
    pg_session.commit()

    assert generate_event_suggestions("user_id") == 0

    pg_session.expire_all()
    existing = pg_session.query(EventSuggestion).one()
    assert (existing.id, existing.suggested_name, existing.category_id) == ("es_existing", "Old title", None)
    assert existing.source == "event_hint"
    assert (existing.rejected_at is not None) == rejected


def test_line_item_already_in_event_is_not_suggested(pg_session, test_client, jwt_token, stripe_line_item):
    response = test_client.post(
        "/api/events",
        json={"name": "Groceries run", "category": "Groceries", "line_items": [stripe_line_item.id]},
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    assert response.status_code == 201

    assert generate_event_suggestions("user_id") == 0


def test_legacy_suggestion_whose_hint_was_deleted_is_still_listed(pg_session, test_client, jwt_token):
    line_item, subscription = create_matching_line_item_and_hint(pg_session)
    generate_event_suggestions("user_id")
    pg_session.query(EventHint).delete()
    pg_session.commit()

    suggestion = review_suggestions(test_client, jwt_token)[line_item.id]
    assert suggestion["matched_hint_name"] is None
    assert suggestion["category_id"] == subscription.id
    assert suggestion["source"] == "event_hint"


def test_another_users_category_is_not_exposed_in_review_list(pg_session, test_client, jwt_token):
    line_item, _ = create_matching_line_item_and_hint(pg_session)
    other = User(id="other_user", first_name="O", last_name="U", email="other@example.com", password_hash="x")
    other_category = Category(id="cat_other", user_id="other_user", name="Secret")
    pg_session.add_all([other, other_category])
    pg_session.flush()
    pg_session.add(
        EventSuggestion(
            id="es_foreign", user_id="user_id", line_item_id=line_item.id, suggested_name="X", category_id="cat_other"
        )
    )
    pg_session.commit()

    suggestion = review_suggestions(test_client, jwt_token)[line_item.id]
    assert (suggestion["category_id"], suggestion["category"]) == (None, None)


def test_suggestion_whose_category_was_deleted_stays_listed_without_a_category(pg_session, test_client, jwt_token):
    line_item, subscription = create_matching_line_item_and_hint(pg_session)
    generate_event_suggestions("user_id")
    pg_session.query(EventSuggestion).update({"category_id": None})
    pg_session.commit()

    suggestion = review_suggestions(test_client, jwt_token)[line_item.id]
    assert (suggestion["name"], suggestion["category_id"], suggestion["category"]) == ("Spotify", None, None)


def test_name_only_hint_does_not_shadow_later_categorized_hint(pg_session):
    _, subscription = create_matching_line_item_and_hint(pg_session)
    pg_session.add(
        EventHint(
            id="eh_name_only",
            user_id="user_id",
            name="Spotify name",
            cel_expression='description.contains("Spotify")',
            prefill_name="Music",
            display_order=-1,
            is_active=True,
        )
    )
    pg_session.commit()

    assert generate_event_suggestions("user_id") == 1

    suggestion = pg_session.query(EventSuggestion).one()
    assert (suggestion.event_hint_id, suggestion.suggested_name, suggestion.category_id) == (
        "eh_suggestion",
        "Spotify",
        subscription.id,
    )


def test_users_without_hints_skip_hint_evaluation(pg_session, mocker, stripe_line_item):
    evaluate = mocker.patch("utils.category_suggestions.evaluate_hints")

    assert generate_event_suggestions("user_id") == 1
    evaluate.assert_not_called()


def test_accepting_with_corrected_category_creates_event_in_that_category(
    pg_session, test_client, jwt_token, stripe_line_item
):
    generate_event_suggestions("user_id")
    suggestion = pg_session.query(EventSuggestion).one()
    dining = pg_session.query(Category).filter_by(user_id="user_id", name="Dining").one()

    response = accept(test_client, jwt_token, suggestion.id, {"name": "Lunch", "category_id": dining.id})

    pg_session.expire_all()
    assert response.status_code == 201
    assert response.get_json()["category"] == "Dining"
    event = pg_session.query(Event).one()
    assert (event.description, event.category_id) == ("Lunch", dining.id)
    assert pg_session.query(EventLineItem).filter_by(event_id=event.id, line_item_id=stripe_line_item.id).one()
    assert pg_session.query(EventSuggestion).count() == 0


@pytest.mark.parametrize("category_id", ["cat_other", "cat_missing", 42])
def test_accepting_with_unowned_category_is_rejected_without_consuming_suggestion(
    pg_session, test_client, jwt_token, stripe_line_item, category_id
):
    pg_session.add(User(id="other_user", first_name="O", last_name="U", email="other@example.com", password_hash="x"))
    pg_session.flush()
    pg_session.add(Category(id="cat_other", user_id="other_user", name="Groceries"))
    pg_session.commit()
    generate_event_suggestions("user_id")

    response = accept(test_client, jwt_token, pg_session.query(EventSuggestion).one().id, {"category_id": category_id})

    pg_session.expire_all()
    assert response.status_code == 400
    assert response.get_json()["error"] == "Category not found"
    assert pg_session.query(EventSuggestion).count() == 1
    assert pg_session.query(Event).count() == 0


def test_empty_category_override_keeps_the_suggested_category(pg_session, test_client, jwt_token, stripe_line_item):
    generate_event_suggestions("user_id")

    response = accept(test_client, jwt_token, pg_session.query(EventSuggestion).one().id, {"category_id": ""})

    assert response.status_code == 201
    assert response.get_json()["category"] == "Groceries"


def test_unavailable_stored_category_requires_a_correction(pg_session, test_client, jwt_token, stripe_line_item):
    generate_event_suggestions("user_id")
    suggestion = pg_session.query(EventSuggestion).one()
    suggestion.category_id = None
    pg_session.commit()
    dining = pg_session.query(Category).filter_by(user_id="user_id", name="Dining").one()

    missing = accept(test_client, jwt_token, suggestion.id, {})
    corrected = accept(test_client, jwt_token, suggestion.id, {"category_id": dining.id})

    assert missing.status_code == 409
    assert missing.get_json()["error"] == "Suggested category is no longer available"
    assert corrected.status_code == 201
    assert corrected.get_json()["category"] == "Dining"


def test_concurrently_inserted_suggestion_is_skipped(pg_session, stripe_line_item):
    pg_session.add(
        EventSuggestion(id="es_winner", user_id="user_id", line_item_id=stripe_line_item.id, suggested_name="Winner")
    )
    pg_session.flush()

    loser = EventSuggestion(id="es_loser", user_id="user_id", line_item_id=stripe_line_item.id, suggested_name="Loser")
    assert insert_unless_already_suggested(pg_session, loser) is False

    assert [s.id for s in pg_session.query(EventSuggestion).all()] == ["es_winner"]


def test_other_integrity_failures_propagate(pg_session, stripe_line_item):
    pg_session.add(EventSuggestion(id="es_taken", user_id="user_id", line_item_id=stripe_line_item.id, suggested_name="A"))
    pg_session.flush()
    other_transaction = Transaction(
        id="txn_other", source="manual", source_id="other", source_data={}, transaction_date=datetime.now(UTC)
    )
    other_item = LineItem(
        id="li_other",
        transaction_id=other_transaction.id,
        date=datetime.now(UTC),
        description="Other",
        amount=1,
        payment_method_id=stripe_line_item.payment_method_id,
    )
    pg_session.add_all([other_transaction, other_item])
    pg_session.flush()

    with pytest.raises(IntegrityError):
        insert_unless_already_suggested(
            pg_session, EventSuggestion(id="es_taken", user_id="user_id", line_item_id=other_item.id, suggested_name="B")
        )


def test_users_with_only_name_only_hints_skip_non_stripe_items(pg_session, mocker):
    create_matching_line_item_and_hint(pg_session, category=False)
    evaluate = mocker.patch("utils.category_suggestions.evaluate_hints")

    assert generate_event_suggestions("user_id") == 0
    evaluate.assert_not_called()
