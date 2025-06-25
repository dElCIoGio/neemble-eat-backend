from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query

from app.services import subscription as subscription_service
from app.schema import subscription_plan as plan_schema
from app.schema import user_subscription as subscription_schema
from app.services.subscription import subscription_model, plan_model
from app.utils.auth import admin_required

router = APIRouter()


# Subscription Plan CRUD

@router.get("/plans/paginate")
async def paginate_plans(
    limit: int = Query(10, gt=0),
    cursor: Optional[str] = Query(None),
):
    try:
        filters: Dict[str, Any] = {}

        result = await plan_model.paginate(filters=filters, limit=limit, cursor=cursor)

        return result
    except Exception as error:
        print(error)

@router.post('/plans', dependencies=[Depends(admin_required)])
async def create_plan(data: plan_schema.SubscriptionPlanCreate):
    try:
        plan = await subscription_service.create_plan(data)
        return plan.to_response()
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.put('/plans/{plan_id}', dependencies=[Depends(admin_required)])
async def update_plan(plan_id: str, data: plan_schema.SubscriptionPlanUpdate):
    updated = await subscription_service.update_plan(plan_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail='Plan not found')
    return updated.to_response()


@router.delete('/plans/{plan_id}', dependencies=[Depends(admin_required)])
async def delete_plan(plan_id: str):
    deleted = await subscription_service.delete_plan(plan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Plan not found')
    return True


@router.get('/plans/{plan_id}')
async def get_plan(plan_id: str):
    plan = await subscription_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail='Plan not found')
    return plan.to_response()


@router.get('/plans')
async def list_available_plans():
    plans = await subscription_service.list_plans(active_only=True)
    return [p.to_response() for p in plans]


@router.get('/plans/all', dependencies=[Depends(admin_required)])
async def list_all_plans():
    plans = await subscription_service.list_plans()
    return [p.to_response() for p in plans]


# User Subscription Endpoints

@router.get("/subscriptions/paginate")
async def paginate_subscriptions(
    limit: int = Query(10, gt=0),
    cursor: Optional[str] = Query(None),
):
    try:
        filters: Dict[str, Any] = {}

        result = await subscription_model.paginate(filters=filters, limit=limit, cursor=cursor)

        return result
    except Exception as error:
        print(error)

@router.post('/subscribe')
async def subscribe(data: subscription_schema.UserSubscriptionCreate):
    try:
        sub = await subscription_service.subscribe_user(data.user_id, data.plan_id)
        return sub.to_response()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/unsubscribe/{subscription_id}')
async def unsubscribe(subscription_id: str):
    updated = await subscription_service.unsubscribe(subscription_id)
    if not updated:
        raise HTTPException(status_code=404, detail='Subscription not found')
    return updated.to_response()


@router.get('/users/{user_id}/current')
async def get_current_plan(user_id: str):
    sub = await subscription_service.get_user_current_subscription(user_id)
    if not sub:
        return None
    plan = await subscription_service.get_plan(sub.plan_id)
    return plan.to_response() if plan else None
