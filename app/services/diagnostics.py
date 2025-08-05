from http.client import HTTPException
from idlelib.run import manage_socket
from typing import Any, Dict, List

from bson import ObjectId

from app.models.table import TableModel
from app.models.table_session import TableSessionModel
from app.schema.table_session import TableSessionStatus, TableSessionDocument
from app.models.item import ItemModel
from app.models.restaurant import RestaurantModel
from app.utils.images import RESTAURANT_BANNER, RESTAURANT_LOGO
from app.services.google_bucket import get_google_bucket_manager


table_model = TableModel()
session_model = TableSessionModel()
item_model = ItemModel()
restaurant_model = RestaurantModel()


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
        filter = {
            "$and": [
                {
                    "tableId": str(t.id)
                }, {
                    "status": {"$in": [TableSessionStatus.ACTIVE, TableSessionStatus.NEED_BILL]}
                }
            ]
        }
        sessions = await session_model.get_by_fields(filter)

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


async def cleanup_unlinked_images() -> List[str]:
    """Delete images in cloud storage not linked to any item or restaurant."""
    manager = get_google_bucket_manager()
    deleted: List[str] = []
    images = manager.list_images(folder="neemble-eat-storage")

    # Iterate over all uploaded images
    for blob in manager.client.list_blobs(manager.bucket, prefix="uploads/"):
        blob.reload()
        metadata = blob.metadata or {}

        item_id = metadata.get("item_id")
        restaurant_id = metadata.get("restaurant_id")
        image_type = metadata.get("image_type")
        blob_url = f"https://storage.googleapis.com/{manager.bucket.name}/{blob.name}"

        unlink = False

        if item_id:
            item = await item_model.get(item_id)
            if not item or item.image_url != blob_url:
                unlink = True
        elif restaurant_id:
            restaurant = await restaurant_model.get(restaurant_id)
            expected_url = None
            if restaurant:
                if image_type == RESTAURANT_BANNER:
                    expected_url = restaurant.banner_url
                elif image_type == RESTAURANT_LOGO:
                    expected_url = restaurant.logo_url
            if not restaurant or expected_url != blob_url:
                unlink = True
        else:
            unlink = True

        if unlink:
            if manager.delete_image(blob.name):
                deleted.append(blob.name)

    return deleted


async def run_all() -> Dict[str, Any]:

    r1 = await duplicate_active_sessions()

    try:
        r2 = await mismatched_current_sessions()
        r3 = await orphan_sessions()
        return {
            "duplicateActiveSessions": r1,
            "currentSessionMismatches": r2,
            "orphanSessions": r3,
        }
    except Exception as error:
        print(str(error))
        raise str(error)
