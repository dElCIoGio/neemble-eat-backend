import os
from typing import List, Optional, Dict, Any

from fastapi import (
    APIRouter,
    Depends,
    Form,
    UploadFile,
    File,
    Request,
    HTTPException,
    Query,
)
from pymongo.errors import DuplicateKeyError

from app.schema.restaurant import OpeningHours, RestaurantDocument
from app.schema.user import UserRestaurantMembership, UserDocument
from app.services.restaurant import (
    create_restaurant,
    deactivate_restaurant,
    get_restaurant,
    get_by_slug,
    update_restaurant,
    delete_restaurant,
    get_restaurants,
    get_active_restaurants,
    restaurant_model,
    change_current_menu,
    get_current_menu,
    list_current_menu_items_by_slug,
)
from app.schema import restaurant as restaurant_schema
from app.services.roles import create_default_roles_for_restaurant
from app.models.role import RoleModel
from app.utils.auth import (
    get_current_user,  # returns the logged user without checking if they are admin
    admin_required,  # returns the logged user and checks if they are admin
)
from app.utils.restaurant import parse_opening_hours
from app.utils.images import (
    save_restaurant_image,
    RESTAURANT_BANNER,
    RESTAURANT_LOGO,
    validate_image_dimensions,
    rename_restaurant_image,
    cleanup_restaurant_images,
    delete_restaurant_image,
    _blob_name_from_url,
)
from app.models.user import UserModel
from app.utils.slug import generate_unique_slug

router = APIRouter()

role_model = RoleModel()
user_model = UserModel()


@router.get("/paginate")
async def paginate_orders(
    limit: int = Query(10, gt=0),
    cursor: Optional[str] = Query(None),
):
    try:
        filters: Dict[str, Any] = {}

        result = await restaurant_model.paginate(
            filters=filters, limit=limit, cursor=cursor
        )

        return result
    except Exception as error:
        print(error)


