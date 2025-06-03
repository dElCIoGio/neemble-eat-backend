from pydantic import BaseModel, Field, ConfigDict


class ItemOrderQuantity(BaseModel):
    item_id: str = Field(..., alias="itemId")
    item_name: str = Field(..., alias="itemName")
    quantity: int = 0

    model_config = ConfigDict(
        populate_by_name=True
    )


class SalesSummary(BaseModel):
    total_sales: float = Field(..., alias="totalSales")
    invoice_count: int = Field(..., alias="invoiceCount")
    average_invoice: float = Field(..., alias="averageInvoice")
    distinct_tables: int = Field(..., alias="distinctTables")
    revenue_per_table: float = Field(..., alias="revenuePerTable")

    model_config = ConfigDict(
        populate_by_name=True
    )


class InvoiceCount(BaseModel):
    invoice_count: int = Field(..., alias="invoiceCount")

    model_config = ConfigDict(
        populate_by_name=True
    )


class OrderCount(BaseModel):
    order_count: int = Field(..., alias="orderCount")

    model_config = ConfigDict(
        populate_by_name=True
    )


class CancelledCount(BaseModel):
    cancelled_count: int = Field(..., alias="cancelledCount")

    model_config = ConfigDict(
        populate_by_name=True
    )


class AverageSessionDuration(BaseModel):
    average_duration_minutes: float = Field(..., alias="averageDurationMinutes")

    model_config = ConfigDict(
        populate_by_name=True
    )


class ActiveSessionCount(BaseModel):
    active_sessions: int = Field(..., alias="activeSessions")

    model_config = ConfigDict(
        populate_by_name=True
    )


class TotalOrdersCount(BaseModel):
    date: str
    sales: int
    day: str