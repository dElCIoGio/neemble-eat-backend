# Menus Module - Test Cases

This file lists scenarios for menu related endpoints located in `app/api/v1/endpoints/menus.py`.

## Activation Endpoint `/api/v1/menus/{menu_id}/activate`
- **TC1.1** Valid menu ID sets `isActive` to `true` and returns the updated menu.
- **TC1.2** Unknown menu ID returns HTTP 404 "Menu not found".
