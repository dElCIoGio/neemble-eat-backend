# Restaurants Module - Test Cases and Requirements

This document lists basic requirements and test cases for the restaurants module. FastAPI endpoints live in `app/api/v1/endpoints/restaurants.py` with supporting logic in `app/services/restaurant.py`.

## Basic Requirements

1. **Current Menu Retrieval**
   - Retrieve the restaurant's current menu by restaurant ID.
   - Changing the current menu must validate that the menu belongs to the restaurant.
2. **Item Listing by Slug**
   - Given a restaurant slug, return all items in its current menu.
   - If the slug does not exist, the endpoint should return HTTP 404.
   - If the restaurant has no current menu, an empty list should be returned.
3. **Opening Hours Update**
   - Restaurants should be able to update their opening hours through a
     dedicated endpoint.
   - The endpoint accepts the ``OpeningHours`` schema and returns the updated
     restaurant document.
4. **Automatic Stock Adjustments**
   - Restaurants can toggle automatic stock adjustments using a dedicated
     endpoint.
   - The endpoint accepts a boolean ``automaticStockAdjustments`` and returns
     the updated restaurant document.

These scenarios can be automated with a testing framework such as `pytest` and FastAPI's test client.

