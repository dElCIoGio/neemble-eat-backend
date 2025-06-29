from typing import List

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field
from app.schema.collection_id.document_id import DocumentId  # your existing DocumentId with id, createdAt, updatedAt
from app.utils.make_optional_model import make_optional_model
from enum import Enum

class Sections(Enum):
    # 🍽️ RestaurantMenu & Ordering
    MENUS = "menus"
    CATEGORIES = "categories"
    ITEMS = "items"
    CUSTOMIZATIONS = "customizations"
    ORDERS = "orders"

    # 🛒 Customer Experience
    CUSTOMER_ORDERS_SUMMARY = "customer_orders_summary"
    TABLE_QR_ACCESS_CONTROL = "table_qr_access_control"

    # 👨‍🍳 Restaurant Operations
    KITCHEN_VIEW = "kitchen_view"
    BAR_VIEW = "bar_view"
    ORDER_QUEUE = "order_queue"
    TABLES = "tables"
    RESERVATIONS = "reservations"

    # 👥 Team & Roles
    USERS = "users"
    ROLES = "roles"
    PERMISSIONS = "permissions"

    # 💳 Sales & Billing
    SALES_DASHBOARD = "sales_dashboard"
    INVOICES = "invoices"
    PAYMENTS = "payments"
    REPORTS = "reports"

    # 📊 Analytics & Insights
    PERFORMANCE_INSIGHTS = "performance_insights"
    PRODUCT_POPULARITY = "product_popularity"
    REVENUE_TRENDS = "revenue_trends"
    CUSTOMER_FEEDBACK = "customer_feedback"

    # ⚙️ Settings & Config
    RESTAURANT_SETTINGS = "restaurant_settings"
    OPENING_HOURS = "opening_hours"
    PRINTER_SETUP = "printer_setup"
    TABLE_QR_CONFIGURATION = "table_qr_configuration"

    # 📢 Marketing & Communication
    PROMOTIONS = "promotions"
    ANNOUNCEMENTS = "announcements"
    CUSTOMER_REVIEWS = "customer_reviews"

    # 🛠️ Support & Maintenance
    SYSTEM_LOGS = "system_logs"
    INTEGRATION_SETTINGS = "integration_settings"
    HELP_REQUESTS = "help_requests"

class Permissions(BaseModel):
    can_view: bool = Field(alias="canView", default=False)
    can_edit: bool = Field(alias="canEdit", default=False)
    can_delete: bool = Field(alias="canDelete", default=False)


class SectionPermission(BaseModel):
    section: str
    permissions: Permissions = Field(default_factory=Permissions)


class RoleBase(BaseModel):
    name: str = Field(..., description="Role name, e.g., Manager, Chef")
    description: str = Field(default="", description="Role description")
    permissions: List[SectionPermission] = Field(default_factory=list)
    restaurant_id: str = Field(..., alias="restaurantId")
    level: int = Field(default=0)

    model_config = {
        "populate_by_name": True,
    }


class RoleCreate(RoleBase):
    pass  # Same fields when creating


class Role(RoleBase, DocumentId):

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

RoleUpdate = make_optional_model(RoleBase)

class RoleDocument(Document, Role):
    """Database representation for roles."""

    def to_response(self) -> "Role":
        """Convert document to API response model."""
        return Role(**self.model_dump(by_alias=True))

    class Settings:
        name = "roles"
        bson_encoders = {ObjectId: str}

