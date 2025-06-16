from typing import List, Optional

from app.models.sale import SaleModel
from app.schema import sale as sale_schema
from app.schema import recipe as recipe_schema
from app.services import stock_item as stock_service
from app.models.recipe import RecipeModel
from app.utils.time import now_in_luanda

sale_model = SaleModel()
recipe_model = RecipeModel()


async def create_sale(recipe_id: str, quantity: int) -> Optional[sale_schema.SaleDocument]:
    recipe = await recipe_model.get(recipe_id)
    if not recipe:
        return None

    total = recipe.cost * quantity
    sale_data = sale_schema.SaleCreate(
        dishName=recipe.dish_name,
        quantity=quantity,
        date=now_in_luanda().isoformat(),
        restaurantId=recipe.restaurant_id,
        total=total,
    )
    sale = await sale_model.create(sale_data.model_dump(by_alias=True))

    for ingredient in recipe.ingredients:
        await stock_service.remove_stock(
            ingredient.product_id,
            ingredient.quantity * quantity,
            reason=f"Sale of {recipe.dish_name}",
            user="system",
        )
    return sale


async def list_sales() -> List[sale_schema.SaleDocument]:
    return await sale_model.get_all()