@router.post("/")
async def create(
    request: Request,
    name: str = Form(...),
    address: str = Form(...),
    description: str = Form(...),
    phone_number: str = Form(...),
    banner_file: UploadFile = File(...),
    logo_file: Optional[UploadFile] = File(None),
    firebase_uid: str = Depends(get_current_user),
):
    try:
        # Parse openingHours from form data
        form = await request.form()
        opening_hours = parse_opening_hours(form)

        opening_hours = OpeningHours(
            monday=opening_hours["monday"],
            tuesday=opening_hours["tuesday"],
            wednesday=opening_hours["wednesday"],
            thursday=opening_hours["thursday"],
            friday=opening_hours["friday"],
            saturday=opening_hours["saturday"],
            sunday=opening_hours["sunday"],
        )

        # Create restaurant settings with opening hours
        settings = restaurant_schema.RestaurantSettings(openingHours=opening_hours)

        # Save banner image
        banner_content = await banner_file.read()
        is_valid, error_msg = validate_image_dimensions(
            banner_content, RESTAURANT_BANNER
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        banner_file.file.seek(0)  # Reset file pointer after reading
        banner_result = await save_restaurant_image(
            image=banner_file,
            restaurant_id="temp",  # Will be updated after restaurant creation
            image_type=RESTAURANT_BANNER,
        )

        if not banner_result.success:
            raise HTTPException(status_code=500, detail="Failed to upload banner image")

        # Save logo image if provided
        logo_url = None
        if logo_file:
            logo_content = await logo_file.read()
            is_valid, error_msg = validate_image_dimensions(
                logo_content, RESTAURANT_LOGO
            )
            if not is_valid:
                # Clean up banner image before raising error
                await cleanup_restaurant_images(
                    "temp", RESTAURANT_BANNER, keep_latest=False
                )
                raise HTTPException(status_code=400, detail=error_msg)

            logo_file.file.seek(0)  # Reset file pointer after reading
            logo_result = await save_restaurant_image(
                image=logo_file,
                restaurant_id="temp",  # Will be updated after restaurant creation
                image_type=RESTAURANT_LOGO,
            )

            if not logo_result.success:
                # Clean up banner image before raising error
                await cleanup_restaurant_images(
                    "temp", RESTAURANT_BANNER, keep_latest=False
                )
                raise HTTPException(
                    status_code=500, detail="Failed to upload logo image"
                )

            logo_url = logo_result.public_url

        banner_url = banner_result.public_url
        # Create restaurant data object
        restaurant_data = restaurant_schema.RestaurantCreate(
            name=name,
            address=address,
            description=description,
            phoneNumber=phone_number,
            settings=settings,
            bannerUrl=banner_url,
            logoUrl=logo_url,
        )

        # Create restaurant in database
        restaurant = await create_restaurant(restaurant_data)

        if restaurant is None:
            # Clean up uploaded images if restaurant creation fails
            await cleanup_restaurant_images(
                "temp", RESTAURANT_BANNER, keep_latest=False
            )
            if logo_file:
                await cleanup_restaurant_images(
                    "temp", RESTAURANT_LOGO, keep_latest=False
                )
            raise HTTPException(status_code=500, detail="Failed to create restaurant")

        # Update image paths with actual restaurant ID
        # Rename banner
        new_banner_blob_name = await rename_restaurant_image(
            old_restaurant_id="temp",
            new_restaurant_id=str(restaurant.id),
            image_type=RESTAURANT_BANNER,
            blob_name=banner_result.blob_name,
        )

        if not new_banner_blob_name:
            # Clean up uploaded images if renaming fails
            await cleanup_restaurant_images(
                "temp", RESTAURANT_BANNER, keep_latest=False
            )
            if logo_file:
                await cleanup_restaurant_images(
                    "temp", RESTAURANT_LOGO, keep_latest=False
                )
            raise HTTPException(
                status_code=500, detail="Failed to update banner image path"
            )

        # Rename logo if exists
        if logo_file:
            new_logo_blob_name = await rename_restaurant_image(
                old_restaurant_id="temp",
                new_restaurant_id=str(restaurant.id),
                image_type=RESTAURANT_LOGO,
                blob_name=logo_result.blob_name,
            )

            if not new_logo_blob_name:
                # Clean up uploaded images if renaming fails
                await cleanup_restaurant_images(
                    str(restaurant.id), RESTAURANT_BANNER, keep_latest=False
                )
                await cleanup_restaurant_images(
                    "temp", RESTAURANT_LOGO, keep_latest=False
                )
                raise HTTPException(
                    status_code=500, detail="Failed to update logo image path"
                )

        # Update restaurant with image URLs

        slug = await generate_unique_slug(
            name=restaurant.name, model=restaurant_schema.RestaurantDocument
        )

        await restaurant_model.update(
            str(restaurant.id),
            {"bannerUrl": banner_result.public_url, "logoUrl": logo_url, "slug": slug},
        )

        # Add manager membership to the user

        user_model = UserModel()
        user = await user_model.get_user_by_firebase_uid(firebase_uid)

        if not user:
            raise HTTPException(detail="User do not exist.", status_code=404)

        roles = await create_default_roles_for_restaurant(str(restaurant.id))

        # Find manager role and create membership
        manager_role = next((role for role in roles if role.name == "gerente"), None)
        if not manager_role:
            raise Exception("Manager role not found")

        # Create new membership
        membership = UserRestaurantMembership(
            roleId=str(manager_role.id), isActive=True
        )

        # Initialize memberships list if it doesn't exist
        if not user.memberships:
            user.memberships = []

        # Update user with new membership
        await user_model.update(
            _id=str(user.id),
            data={
                "memberships": [membership.model_dump(by_alias=True)],
                "currentRestaurantId": str(restaurant.id),
            },
        )

        return restaurant.to_response()

    except DuplicateKeyError as e:
        return HTTPException(
            status_code=500,
            detail="The number is already being used by another restaurant",
        )

    except Exception as e:
        print(e)
        # Clean up any uploaded images if restaurant creation fails
        if "banner_result" in locals() and banner_result.success:
            await cleanup_restaurant_images(
                "temp", RESTAURANT_BANNER, keep_latest=False
            )
        if "logo_result" in locals() and logo_result.success:
            await cleanup_restaurant_images("temp", RESTAURANT_LOGO, keep_latest=False)
        if restaurant:
            restaurant_id = restaurant.id
            await delete_restaurant(restaurant_id)

        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{restaurant_id}/deactivate", dependencies=[Depends(admin_required)])
async def deactivate_existing_restaurant(restaurant_id: str):
    return await deactivate_restaurant(restaurant_id)


@router.get("/{restaurant_id}")
async def get_single_restaurant(restaurant_id: str):
    try:
        restaurant = await get_restaurant(restaurant_id)
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        return restaurant.to_response()
    except Exception as error:
        print(error)
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/slug/{slug}")
async def get_restaurant_by_slug(slug: str):
    restaurant = await get_by_slug(slug)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant.to_response()


@router.get("/slug/{slug}/menu/items")
async def list_current_menu_items(slug: str):
    """Return all items in the restaurant's current menu identified by slug."""
    try:
        items = await list_current_menu_items_by_slug(slug)
        return [i.to_response() for i in items]
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.put("/{restaurant_id}")
async def update_existing_restaurant(
    restaurant_id: str, data: restaurant_schema.RestaurantUpdate
):
    return await update_restaurant(restaurant_id, data)


@router.put("/{restaurant_id}/banner")
async def update_restaurant_banner(
    restaurant_id: str, banner_file: UploadFile = File(..., alias="bannerFile")
):
    """Replace a restaurant's banner image and remove the old one."""
    restaurant = await get_restaurant(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    content = await banner_file.read()
    is_valid, error = validate_image_dimensions(content, RESTAURANT_BANNER)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    banner_file.file.seek(0)
    upload = await save_restaurant_image(banner_file, restaurant_id, RESTAURANT_BANNER)
    if not upload.success:
        raise HTTPException(status_code=500, detail="Failed to upload banner image")

    if restaurant.banner_url:
        blob = _blob_name_from_url(restaurant.banner_url)
        if blob:
            await delete_restaurant_image(
                restaurant_id, RESTAURANT_BANNER, blob_name=blob
            )

    updated = await restaurant_model.update(
        restaurant_id, {"bannerUrl": upload.public_url}
    )
    return updated.to_response()


@router.put("/{restaurant_id}/logo")
async def update_restaurant_logo(
    restaurant_id: str, logo_file: UploadFile = File(..., alias="logoFile")
):
    """Replace a restaurant's logo image and remove the old one."""
    restaurant = await get_restaurant(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    content = await logo_file.read()
    is_valid, error = validate_image_dimensions(content, RESTAURANT_LOGO)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    logo_file.file.seek(0)
    upload = await save_restaurant_image(logo_file, restaurant_id, RESTAURANT_LOGO)
    if not upload.success:
        raise HTTPException(status_code=500, detail="Failed to upload logo image")

    if restaurant.logo_url:
        blob = _blob_name_from_url(restaurant.logo_url)
        if blob:
            await delete_restaurant_image(
                restaurant_id, RESTAURANT_LOGO, blob_name=blob
            )

    updated = await restaurant_model.update(
        restaurant_id, {"logoUrl": upload.public_url}
    )
    return updated.to_response()


@router.put("/{restaurant_id}/current-menu/{menu_id}")
async def change_current_menu_endpoint(restaurant_id: str, menu_id: str):

    return await change_current_menu(restaurant_id, menu_id)


@router.get("/{restaurant_id}/menu")
async def get_current_menu_endpoint(restaurant_id: str):
    menu = await get_current_menu(restaurant_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Current menu not found")
    return menu.to_response()


@router.delete("/{restaurant_id}", dependencies=[Depends(admin_required)])
async def delete_existing_restaurant(restaurant_id: str):
    return await delete_restaurant(restaurant_id)


@router.get("/")
async def list_all_restaurants(admin=Depends(admin_required)):
    try:
        documents: List[restaurant_schema.RestaurantDocument] = await get_restaurants()
        restaurants = list(map(lambda restaurant: restaurant.to_response, documents))
        return restaurants
    except Exception as error:
        print(str(error))
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get("/active", response_model_by_alias=True)
async def get_active_restaurant(admin=Depends(admin_required)):
    documents = await get_active_restaurants()
    restaurants = list(map(lambda restaurant: restaurant.to_response, documents))
    return restaurants


@router.get("/members/{restaurant_id}")
async def get_all_members(restaurant_id: str):
    restaurant = await restaurant_model.get(restaurant_id)

    if not restaurant:
        raise HTTPException(detail="Restaurant not found", status_code=400)

    try:

        # Get all users who have a membership for this restaurant
        users = await user_model.get_all()

        # Filter users to only include those with active memberships for this restaurant
        restaurant_members = []
        for user in users:
            for membership in user.memberships:
                if membership:

                    # Get the role to check if it belongs to this restaurant
                    role = await role_model.get(membership.role_id)
                    if role and role.restaurant_id == restaurant_id:
                        restaurant_members.append(user.to_response())
                        break

        return restaurant_members
    except Exception as error:
        print(error)


@router.delete("/{restaurant_id}/members/{user_id}")
async def remove_member(restaurant_id: str, user_id: str):
    """Remove a member from a restaurant.

    This will deactivate the user's membership for the provided restaurant.
    """
    restaurant = await restaurant_model.get(restaurant_id)
    if not restaurant:
        raise HTTPException(detail="Restaurant not found", status_code=400)

    user = await user_model.get(user_id)
    if not user:
        raise HTTPException(detail="User not found", status_code=404)

    updated = False
    for membership in user.memberships:
        if membership.is_active:
            role = await role_model.get(membership.roleId)
            if role and role.restaurantId == restaurant_id:
                membership.is_active = False
                updated = True

    if not updated:
        raise HTTPException(
            detail="User is not a member of this restaurant", status_code=400
        )

    update_data = {
        "memberships": [m.model_dump(by_alias=True) for m in user.memberships]
    }
    if user.current_restaurant_id == restaurant_id:
        update_data["currentRestaurantId"] = None

    await user_model.update(str(user.id), update_data)
    return True
