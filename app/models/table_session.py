from typing import Dict, Any, Optional
import json

from app.db.crud import MongoCrud
from app.schema import table_session as table_session_schema
from app.services.websocket_manager import get_websocket_manger


class TableSessionModel(MongoCrud[table_session_schema.TableSessionDocument]):
    def __init__(self):
        super().__init__(table_session_schema.TableSessionDocument)

    async def update(self, _id: str, data: Dict[str, Any]) -> Optional[table_session_schema.TableSessionDocument]:
        updated = await super().update(_id, data)
        if updated and ("orders" in data or "status" in data):
            websocket_manager = get_websocket_manger()
            session_data = json.dumps(updated.to_response().model_dump())
            await websocket_manager.broadcast(session_data, f"{updated.restaurant_id}/session-status")
        return updated
