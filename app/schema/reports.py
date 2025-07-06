from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class SalesReport(BaseModel):
    date: datetime
    gross_sales: float = Field(..., alias="grossSales")
    orders: int

    model_config = ConfigDict(
        populate_by_name=True
    )