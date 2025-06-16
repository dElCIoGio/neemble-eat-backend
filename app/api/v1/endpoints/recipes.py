from fastapi import APIRouter, HTTPException

from app.schema import recipe as recipe_schema
from app.services import recipe as recipe_service

router = APIRouter()


@router.get("/restaurant/{restaurant_id}")
async def list_recipes(restaurant_id: str):
    try:
        recipes = await recipe_service.list_recipes_for_restaurant(restaurant_id)
        return [r.to_response() for r in recipes]
    except Exception as error:
        print(error)


@router.post("/restaurant/{restaurant_id}")
async def create_recipe(restaurant_id: str, data: recipe_schema.RecipeCreate):
    if data.restaurant_id != restaurant_id:
        raise HTTPException(status_code=400, detail="Mismatched restaurant id")
    recipe = await recipe_service.create_recipe(data)
    return recipe.to_response()


@router.put("/{recipe_id}")
async def update_recipe(recipe_id: str, data: recipe_schema.RecipeUpdate):
    updated = await recipe_service.update_recipe(recipe_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return updated.to_response()


@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: str):
    deleted = await recipe_service.delete_recipe(recipe_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return True
