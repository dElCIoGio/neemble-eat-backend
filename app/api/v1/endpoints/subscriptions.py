from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from pydantic import BaseModel, Field

from app.services import subscription as subscription_service
from app.schema import user_subscription as subscription_schema
from app.services.subscription import subscription_model
from app.utils.auth import get_current_user

router = APIRouter()


class ChangePlanRequest(BaseModel):
    plan_id: str = Field(..., alias="planId")
    reason: Optional[str] = None


# User Subscription Endpoints

@router.get("/paginate")
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


@router.post('/change-plan')
async def change_plan(
    req: ChangePlanRequest,
    uid: str = Depends(get_current_user),
):
    sub = await subscription_service.get_user_current_subscription(uid)
    if not sub:
        raise HTTPException(status_code=404, detail='Subscription not found')
    updated = await subscription_service.change_plan(str(sub.id), req.plan_id, req.reason)
    if not updated:
        raise HTTPException(status_code=404, detail='Plan not found')
    return updated.to_response()


@router.get('/users/{user_id}/current')
async def get_current_plan(user_id: str):
    sub = await subscription_service.get_user_current_subscription(user_id)
    if not sub:
        return None
    plan = await subscription_service.get_plan(sub.plan_id)
    return plan.to_response() if plan else None


@router.get('/current')
async def get_my_subscription(uid: str = Depends(get_current_user)):
    sub = await subscription_service.get_user_current_subscription(uid)
    if not sub:
        return None
    plan = await subscription_service.get_plan(sub.plan_id) if sub.plan_id else None
    return {
        "plan": plan.to_response() if plan else None,
        "billingCycle": plan.interval if plan else None,
        "autoRenew": sub.auto_renew,
        "features": plan.features if plan else [],
    }


@router.get('/usage')
async def get_usage(uid: str = Depends(get_current_user)):
    return await subscription_service.get_usage_metrics(uid)


@router.post('/{subscription_id}/pause')
async def pause_subscription(subscription_id: str):
    updated = await subscription_service.pause_subscription(subscription_id)
    if not updated:
        raise HTTPException(status_code=404, detail='Subscription not found')
    return updated.to_response()


@router.post('/{subscription_id}/resume')
async def resume_subscription(subscription_id: str):
    updated = await subscription_service.resume_subscription(subscription_id)
    if not updated:
        raise HTTPException(status_code=404, detail='Subscription not found')
    return updated.to_response()


@router.get('/backup')
async def backup_account_data_endpoint(uid: str = Depends(get_current_user)):
    blob = await subscription_service.backup_account_data(uid)
    return Response(content=blob, media_type='application/octet-stream')
