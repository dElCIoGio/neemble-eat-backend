from typing import Dict, Any, Optional
from app.db.crud import MongoCrud
from app.schema import stock_item as stock_item_schema
from app.schema.stock_item import StockStatus


class StockItemModel(MongoCrud[stock_item_schema.StockItemDocument]):
    def __init__(self):
        super().__init__(stock_item_schema.StockItemDocument)


    async def update(self, _id: str, data: Dict[str, Any]) -> Optional[stock_item_schema.StockItemDocument]:

        item_status = await self._get_updated_status(_id)

        data["status"] = item_status

        return await super().update(_id, data)


    async def _get_updated_status(self, _id: str):
        stock_item = await self.get(_id)

        q = stock_item.current_quantity
        min_q = stock_item.min_quantity

        if q == 0:
            return StockStatus.OUTOFSTOCK
        elif q <= min_q * 0.25:
            return StockStatus.CRITICO
        elif q <= min_q:
            return StockStatus.BAIXO
        else:
            return StockStatus.OK


    async def create(self, data: Dict[str, Any]):

        _id = data["_id"]
        item_status = await self._get_updated_status(_id)

        data["status"] = item_status

        return await super().create(data)





