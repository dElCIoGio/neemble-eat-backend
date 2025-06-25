from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any

from app.models.table import TableModel
from app.schema import table as table_schema
from app.services import table as table_service
from app.utils.auth import admin_required

router = APIRouter()
table_model = TableModel()


@router.get("/paginate")
async def paginate_tables(
    limit: int = Query(10, gt=0),
    cursor: Optional[str] = Query(None),
):
    try:
        filters: Dict[str, Any] = {}

        result = await table_model.paginate(filters=filters, limit=limit, cursor=cursor)

        orders = result.items

        return result
    except Exception as error:
        print(error)

@router.post("/")
async def create_table(data: table_schema.TableCreate):
    try:
        table = await table_service.create_table(data)
        return table.to_response()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/{table_id}")
async def get_table(table_id: str):
    table = await table_service.get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    return table.to_response()


@router.get("/restaurant/{restaurant_id}")
async def list_tables(restaurant_id: str):
    tables = await table_service.list_tables_for_restaurant(restaurant_id)

    print(tables)
    print(len(tables))
    return [t.to_response() for t in tables]


@router.put("/{table_id}")
async def update_table(table_id: str, data: table_schema.TableUpdate):
    updated = await table_service.update_table(table_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Table not found")
    return updated.to_response()


@router.delete("/{table_id}")
async def delete_table(table_id: str):
    result = await table_service.delete_table(table_id)
    if not result:
        raise HTTPException(status_code=404, detail="Table not found")
    return True


@router.put("/{table_id}/status")
async def update_table_status(table_id: str, is_active: bool):
    table = await table_service.update_table_status(table_id, is_active)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    return table.to_response()


@router.put("/{table_id}/session")
async def update_table_session(table_id: str, session_id: Optional[str] = None):
    table = await table_service.update_table_session(table_id, session_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    return table.to_response()


@router.post("/reset", dependencies=[Depends(admin_required)])
async def reset_all_tables_endpoint():
    tables = await table_service.reset_all_tables()
    return [t.to_response() for t in tables]


@router.post("/restaurant/{restaurant_id}/reset", dependencies=[Depends(admin_required)])
async def reset_restaurant_tables_endpoint(restaurant_id: str):
    tables = await table_service.reset_tables_for_restaurant(restaurant_id)
    return [t.to_response() for t in tables]


@router.post("/{table_id}/reset", dependencies=[Depends(admin_required)])
async def reset_single_table_endpoint(table_id: str):
    table = await table_service.reset_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    return table.to_response()
