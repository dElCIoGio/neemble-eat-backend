from app.models.table_session import TableSessionModel
from datetime import datetime

session_model = TableSessionModel()

async def start_session(data: dict):
    return await session_model.create(data)

async def get_active_session_for_table(table_id: str):
    filters = {
        "tableId": table_id,
        "status": "active"
    }
    sessions = await session_model.get_by_fields(filters, limit=1)

    if sessions:
        return sessions[0]
    return None

async def close_session(session_id: str):
    session = await session_model.get(session_id)
    if not session:
        raise Exception("Session not found")

    if session.status != "active":
        raise Exception("Session is not active")

    session_data = {
        "status": "closed",
        "endTime": datetime.now()
    }
    await session_model.update(session_id, session_data)

    return session

async def list_sessions_for_table(table_id: str):
    filters = {"tableId": table_id}
    return await session_model.get_by_fields(filters)
