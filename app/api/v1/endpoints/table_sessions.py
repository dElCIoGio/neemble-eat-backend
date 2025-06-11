from fastapi import APIRouter, HTTPException
from app.services import table_session as session_service
from app.schema.table_session import TableSession, TableSessionStatus

router = APIRouter()

@router.get("/active/{restaurant_id}/{table_number}")
async def get_active_session_by_number(restaurant_id: str, table_number: int):
    session = await session_service.get_active_session_for_restaurant_table(restaurant_id, table_number)
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

@router.post("/{session_id}/close")
async def close_session(session_id: str):
    try:
        session = await session_service.close_table_session(session_id)
        return session.to_response()
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.post("/{session_id}/cancel")
async def cancel_session(session_id: str):
    try:
        session = await session_service.close_table_session(session_id, cancelled=True)
        return session.to_response()
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
