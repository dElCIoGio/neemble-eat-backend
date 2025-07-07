# Backend Endpoints for Stock Page

This document outlines the backend/database interactions required to make the page functional. The page manages stock items,
movements, recipes, sales and suppliers. Below is a summary of the required API
endpoints and the data shapes used.

## Stock Items

### List stock items
- **GET /api/v1/stock/restaurant/{restaurant_id}** – Returns an array of `StockItem` for a restaurant.

- **POST /api/v1/stock/restaurant/{restaurant_id}** – Expects `StockItemCreate`. Returns created
  `StockItem`.

### Retrieve single item
- **GET /api/v1/stock/{id}** – Returns the `StockItem` with given `id`.

- **PUT /api/v1/stock/{id}** – Accepts partial `StockItem` with fields to update.
  Returns the updated `StockItem`.

- **DELETE /api/v1/stock/{id}** – Deletes the stock item. Should also remove
  related `Movement` records if needed.

- **POST /api/v1/stock/{id}/add** – Body: `{ quantity: number, reason?: string }`.
  Creates a new `Movement` of type `entrada` and updates the item's
  `currentQuantity` and `lastEntry`.

- **POST /api/v1/stock/{id}/remove** – Body: `{ quantity: number, reason?: string }`.
  Adds a `Movement` of type `saída` or `ajuste` and updates the quantity.

## Movements

-### List movements
- **GET /api/v1/movements/restaurant/{restaurant_id}** – Returns array of `Movement` ordered by date
  descending for a specific restaurant. Supports filtering by product or date range.

-### Create movement
- **POST /api/v1/movements/restaurant/{restaurant_id}** – Create a movement record (for situations where the
  movement does not originate from another endpoint).

## Recipes

### List recipes
- **GET /api/v1/recipes/:restaurant_id** – Returns array of `Recipe` for a specific restaurant.

### Create recipe
- **POST /api/v1/recipes/:restaurant_id** – Body: `Recipe` without `id`. Should validate that all
  referenced products exist.

### Update recipe
- **PUT /api/v1/recipes/:id** – Update an existing recipe.

### Delete recipe
- **DELETE /api/v1/recipes/:id** – Remove recipe. Optionally disallow deletion when
  sales reference the recipe.

## Sales

### List sales
- **GET /api/v1/sales** – Returns array of `Sale`.
- **GET /api/v1/sales/restaurant/{restaurant_id}/day/{date}** – Returns all sales for a restaurant on a specific day. The `date` should be in `YYYY-MM-DD` format.

### Register sale
- **POST /api/v1/sales/restaurant/{restaurant_id}** – Body: `{ recipeId: string, quantity: number }`.
  Decrements stock for each ingredient, adds a `Movement` record for each item
  and creates a `Sale` entry.

## Suppliers

### List suppliers
- **GET /api/v1/suppliers/restaurant/{restaurant_id}** – Returns array of `Supplier`.

### Create supplier
- **POST /api/v1/suppliers** – Body: `Supplier` without `id`.

### Update supplier
- **PUT /api/v1/suppliers/:id** – Update supplier information and list of supplied
  products.

### Delete supplier
- **DELETE /api/v1/suppliers/:id** – Remove supplier.

## Categories

Although categories are simple strings on the page, an endpoint may be useful
for managing them:
- **GET /api/v1/stock/categories** – List distinct category names.
- **DELETE /api/v1/stock/categories/{name}** – Remove a category (all items with such category name).
g
## Stats and Reports

The page displays statistics such as total products, items with low stock,
critical items and total inventory value. These can be computed client‑side from
the `/api/v1/stock` response, but for efficiency the backend may expose:
- **GET /api/v1/stock/stats?restaurant_id={id}** – Returns totals, e.g. `{ totalItems, lowStock,
  criticalStock, totalValue }`.

## Purchase Orders and Auto Reorder

Comments in the page suggest generating purchase orders and automatic
replenishment. For that the backend could provide:
- **GET /api/v1/stock/auto-reorder?restaurant_id={id}** – Returns items where `autoReorder` is true and
  `currentQuantity <= reorderPoint` along with suggested quantities.
  Purchase order creation is not implemented yet.

