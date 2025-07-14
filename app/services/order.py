import json
from datetime import datetime, timedelta

from beanie.operators import And, Eq, GTE, In
from fastapi import HTTPException

from app.models.order import OrderModel
from app.schema import order as order_schema
from app.schema.order import OrderDocument
from app.services import (
    table_session as table_session_service,
    table as table_service,
    recipe as recipe_service,
    stock_item as stock_item_service,
    restaurant as restaurant_service,
)
from app.services.websocket_manager import get_websocket_manger
from app.schema import recipe as recipe_schema
from app.utils.time import now_in_luanda

order_model = OrderModel()


async def place_order(data: dict) -> order_schema.OrderDocument:
    """Create a new order and attach it to the related table session.

    If the provided ``sessionId`` is missing or refers to a session that is not
    active, a new session is created and linked to the table automatically.
    """
    session_id = data.get("sessionId")
    restaurant_id = data.get("restaurantId")
    table_number = data.get("tableNumber")

    # Ensure there is an active session
    if not session_id and restaurant_id and table_number is not None:
        session = await table_session_service.get_active_session_for_restaurant_table(
            restaurant_id,
            table_number,
            create_if_missing=True,
        )
        if session:
            session_id = str(session.id)
            data["sessionId"] = session_id

    order = await order_model.create(data)

    if session_id:
        await table_session_service.add_order_to_session(session_id, str(order.id))

    try:
        websocket_manager = get_websocket_manger()
        json_data = json.dumps(order.to_response().model_dump(by_alias=True))
        await websocket_manager.broadcast(json_data, f"{str(restaurant_id)}/order")
    except Exception as error:
        print(str(error))
        # raise HTTPException(
        #     status_code=500,
        #     detail=str(error)
        # )

    # Adjust stock levels based on recipe if automatic adjustments are enabled
    if restaurant_id:
        restaurant = await restaurant_service.get_restaurant(restaurant_id)
        if (
            restaurant
            and restaurant.settings
            and restaurant.settings.automatic_stock_adjustments
        ):
            recipe = await recipe_service.get_recipe_by_menu_item(
                data.get("itemId"), restaurant_id
            )
            if recipe:
                ingredients_updated = False
                stock_cache = None
                for ingredient in recipe.ingredients:
                    stock_item = await stock_item_service.get_stock_item(
                        ingredient.product_id
                    )
                    if not stock_item:
                        if stock_cache is None:
                            stock_cache = await stock_item_service.list_stock_items_for_restaurant(
                                restaurant_id
                            )
                        match = next(
                            (
                                s
                                for s in stock_cache
                                if s.name.lower() == ingredient.product_name.lower()
                            ),
                            None,
                        )
                        if match:
                            ingredient.product_id = str(match.id)
                            stock_item = match
                            ingredients_updated = True
                    if stock_item:
                        await stock_item_service.remove_stock(
                            str(stock_item.id),
                            ingredient.quantity * order.quantity,
                            reason=f"Venda de {order.ordered_item_name}",
                        )

                if ingredients_updated:
                    await recipe_service.update_recipe(
                        str(recipe.id),
                        recipe_schema.RecipeUpdate(ingredients=recipe.ingredients),
                    )

    return order


async def place_orders(data_list: list[dict], session_id: str | None = None) -> list[order_schema.OrderDocument]:
    """Place multiple orders sequentially.

    If ``session_id`` is provided, it will be used for all orders unless an
    individual order already specifies a ``sessionId``.
    """
    orders: list[order_schema.OrderDocument] = []
    for data in data_list:
        payload = data.copy()
        if session_id and "sessionId" not in payload:
            payload["sessionId"] = session_id
        order = await place_order(payload)
        orders.append(order)
    return orders


async def get_order(order_id: str) -> order_schema.OrderDocument | None:
    return await order_model.get(order_id)


async def update_order_prep_status(order_id: str, status: order_schema.OrderPrepStatus) -> order_schema.OrderDocument | None:
    return await order_model.update(order_id, {"prepStatus": status})


async def mark_order_delivered(order_id: str) -> order_schema.OrderDocument | None:
    return await order_model.update(order_id, {"isDelivered": True})


async def cancel_order(order_id: str) -> order_schema.OrderDocument | None:
    return await order_model.update(order_id, {"prepStatus": "CANCELLED", "isDelivered": False})


async def list_orders_for_session(session_id: str) -> list[order_schema.OrderDocument]:
    filters = {"sessionId": session_id}
    return await order_model.get_by_fields(filters)


async def list_orders_by_prep_status(status: order_schema.OrderPrepStatus) -> list[order_schema.OrderDocument]:
    filters = {"prepStatus": status}
    return await order_model.get_by_fields(filters)


async def list_orders_for_restaurant(restaurant_id: str) -> list[order_schema.OrderDocument]:
    filters = {"restaurantId": restaurant_id}
    return await order_model.get_by_fields(filters)


async def list_recent_orders_for_restaurant(
    restaurant_id: str, hours: int = 24
) -> list[order_schema.OrderDocument]:
    """List orders placed within the last ``hours`` that belong to current table sessions."""

    cutoff = now_in_luanda() - timedelta(hours=hours)

    # Fetch all tables for the restaurant to determine their current sessions
    tables = await table_service.list_tables_for_restaurant(restaurant_id)
    session_ids = [t.current_session_id for t in tables if t.current_session_id]

    if not session_ids:
        return []

    return await OrderDocument.find(
        And(
            Eq(OrderDocument.restaurant_id, restaurant_id),
            In(OrderDocument.session_id, session_ids),
            GTE(OrderDocument.order_time, cutoff),
        )
    ).sort("-order_time").to_list()


async def update_order(order_id: str, data: order_schema.OrderUpdate) -> order_schema.OrderDocument | None:
    return await order_model.update(order_id, data.model_dump(exclude_none=True, by_alias=True))


async def delete_order(order_id: str) -> bool:
    return await order_model.delete(order_id)
