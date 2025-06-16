# Categories Module - Test Cases and Requirements

This document describes the basic requirements and a comprehensive list of test cases for the categories module. The API endpoints are implemented in `app/api/v1/endpoints/categories.py` and helper logic lives in `app/services/category.py`.

## Basic Requirements

1. **Category CRUD**
   - Create a category with required fields `name`, `restaurantId` and `menuId`.
   - Retrieve, update and delete categories by ID.
   - Slugs should be generated automatically and be unique.
2. **Availability Management**
   - Toggle a category's `isActive` flag via the dedicated endpoint.
3. **Item Association**
   - Add or remove items from a category and list items belonging to a category.
4. **Listing Functions**
   - Provide listings of categories for a menu or restaurant and lookup by slug.
5. **Error Handling**
   - Invalid IDs or slugs should return HTTP 404 or 400 as appropriate without exposing internals.

## Test Cases

### 1. Create Category Endpoint `/api/v1/categories/`
- **TC1.1** Valid payload creates the category and returns it with a unique slug.
- **TC1.2** Missing required fields results in HTTP 400 validation error.
- **TC1.3** Creating two categories with the same name generates different slugs.
- **TC1.4** Invalid menu or restaurant IDs return HTTP 400.

### 2. Get Category Endpoint `/api/v1/categories/{category_id}`
- **TC2.1** Existing ID returns the corresponding category.
- **TC2.2** Non‑existent or malformed ID returns HTTP 404.

### 3. Update Category Endpoint `/api/v1/categories/{category_id}`
- **TC3.1** Valid update modifies the category and returns updated values.
- **TC3.2** Updating a non‑existent ID returns HTTP 404.
- **TC3.3** Invalid fields or types return HTTP 400.

### 4. Delete Category Endpoint `/api/v1/categories/{category_id}`
- **TC4.1** Valid ID deletes the category and returns `True`.
- **TC4.2** Non‑existent ID returns HTTP 404.

### 5. Switch Availability `/api/v1/categories/availability/{category_id}`
- **TC5.1** Toggling an existing category switches the `isActive` value.
- **TC5.2** Invalid category ID returns HTTP 404.

### 6. List Category Items `/api/v1/categories/{category_id}/items`
- **TC6.1** Returns only active items belonging to the category.
- **TC6.2** Inactive category returns an empty list.
- **TC6.3** Invalid category ID returns HTTP 404.

### 7. List Category Items by Slug `/api/v1/categories/{category_slug}/slug/items`
- **TC7.1** Valid slug returns items for the category.
- **TC7.2** Unknown slug returns HTTP 400.
- **TC7.3** Inactive category slug results in an empty list.

### 8. Add Item to Category `/api/v1/categories/{category_id}/items/{item_id}`
- **TC8.1** Valid IDs append the item ID to the category if not already present.
- **TC8.2** Non‑existent category returns HTTP 404.
- **TC8.3** Adding a duplicate item does not create a duplicate entry.

### 9. Remove Item from Category `/api/v1/categories/{category_id}/items/{item_id}`
- **TC9.1** Valid IDs remove the item ID from the category.
- **TC9.2** Non‑existent category returns HTTP 404.
- **TC9.3** Removing an item not present leaves the list unchanged.

### 10. List Categories for Menu `/api/v1/categories/menu/{menu_id}`
- **TC10.1** Valid menu ID returns all categories for that menu.
- **TC10.2** Menu with no categories returns an empty list.

### 11. List Categories by Menu Slug `/api/v1/categories/menu/slug/{menu_slug}`
- **TC11.1** Existing slug returns categories for the menu.
- **TC11.2** Unknown slug returns HTTP 400 "The menu was not found".

### 12. List Categories for Restaurant `/api/v1/categories/restaurant/{restaurant_id}`
- **TC12.1** Valid ID returns categories for that restaurant.
- **TC12.2** Restaurant with no categories returns an empty list.

### 13. Get Category by Slug `/api/v1/categories/slug/{slug}`
- **TC13.1** Valid slug returns the category.
- **TC13.2** Unknown slug returns HTTP 404.

### 14. General Edge Cases
- **TC14.1** Slug generation should handle special characters and produce URL-safe slugs.
- **TC14.2** Stress test with a large number of categories to validate listing performance.
- **TC14.3** Endpoints are public; verify they work without authentication headers.

These test cases cover common and edge scenarios for the categories workflow and can be implemented using a framework such as `pytest` together with an HTTP client for requests.

