from typing import Optional, Tuple, List
from fastapi import UploadFile
from PIL import Image
import io
import re

from app.services.google_bucket import (
    get_google_bucket_manager,
    ImageFormat,
    UploadResult,
)

# Constants for restaurant image types
RESTAURANT_BANNER = "banner"
RESTAURANT_LOGO = "logo"

# Maximum dimensions for restaurant images
MAX_BANNER_DIMENSIONS = (1920, 1080)  # 16:9 aspect ratio
MAX_LOGO_DIMENSIONS = (500, 500)  # Square format

# =====================
# Item Image Utils
# =====================


async def save_item_image(
    image: UploadFile,
    restaurant_id: str,
    item_id: str,
    optimize: bool = True,
) -> UploadResult:
    """Save an item image to cloud storage."""
    content = await image.read()
    image_manager = get_google_bucket_manager()
    folder = f"restaurants/{restaurant_id}/items/{item_id}"

    return image_manager.upload_image(
        image_source=content,
        filename=image.filename,
        folder=folder,
        public=True,
        optimize=optimize,
        format_type=ImageFormat.JPEG,
        quality=85,
        metadata={
            "restaurant_id": restaurant_id,
            "item_id": item_id,
            "original_filename": image.filename,
        },
    )


async def save_restaurant_image(
    image: UploadFile, restaurant_id: str, image_type: str, optimize: bool = True
) -> UploadResult:
    """
    Save a restaurant image (banner or logo) to cloud storage.

    Args:
        image: The uploaded image file
        restaurant_id: The ID of the restaurant
        image_type: Type of image (banner or logo)
        optimize: Whether to optimize the image

    Returns:
        UploadResult containing the upload status and metadata
    """
    # Validate image type
    if image_type not in [RESTAURANT_BANNER, RESTAURANT_LOGO]:
        raise ValueError(
            f"Invalid image type. Must be one of: {RESTAURANT_BANNER}, {RESTAURANT_LOGO}"
        )

    # Read image content
    content = await image.read()

    # Get image manager
    image_manager = get_google_bucket_manager()

    # Determine folder and dimensions based on image type
    folder = f"restaurants/{restaurant_id}/{image_type}"
    max_dimensions = (
        MAX_BANNER_DIMENSIONS
        if image_type == RESTAURANT_BANNER
        else MAX_LOGO_DIMENSIONS
    )

    # Process and upload image
    result = image_manager.upload_image(
        image_source=content,
        filename=image.filename,
        folder=folder,
        public=True,  # Make images publicly accessible
        optimize=optimize,
        format_type=ImageFormat.JPEG,
        quality=85,
        metadata={
            "restaurant_id": restaurant_id,
            "image_type": image_type,
            "original_filename": image.filename,
        },
    )

    return result


async def delete_restaurant_image(
    restaurant_id: str, image_type: str, blob_name: Optional[str] = None
) -> bool:
    """
    Delete a restaurant image from cloud storage.

    Args:
        restaurant_id: The ID of the restaurant
        image_type: Type of image (banner or logo)
        blob_name: Optional specific blob name to delete. If not provided,
                  will delete the most recent image of the specified type.

    Returns:
        bool indicating success of deletion
    """
    # Validate image type
    if image_type not in [RESTAURANT_BANNER, RESTAURANT_LOGO]:
        raise ValueError(
            f"Invalid image type. Must be one of: {RESTAURANT_BANNER}, {RESTAURANT_LOGO}"
        )

    image_manager = get_google_bucket_manager()

    if blob_name:
        # Delete specific image
        return image_manager.delete_image(blob_name)
    else:
        # List images in the restaurant's folder
        folder = f"restaurants/{restaurant_id}/{image_type}"
        images = image_manager.list_images(folder=folder)

        if not images:
            return False

        # Delete the most recent image
        return image_manager.delete_image(images[-1])


def get_restaurant_image_url(
    restaurant_id: str, image_type: str, blob_name: Optional[str] = None
) -> Optional[str]:
    """
    Get the public URL for a restaurant image.

    Args:
        restaurant_id: The ID of the restaurant
        image_type: Type of image (banner or logo)
        blob_name: Optional specific blob name. If not provided,
                  will return URL for the most recent image of the specified type.

    Returns:
        Optional[str]: The public URL of the image, or None if not found
    """
    # Validate image type
    if image_type not in [RESTAURANT_BANNER, RESTAURANT_LOGO]:
        raise ValueError(
            f"Invalid image type. Must be one of: {RESTAURANT_BANNER}, {RESTAURANT_LOGO}"
        )

    image_manager = get_google_bucket_manager()

    if blob_name:
        # Get URL for specific image
        image_info = image_manager.get_image_info(blob_name)
        return image_info.public_url if image_info else None
    else:
        # List images in the restaurant's folder
        folder = f"restaurants/{restaurant_id}/{image_type}"
        images = image_manager.list_images(folder=folder)

        if not images:
            return None

        # Get URL for the most recent image
        image_info = image_manager.get_image_info(images[-1])
        return image_info.public_url if image_info else None


