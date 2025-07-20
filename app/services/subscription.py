from typing import List, Optional, Set

from app.models.subscription_plan import SubscriptionPlanModel
from app.models.user_subscription import UserSubscriptionModel
from app.models.user import UserModel
from app.models.role import RoleModel
from app.models.table import TableModel
from app.models.booking import BookingModel
from app.schema import subscription_plan as plan_schema
from app.schema import user_subscription as subscription_schema
from app.schema import table as table_schema
from app.schema import bookings as booking_schema
from beanie.operators import In
from app.utils.time import now_in_luanda

plan_model = SubscriptionPlanModel()
subscription_model = UserSubscriptionModel()
user_model = UserModel()
role_model = RoleModel()
table_model = TableModel()
booking_model = BookingModel()


# Subscription Plan CRUD
async def create_plan(data: plan_schema.SubscriptionPlanCreate) -> plan_schema.SubscriptionPlanDocument:
    return await plan_model.create(data.model_dump(by_alias=True))


async def update_plan(plan_id: str, data: plan_schema.SubscriptionPlanUpdate) -> Optional[plan_schema.SubscriptionPlanDocument]:
    return await plan_model.update(plan_id, data.model_dump(exclude_none=True, by_alias=True))


async def delete_plan(plan_id: str) -> bool:
    return await plan_model.delete(plan_id)


async def get_plan(plan_id: str) -> Optional[plan_schema.SubscriptionPlanDocument]:
    return await plan_model.get(plan_id)


async def list_plans(active_only: bool = False) -> List[plan_schema.SubscriptionPlanDocument]:
    filters = {}
    if active_only:
        filters["isActive"] = True
    if filters:
        return await plan_model.get_by_fields(filters)
    return await plan_model.get_all()


# User Subscription management
async def subscribe_user(user_id: str, plan_id: str) -> subscription_schema.UserSubscriptionDocument:
    payload = subscription_schema.UserSubscriptionCreate(userId=user_id, planId=plan_id)
    return await subscription_model.create(payload.model_dump(by_alias=True))


async def unsubscribe(subscription_id: str) -> Optional[subscription_schema.UserSubscriptionDocument]:
    data = {
        "status": subscription_schema.SubscriptionStatus.CANCELADA,
        "endDate": now_in_luanda(),
    }
    return await subscription_model.update(subscription_id, data)


async def change_plan(
    subscription_id: str, plan_id: str, reason: Optional[str] = None
) -> Optional[subscription_schema.UserSubscriptionDocument]:
    data = {"planId": plan_id}
    return await subscription_model.update(subscription_id, data)


async def get_user_current_subscription(user_id: str) -> Optional[subscription_schema.UserSubscriptionDocument]:
    subs = await subscription_model.get_by_fields({
        "userId": user_id,
        "status": subscription_schema.SubscriptionStatus.ATIVA,
    })
    if not subs:
        return None
    subs.sort(key=lambda s: s.start_date, reverse=True)
    return subs[0]


async def get_usage_metrics(user_id: str) -> dict:
    """Return usage metrics for the user's subscription."""
    user = await user_model.get(user_id)
    if not user:
        return {"restaurants": 0, "tables": 0, "reservations": 0, "staff": 0}

    active_memberships = [m for m in (user.memberships or []) if m.is_active]
    role_ids = [m.role_id for m in active_memberships]
    roles = await role_model.get_many(role_ids) if role_ids else []
    restaurant_ids: Set[str] = {r.restaurant_id for r in roles}

    if not restaurant_ids:
        return {"restaurants": 0, "tables": 0, "reservations": 0, "staff": 0}

    table_count = await table_schema.TableDocument.find(
        In(table_schema.TableDocument.restaurant_id, list(restaurant_ids))
    ).count()

    reservation_count = await booking_schema.BookingDocument.find(
        In(booking_schema.BookingDocument.restaurant_id, list(restaurant_ids))
    ).count()

    roles_in_restaurants = await role_model.get_by_fields({
        "restaurantId": {"$in": list(restaurant_ids)}
    })
    allowed_role_ids = {str(r.id) for r in roles_in_restaurants}

    users = await user_model.get_by_fields({"isActive": True})
    staff_count = 0
    for u in users:
        if u.memberships:
            if any(m.is_active and m.role_id in allowed_role_ids for m in u.memberships):
                staff_count += 1

    return {
        "restaurants": len(restaurant_ids),
        "tables": table_count,
        "reservations": reservation_count,
        "staff": staff_count,
    }
