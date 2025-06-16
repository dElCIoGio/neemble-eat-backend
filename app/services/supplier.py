from typing import List, Optional

from app.models.supplier import SupplierModel
from app.schema import supplier as supplier_schema

supplier_model = SupplierModel()


async def create_supplier(data: supplier_schema.SupplierCreate) -> supplier_schema.SupplierDocument:
    payload = data.model_dump(by_alias=True)
    return await supplier_model.create(payload)


async def get_supplier(supplier_id: str) -> Optional[supplier_schema.SupplierDocument]:
    return await supplier_model.get(supplier_id)


async def list_suppliers_for_restaurant(restaurant_id: str) -> List[supplier_schema.SupplierDocument]:
    return await supplier_model.get_by_fields({"restaurantId": restaurant_id})


async def update_supplier(supplier_id: str, data: supplier_schema.SupplierUpdate) -> Optional[supplier_schema.SupplierDocument]:
    return await supplier_model.update(supplier_id, data.model_dump(exclude_none=True, by_alias=True))


async def delete_supplier(supplier_id: str) -> bool:
    return await supplier_model.delete(supplier_id)
