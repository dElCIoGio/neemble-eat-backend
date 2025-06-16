from typing import List, Optional

from app.models.recipe import RecipeModel
from app.schema import recipe as recipe_schema

recipe_model = RecipeModel()


async def create_recipe(data: recipe_schema.RecipeCreate) -> recipe_schema.RecipeDocument:
    payload = data.model_dump(by_alias=True)
    return await recipe_model.create(payload)


async def get_recipe(recipe_id: str) -> Optional[recipe_schema.RecipeDocument]:
    return await recipe_model.get(recipe_id)


async def list_recipes_for_restaurant(restaurant_id: str) -> List[recipe_schema.RecipeDocument]:
    return await recipe_model.get_by_fields({"restaurantId": restaurant_id})


async def update_recipe(recipe_id: str, data: recipe_schema.RecipeUpdate) -> Optional[recipe_schema.RecipeDocument]:
    return await recipe_model.update(recipe_id, data.model_dump(exclude_none=True, by_alias=True))


async def delete_recipe(recipe_id: str) -> bool:
    return await recipe_model.delete(recipe_id)
