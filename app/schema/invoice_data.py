from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class InvoiceItem(BaseModel):
    id: str
    name: str
    unit_price: float = Field(alias="unitPrice")
    quantity: int
    total: float

    model_config = ConfigDict(populate_by_name=True)

class InvoiceData(BaseModel):
    restaurant_name: str = Field(alias="restaurantName")
    restaurant_address: str = Field(alias="restaurantAddress")
    restaurant_phone_number: str = Field(alias="restaurantPhoneNumber")
    table_number: int = Field(alias="tableNumber")
    invoice_number: str = Field(alias="invoiceNumber")
    invoice_date: str = Field(alias="invoiceDate")
    items: List[InvoiceItem]
    tax: Optional[float] = Field(default=0)
    discount: Optional[float] = Field(default=0)
    total: float

    model_config = ConfigDict(populate_by_name=True)
