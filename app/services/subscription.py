from typing import List, Optional

from app.models.subscription_plan import SubscriptionPlanModel
from app.models.user_subscription import UserSubscriptionModel
from app.schema import subscription_plan as plan_schema
from app.schema import user_subscription as subscription_schema
from app.utils.time import now_in_luanda

plan_model = SubscriptionPlanModel()
subscription_model = UserSubscriptionModel()


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
        "status": subscription_schema.SubscriptionStatus.CANCELLED,
        "endDate": now_in_luanda(),
    }
    return await subscription_model.update(subscription_id, data)


async def get_user_current_subscription(user_id: str) -> Optional[subscription_schema.UserSubscriptionDocument]:
    subs = await subscription_model.get_by_fields({
        "userId": user_id,
        "status": subscription_schema.SubscriptionStatus.ACTIVE,
    })
    if not subs:
        return None
    subs.sort(key=lambda s: s.start_date, reverse=True)
    return subs[0]
