from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query

from app.services import subscription as subscription_service
from app.schema import subscription_plan as plan_schema
from app.services.subscription import plan_model
from app.utils.auth import admin_required

router = APIRouter()


@router.get("/paginate")
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


@router.post("/", dependencies=[Depends(admin_required)])
async def create_plan(data: plan_schema.SubscriptionPlanCreate):
    try:
        plan = await subscription_service.create_plan(data)
        return plan.to_response()
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{plan_id}", dependencies=[Depends(admin_required)])
async def update_plan(plan_id: str, data: plan_schema.SubscriptionPlanUpdate):
    updated = await subscription_service.update_plan(plan_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Plan not found")
    return updated.to_response()


@router.delete("/{plan_id}", dependencies=[Depends(admin_required)])
async def delete_plan(plan_id: str):
    deleted = await subscription_service.delete_plan(plan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Plan not found")
    return True


@router.get("/{plan_id}")
async def get_plan(plan_id: str):
    plan = await subscription_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan.to_response()


@router.get("/")
async def list_available_plans():
    plans = await subscription_service.list_plans(active_only=True)
    return [p.to_response() for p in plans]


@router.get("/all")
async def list_all_plans():
    plans = await subscription_service.list_plans()
    return [p.to_response() for p in plans]
