from pydantic import BaseModel, Field


class ItemOrderQuantity(BaseModel):
    item_id: str = Field(..., alias="itemId")
    item_name: str = Field(..., alias="itemName")
    quantity: int = 0


class SalesSummary(BaseModel):
    total_sales: float = Field(..., alias="totalSales")
    invoice_count: int = Field(..., alias="invoiceCount")
    average_invoice: float = Field(..., alias="averageInvoice")
    distinct_tables: int = Field(..., alias="distinctTables")
    revenue_per_table: float = Field(..., alias="revenuePerTable")


class InvoiceCount(BaseModel):
    invoice_count: int = Field(..., alias="invoiceCount")


class OrderCount(BaseModel):
    order_count: int = Field(..., alias="orderCount")


class CancelledCount(BaseModel):
    cancelled_count: int = Field(..., alias="cancelledCount")


class AverageSessionDuration(BaseModel):
    average_duration_minutes: float = Field(..., alias="averageDurationMinutes")


class ActiveSessionCount(BaseModel):
    active_sessions: int = Field(..., alias="activeSessions")