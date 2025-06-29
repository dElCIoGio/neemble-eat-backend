import json
from typing import Dict, Optional, Any

from fastapi import APIRouter, HTTPException, Query
from app.services import table_session as session_service
from app.services.table_session import session_model

router = APIRouter()


@router.get("/paginate")
async def paginate_sessions(
    limit: int = Query(10, gt=0),
    cursor: Optional[str] = Query(None),
):
    try:
        filters: Dict[str, Any] = {}
        result = await session_model.paginate(
            filters=filters, limit=limit, cursor=cursor
        )
        return result
    except Exception as error:
        print(error)


@router.get("/active/{restaurant_id}/{table_number}")
async def get_active_session_by_number(restaurant_id: str, table_number: str):
    session = await session_service.get_active_session_for_restaurant_table(
        restaurant_id, int(table_number)
    )
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")
    return session.to_response()


@router.get("/active/{table_id}")
async def get_active_session(table_id: str):
    session = await session_service.get_active_session_for_table(table_id)
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")
    return session.to_response()


@router.get("/table/{table_id}")
async def list_sessions(table_id: str):
    sessions = await session_service.list_sessions_for_table(table_id)
    return [s.to_response() for s in sessions]


@router.get("/restaurant/{restaurant_id}/active")
async def list_active_sessions(restaurant_id: str):
    sessions = await session_service.list_active_sessions_for_restaurant(restaurant_id)
    return [s.to_response() for s in sessions]


@router.post("/{session_id}/close")
async def close_session(session_id: str):
    try:
        new_session = await session_service.close_table_session(session_id)

        return new_session.to_response()
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/{session_id}/cancel")
async def cancel_session(session_id: str):
    try:
        session = await session_service.close_table_session(session_id, cancelled=True)
        return session.to_response()
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/{session_id}/pay")
async def pay_session(session_id: str):
    session = await session_service.mark_session_paid(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_response()


@router.post("/{session_id}/needs-bill")
async def mark_session_needs_bill_endpoint(session_id: str):
    try:
        session = await session_service.mark_session_needs_bill(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session.to_response()
    except Exception as error:
        print(str(error))
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/{session_id}/cancel-checkout")
async def cancel_session_checkout_endpoint(session_id: str):
    try:
        session = await session_service.cancel_session_checkout(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session.to_response()
    except Exception as error:
        print(str(error))
        raise HTTPException(status_code=500, detail=str(error))
