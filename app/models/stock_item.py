from typing import Dict, Any, Optional

from app.db.crud import MongoCrud
from app.schema import stock_item as stock_item_schema
from app.schema.stock_item import StockStatus
from app.schema import movement as movement_schema
from app.models.movement import MovementModel
from app.utils.time import now_in_luanda

movement_model = MovementModel()


class StockItemModel(MongoCrud[stock_item_schema.StockItemDocument]):
    def __init__(self):
        super().__init__(stock_item_schema.StockItemDocument)

    def _calculate_status(self, quantity: float, min_quantity: float) -> StockStatus:
        if quantity == 0:
            return StockStatus.OUTOFSTOCK
        if quantity <= min_quantity * 0.25:
            return StockStatus.CRITICO
        if quantity <= min_quantity:
            return StockStatus.BAIXO
        return StockStatus.OK

    async def create(self, data: Dict[str, Any], *, user: str = "Ajuste Automático", reason: str = "") -> stock_item_schema.StockItemDocument:
        quantity = data.get("currentQuantity", 0)
        min_q = data.get("minQuantity", 1)
        data["status"] = self._calculate_status(quantity, min_q)
        new_stock_item = await super().create(data)

        if quantity > 0:
            await movement_model.create({
                "productId": str(new_stock_item.id),
                "productName": new_stock_item.name,
                "type": movement_schema.MovementType.ENTRADA,
                "quantity": quantity,
                "restaurantId": new_stock_item.restaurant_id,
                "unit": new_stock_item.unit,
                "date": now_in_luanda(),
                "reason": reason or "Item created",
                "user": "Ajuste automático",
                "cost": new_stock_item.cost,
            })

        return new_stock_item

    async def update(self, _id: str, data: Dict[str, Any], *, user: str = "Ajuste Automático", reason: str = "") -> Optional[stock_item_schema.StockItemDocument]:
        item = await self.get(_id)
        if not item:
            return None

        new_quantity = data.get("currentQuantity", item.current_quantity)
        min_q = data.get("minQuantity", item.min_quantity)
        data["status"] = self._calculate_status(new_quantity, min_q)
        updated = await super().update(_id, data)

        if updated and new_quantity != item.current_quantity:
            await movement_model.create({
                "productId": str(item.id),
                "productName": item.name,
                "type": movement_schema.MovementType.ENTRADA if new_quantity > item.current_quantity else movement_schema.MovementType.SAIDA,
                "quantity": abs(new_quantity - item.current_quantity),
                "restaurantId": item.restaurant_id,
                "unit": item.unit,
                "date": now_in_luanda(),
                "reason": reason,
                "user": "Ajuste automático",
                "cost": item.cost,
            })

        return updated

    async def delete(self, _id: str, *, user: str = "Ajuste Automático", reason: str = "") -> bool:
        item = await self.get(_id)
        if not item:
            return False

        deleted = await super().delete(_id)

        if deleted and item.current_quantity > 0:
            await movement_model.create({
                "productId": str(item.id),
                "productName": item.name,
                "type": movement_schema.MovementType.SAIDA,
                "quantity": item.current_quantity,
                "restaurantId": item.restaurant_id,
                "unit": item.unit,
                "date": now_in_luanda(),
                "reason": reason or "Item deleted",
                "user": "Ajuste automático",
                "cost": item.cost,
            })

        return deleted





