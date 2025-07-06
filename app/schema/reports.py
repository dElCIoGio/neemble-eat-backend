from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class SalesReport(BaseModel):
    date: datetime
    gross_sales: float = Field(..., alias="grossSales")
    orders: int

    model_config = ConfigDict(
        populate_by_name=True
    )


class SalesReportPagination(BaseModel):
    """Paginated list of ``SalesReport`` entries."""

    items: list[SalesReport]
    next_cursor: str | None = Field(default=None, alias="nextCursor")
    total_count: int = Field(..., alias="totalCount")
    has_more: bool = Field(..., alias="hasMore")

    model_config = ConfigDict(populate_by_name=True)
