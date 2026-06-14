"""Shared pipeline for external data source integrations (Venmo, Splitwise, Stripe).

Each source fetches raw data into the ``transactions`` table and later transforms
those stored transactions into ``LineItem`` objects. The transform → batch → upsert
half is identical across sources, so it lives here and changes in one place; the
source-specific halves (API access in ``fetch_and_store`` and field mapping in
``transactions_to_line_items``) stay in each integration subclass under ``resources/``.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from constants import BATCH_SIZE
from models.database import SessionLocal
from utils.pg_bulk_ops import bulk_upsert_line_items


class DataSourceIntegration(ABC):
    """Base class for external data source integrations.

    A new source needs only to implement the two abstract methods below; the
    batched line-item upsert is inherited.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Source tag stored on transactions and line items (e.g. ``"venmo_api"``)."""

    @abstractmethod
    def fetch_and_store(self) -> None:
        """Fetch from the external API and store raw data in the transactions table."""

    @abstractmethod
    def transactions_to_line_items(self, transactions: List[Dict[str, Any]]) -> List[Any]:
        """Transform stored transaction dicts into LineItem objects.

        May return fewer items than given (or none) when a transaction is filtered out.
        """

    def upsert_line_items(self, transactions: List[Dict[str, Any]]) -> int:
        """Transform stored transactions into line items and bulk upsert them in batches.

        Transactions are transformed one at a time so memory stays bounded by
        ``BATCH_SIZE`` regardless of how many a source returns.
        """
        inserted = 0
        batch: List[Any] = []
        for transaction in transactions:
            batch.extend(self.transactions_to_line_items([transaction]))
            if len(batch) >= BATCH_SIZE:
                inserted += self._upsert_batch(batch)
                batch = []
        if batch:
            inserted += self._upsert_batch(batch)
        return inserted

    def _upsert_batch(self, line_items: List[Any]) -> int:
        with SessionLocal.begin() as db:
            return bulk_upsert_line_items(db, line_items, source=self.source_name)
