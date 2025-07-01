from typing import Any, Dict, List

from bson import ObjectId

from app.models.table import TableModel
from app.models.table_session import TableSessionModel
from app.schema.table_session import TableSessionStatus, TableSessionDocument


table_model = TableModel()
session_model = TableSessionModel()


async def duplicate_active_sessions() -> List[Dict[str, Any]]:
    """Return tables that have more than one active session."""
    coll = TableSessionDocument.get_motor_collection()
    pipeline = [
        {
            "$match": {
                "status": {
                    "$in": [
                        TableSessionStatus.ACTIVE.value,
                        TableSessionStatus.NEED_BILL.value,
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$tableId",
                "count": {"$sum": 1},
                "sessions": {"$push": "$_id"},
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]
    docs = await coll.aggregate(pipeline).to_list(None)
    return [
        {
            "tableId": d["_id"],
            "sessionIds": [str(s) for s in d["sessions"]],
            "count": d["count"],
        }
        for d in docs
    ]


async def mismatched_current_sessions() -> List[Dict[str, Any]]:
    """Return tables whose currentSessionId does not match an active session."""
    tables = await table_model.get_all()
    mismatches: List[Dict[str, Any]] = []
    for t in tables:
        sessions = await TableSessionDocument.find(
            (
                (TableSessionDocument.table_id == str(t.id))
                & (
                    TableSessionDocument.status.in_(
                        [TableSessionStatus.ACTIVE, TableSessionStatus.NEED_BILL]
                    )
                )
            )
        ).to_list()
        active_ids = [str(s.id) for s in sessions]
        if t.current_session_id not in active_ids:
            mismatches.append(
                {
                    "tableId": str(t.id),
                    "restaurantId": t.restaurant_id,
                    "tableNumber": t.number,
                    "currentSessionId": t.current_session_id,
                    "activeSessionIds": active_ids,
                }
            )
    return mismatches


async def orphan_sessions() -> List[Dict[str, Any]]:
    """Return sessions that are not referenced by any table."""
    tables = await table_model.get_all()
    linked_ids = {t.current_session_id for t in tables if t.current_session_id}
    coll = TableSessionDocument.get_motor_collection()
    query: Dict[str, Any] = {}
    if linked_ids:
        object_ids = [ObjectId(sid) for sid in linked_ids]
        query = {"_id": {"$nin": object_ids}}
    docs = await coll.find(query).to_list(None)
    return [
        {
            "sessionId": str(d["_id"]),
            "tableId": d.get("tableId"),
            "status": d.get("status"),
        }
        for d in docs
    ]


async def run_all() -> Dict[str, Any]:
    return {
        "duplicateActiveSessions": await duplicate_active_sessions(),
        "currentSessionMismatches": await mismatched_current_sessions(),
        "orphanSessions": await orphan_sessions(),
    }
