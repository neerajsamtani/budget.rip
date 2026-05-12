from pydantic import BaseModel, RootModel

from resources.schemas._common import ErrorResponse  # noqa: F401


class MonthlyBreakdownEntry(BaseModel):
    date: str
    amount: float


# RootModel is used here because the response is a bare dict with dynamic category-name keys,
# not a fixed-field object. model_dump() on a RootModel returns the root value directly.
class MonthlyBreakdownResponse(RootModel[dict[str, list[MonthlyBreakdownEntry]]]):
    pass
