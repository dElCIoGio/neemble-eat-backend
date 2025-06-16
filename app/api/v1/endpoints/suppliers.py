from fastapi import APIRouter, HTTPException

from app.schema import supplier as supplier_schema
from app.services import supplier as supplier_service

router = APIRouter()


@router.get("/restaurant/{restaurant_id}")
async def list_suppliers(restaurant_id: str):
    suppliers = await supplier_service.list_suppliers_for_restaurant(restaurant_id)
    return [s.to_response() for s in suppliers]


@router.post("/")
async def create_supplier(data: supplier_schema.SupplierCreate):
    supplier = await supplier_service.create_supplier(data)
    return supplier.to_response()


@router.put("/{supplier_id}")
async def update_supplier(supplier_id: str, data: supplier_schema.SupplierUpdate):
    updated = await supplier_service.update_supplier(supplier_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return updated.to_response()


@router.delete("/{supplier_id}")
async def delete_supplier(supplier_id: str):
    deleted = await supplier_service.delete_supplier(supplier_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return True