def validate_image_dimensions(
    image_data: bytes, image_type: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate image dimensions based on type.

    Args:
        image_data: The image data in bytes
        image_type: Type of image (banner or logo)

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        width, height = image.size

        if image_type == RESTAURANT_BANNER:
            max_width, max_height = MAX_BANNER_DIMENSIONS
            if width > max_width or height > max_height:
                return (
                    False,
                    f"Banner image dimensions exceed maximum allowed size of {max_width}x{max_height}",
                )
        elif image_type == RESTAURANT_LOGO:
            max_width, max_height = MAX_LOGO_DIMENSIONS
            if width > max_width or height > max_height:
                return (
                    False,
                    f"Logo image dimensions exceed maximum allowed size of {max_width}x{max_height}",
                )

        return True, None
    except Exception as e:
        return False, f"Failed to validate image dimensions: {str(e)}"


async def rename_restaurant_image(
    old_restaurant_id: str,
    new_restaurant_id: str,
    image_type: str,
    blob_name: Optional[str] = None,
) -> Optional[str]:
    """
    Rename a restaurant image blob to use a new restaurant ID.

    Args:
        old_restaurant_id: The current restaurant ID in the blob name
        new_restaurant_id: The new restaurant ID to use
        image_type: Type of image (banner or logo)
        blob_name: Optional specific blob name to rename. If not provided,
                  will rename the most recent image of the specified type.

    Returns:
        Optional[str]: The new blob name if successful, None otherwise
    """
    # Validate image type
    if image_type not in [RESTAURANT_BANNER, RESTAURANT_LOGO]:
        raise ValueError(
            f"Invalid image type. Must be one of: {RESTAURANT_BANNER}, {RESTAURANT_LOGO}"
        )

    image_manager = get_google_bucket_manager()

    if not blob_name:
        # Get the most recent image for this type
        folder = f"restaurants/{old_restaurant_id}/{image_type}"
        images = image_manager.list_images(folder=folder)
        if not images:
            return None
        blob_name = images[-1]

    # Create new blob name
    new_blob_name = blob_name.replace(old_restaurant_id, new_restaurant_id)

    try:
        # Get the source blob
        source_blob = image_manager.bucket.blob(blob_name)

        # Create a new blob with the new name
        new_blob = image_manager.bucket.blob(new_blob_name)

        # Copy the source blob to the new blob
        image_manager.bucket.copy_blob(source_blob, image_manager.bucket, new_blob_name)

        # Delete the old blob
        source_blob.delete()

        return new_blob_name
    except Exception as e:
        image_manager.logger.error(f"Failed to rename blob {blob_name}: {e}")
        return None


async def cleanup_restaurant_images(
    restaurant_id: str, image_type: str, keep_latest: bool = True
) -> bool:
    """
    Clean up all images for a restaurant of a specific type.

    Args:
        restaurant_id: The restaurant ID
        image_type: Type of image (banner or logo)
        keep_latest: Whether to keep the most recent image

    Returns:
        bool: True if cleanup was successful, False otherwise
    """
    # Validate image type
    if image_type not in [RESTAURANT_BANNER, RESTAURANT_LOGO]:
        raise ValueError(
            f"Invalid image type. Must be one of: {RESTAURANT_BANNER}, {RESTAURANT_LOGO}"
        )

    image_manager = get_google_bucket_manager()

    try:
        # List all images for this restaurant and type
        folder = f"restaurants/{restaurant_id}/{image_type}"
        images = image_manager.list_images(folder=folder)

        if not images:
            return True

        if keep_latest:
            # Keep the most recent image, delete the rest
            images_to_delete = images[:-1]
        else:
            # Delete all images
            images_to_delete = images

        # Delete the images
        success = True
        for blob_name in images_to_delete:
            if not image_manager.delete_image(blob_name):
                success = False

        return success
    except Exception as e:
        image_manager.logger.error(
            f"Failed to cleanup images for restaurant {restaurant_id}: {e}"
        )
        return False
