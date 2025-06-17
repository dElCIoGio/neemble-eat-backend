from typing import Dict, Any, Optional
from app.db.crud import MongoCrud
from app.schema import stock_item as stock_item_schema
from app.schema.stock_item import StockStatus


class StockItemModel(MongoCrud[stock_item_schema.StockItemDocument]):
    def __init__(self):
        super().__init__(stock_item_schema.StockItemDocument)


    async def update(self, _id: str, data: Dict[str, Any]) -> Optional[stock_item_schema.StockItemDocument]:

        item_status = self._get_updated_status(data)

        data["status"] = item_status

        return await super().update(_id, data)


    def _get_updated_status(self, data: Dict[str, Any]):

        q = data.get("currentQuantity", 0)
        min_q = data.get("minQuantity", 1)

        if q == 0:
            return StockStatus.OUTOFSTOCK
        elif q <= min_q * 0.25:
            return StockStatus.CRITICO
        elif q <= min_q:
            return StockStatus.BAIXO
        else:
            return StockStatus.OK


    async def create(self, data: Dict[str, Any]):

        item_status = self._get_updated_status(data)
        data["status"] = item_status
        new_stock_item = await super().create(data)

        return new_stock_item





