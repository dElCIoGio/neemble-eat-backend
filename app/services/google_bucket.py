import os
import io
import uuid
from functools import lru_cache
from typing import Optional, List, Dict, Union, BinaryIO, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account
from PIL import Image, ImageOps
from google.oauth2.service_account import Credentials

from app.core.dependencies import get_logger, get_settings, get_gcp_service_account_credentials
from app.utils.time import now_in_luanda


class ImageFormat(Enum):
    """Supported image formats"""
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WEBP"
    AVIF = "AVIF"


@dataclass
class ImageMetadata:
    """Container for image metadata"""
    filename: str
    size_bytes: int
    width: int
    height: int
    format: str
    content_type: str
    created_at: datetime
    public_url: Optional[str] = None
    signed_url: Optional[str] = None


@dataclass
class UploadResult:
    """Result of an image upload operation"""
    success: bool
    blob_name: str
    public_url: Optional[str] = None
    signed_url: Optional[str] = None
    metadata: Optional[ImageMetadata] = None
    error: Optional[str] = None


class GCSImageManager:
    """
    Modern Google Cloud Storage manager for image handling with advanced features:
    - Image optimization and resizing
    - Multiple format support
    - Batch operations
    - URL generation (public/signed)
    - Metadata extraction
    - Error handling and logging
    """

    def __init__(
            self,
            bucket_name: str,
            credentials: dict = None,
            project_id: Optional[str] = None,
            default_folder: str = "images",
            auto_optimize: bool = True,
            max_image_size: Tuple[int, int] = (2048, 2048),
            default_quality: int = 85
    ):
        """
        Initialize the GCS Image Manager

        Args:
            bucket_name: Name of the GCS bucket
            credentials_path: Path to service account JSON file (optional if using ADC)
            project_id: GCP project ID (optional if in credentials)
            default_folder: Default folder for image uploads
            auto_optimize: Whether to automatically optimize images
            max_image_size: Maximum dimensions for image resizing (width, height)
            default_quality: Default JPEG/WEBP quality (1-100)
        """
        self.bucket_name = bucket_name
        self.default_folder = default_folder.strip('/')
        self.auto_optimize = auto_optimize
        self.max_image_size = max_image_size
        self.default_quality = default_quality

        # Setup logging
        self.logger = get_logger()

        # Initialize GCS client
        self._init_client(credentials, project_id)

        # Get bucket reference
        try:
            self.bucket = self.client.bucket(bucket_name)
            # Test bucket access
            self.bucket.reload()
        except Exception as e:
            self.logger.error(f"Failed to access bucket '{bucket_name}': {e}")
            raise

    def _init_client(self, credentials: dict, project_id: Optional[str]):
        """Initialize the GCS client with proper authentication"""
        try:

            cred = Credentials.from_service_account_info(credentials)

            self.client = storage.Client(credentials=cred)

        except Exception as e:
            self.logger.error(f"Failed to initialize GCS client: {e}")
            raise

    def _generate_blob_name(self, filename: str, folder: Optional[str] = None) -> str:
        """Generate a unique blob name with folder structure"""
        folder = folder or self.default_folder

        # Extract file extension
        file_path = Path(filename)
        name_without_ext = file_path.stem
        extension = file_path.suffix.lower()

        # Generate unique identifier
        timestamp = now_in_luanda().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]

        # Create blob name
        unique_filename = f"{name_without_ext}_{timestamp}_{unique_id}{extension}"
        return f"{folder}/{unique_filename}" if folder else unique_filename

    def _optimize_image(
            self,
            image: Image.Image,
            format_type: ImageFormat = ImageFormat.JPEG,
            quality: Optional[int] = None
    ) -> Tuple[bytes, str]:
        """
        Optimize image for web usage

        Returns:
            Tuple of (optimized_image_bytes, content_type)
        """
        quality = quality or self.default_quality

        # Resize if needed
        # if image.size[0] > self.max_image_size[0] or image.size[1] > self.max_image_size[1]:
        #     image = ImageOps.fit(
        #         image,
        #         self.max_image_size,
        #         Image.Resampling.LANCZOS
        #     )

        # Convert to RGB if necessary (for JPEG)
        if format_type == ImageFormat.JPEG and image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background

        # Save optimized image to bytes
        output = io.BytesIO()
        save_kwargs = {}

        if format_type in [ImageFormat.JPEG, ImageFormat.WEBP]:
            save_kwargs['quality'] = quality
            save_kwargs['optimize'] = True

        if format_type == ImageFormat.PNG:
            save_kwargs['optimize'] = True

        image.save(output, format=format_type.value, **save_kwargs)

        # Determine content type
        content_type_map = {
            ImageFormat.JPEG: 'image/jpeg',
            ImageFormat.PNG: 'image/png',
            ImageFormat.WEBP: 'image/webp',
            ImageFormat.AVIF: 'image/avif'
        }

        return output.getvalue(), content_type_map[format_type]

    def _extract_image_metadata(self, image_data: bytes, filename: str) -> ImageMetadata:
        """Extract metadata from image data"""
        try:
            image = Image.open(io.BytesIO(image_data))

            return ImageMetadata(
                filename=filename,
                size_bytes=len(image_data),
                width=image.size[0],
                height=image.size[1],
                format=image.format or 'Unknown',
                content_type=f'image/{image.format.lower()}' if image.format else 'application/octet-stream',
                created_at=now_in_luanda()
            )
        except Exception as e:
            self.logger.warning(f"Failed to extract image metadata: {e}")
            return ImageMetadata(
                filename=filename,
                size_bytes=len(image_data),
                width=0,
                height=0,
                format='Unknown',
                content_type='application/octet-stream',
                created_at=now_in_luanda()
            )

    def upload_image(
            self,
            image_source: Union[str, bytes, BinaryIO, Image.Image],
            filename: Optional[str] = None,
            folder: Optional[str] = None,
            public: bool = False,
            optimize: Optional[bool] = None,
            format_type: ImageFormat = ImageFormat.JPEG,
            quality: Optional[int] = None,
            metadata: Optional[Dict[str, str]] = None
    ) -> UploadResult:
        """
        Upload an image to GCS with optimization options

        Args:
            image_source: Image file path, bytes, file object, or PIL Image
            filename: Custom filename (auto-generated if None)
            folder: Folder to upload to (uses default if None)
            public: Whether to make the image publicly accessible
            optimize: Whether to optimize the image (uses auto_optimize if None)
            format_type: Output format for the image
            quality: Image quality (1-100)
            metadata: Additional metadata to store with the image

        Returns:
            UploadResult with success status and details
        """
        try:
            # Process image source
            if isinstance(image_source, str):
                # File path
                if not os.path.exists(image_source):
                    return UploadResult(
                        success=False,
                        blob_name="",
                        error=f"File not found: {image_source}"
                    )
                with open(image_source, 'rb') as f:
                    image_data = f.read()
                filename = filename or os.path.basename(image_source)

            elif isinstance(image_source, bytes):
                # Raw bytes
                image_data = image_source
                filename = filename or f"image_{uuid.uuid4().hex[:8]}.jpg"

            elif hasattr(image_source, 'read'):
                # File-like object
                image_data = image_source.read()
                filename = filename or f"image_{uuid.uuid4().hex[:8]}.jpg"

            elif isinstance(image_source, Image.Image):
                # PIL Image
                output = io.BytesIO()
                image_source.save(output, format='PNG')
                image_data = output.getvalue()
                filename = filename or f"image_{uuid.uuid4().hex[:8]}.png"
            else:
                return UploadResult(
                    success=False,
                    blob_name="",
                    error="Unsupported image source type"
                )

            # Optimize image if requested
            optimize = optimize if optimize is not None else self.auto_optimize
            if optimize:
                try:
                    image = Image.open(io.BytesIO(image_data))
                    image_data, content_type = self._optimize_image(
                        image, format_type, quality
                    )
                    # Update filename extension if format changed
                    filename = Path(filename).stem + f".{format_type.value.lower()}"
                except Exception as e:
                    self.logger.warning(f"Image optimization failed: {e}")
                    # Continue with original image

            # Generate blob name
            blob_name = self._generate_blob_name(filename, folder)

            # Create blob and upload
            blob = self.bucket.blob(blob_name)

            # Set content type
            if 'content_type' not in locals():
                content_type = 'image/jpeg'  # default
            blob.content_type = content_type

            # Add custom metadata
            if metadata:
                blob.metadata = metadata

            # Upload the image
            blob.upload_from_string(image_data, content_type=content_type)

            public_url = f"https://storage.googleapis.com/{self.bucket.name}/{blob_name}"

            # Extract image metadata
            img_metadata = self._extract_image_metadata(image_data, filename)
            img_metadata.public_url = public_url

            self.logger.info(f"Successfully uploaded image: {blob_name}")

            return UploadResult(
                success=True,
                blob_name=blob_name,
                public_url=public_url,
                metadata=img_metadata
            )

        except Exception as e:
            self.logger.error(f"Failed to upload image: {e}")
            return UploadResult(
                success=False,
                blob_name="",
                error=str(e)
            )

    def download_image(self, blob_name: str) -> Optional[bytes]:
        """Download an image from GCS"""
        try:
            blob = self.bucket.blob(blob_name)
            return blob.download_as_bytes()
        except NotFound:
            self.logger.error(f"Image not found: {blob_name}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to download image {blob_name}: {e}")
            return None

    def delete_image(self, blob_name: str) -> bool:
        """Delete an image from GCS"""
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            self.logger.info(f"Successfully deleted image: {blob_name}")
            return True
        except NotFound:
            self.logger.warning(f"Image not found for deletion: {blob_name}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete image {blob_name}: {e}")
            return False

    def list_images(
            self,
            folder: Optional[str] = None,
            limit: Optional[int] = None,
            include_metadata: bool = False
    ) -> List[Union[str, ImageMetadata]]:
        """List images in the bucket or folder"""
        try:
            prefix = f"{folder}/" if folder else f"{self.default_folder}/"
            blobs = self.client.list_blobs(
                self.bucket,
                prefix=prefix,
                max_results=limit
            )

            results = []
            for blob in blobs:
                if include_metadata:
                    # Download and extract metadata (expensive operation)
                    try:
                        image_data = blob.download_as_bytes()
                        metadata = self._extract_image_metadata(image_data, blob.name)
                        metadata.public_url = blob.public_url if blob.public_url_set else None
                        results.append(metadata)
                    except Exception as e:
                        self.logger.warning(f"Failed to get metadata for {blob.name}: {e}")
                        results.append(blob.name)
                else:
                    results.append(blob.name)

            return results

        except Exception as e:
            self.logger.error(f"Failed to list images: {e}")
            return []

    def generate_signed_url(
            self,
            blob_name: str,
            expiration_hours: int = 1,
            method: str = 'GET'
    ) -> Optional[str]:
        """Generate a signed URL for temporary access"""
        try:
            blob = self.bucket.blob(blob_name)

            # Check if blob exists
            if not blob.exists():
                self.logger.error(f"Blob does not exist: {blob_name}")
                return None

            expiration = now_in_luanda() + timedelta(hours=expiration_hours)

            signed_url = blob.generate_signed_url(
                expiration=expiration,
                method=method
            )

            return signed_url

        except Exception as e:
            self.logger.error(f"Failed to generate signed URL for {blob_name}: {e}")
            return None

    def batch_upload(
            self,
            image_sources: List[Union[str, bytes, BinaryIO]],
            folder: Optional[str] = None,
            public: bool = False,
            optimize: bool = True
    ) -> List[UploadResult]:
        """Upload multiple images in batch"""
        results = []

        for i, source in enumerate(image_sources):
            filename = f"batch_image_{i}_{uuid.uuid4().hex[:8]}.jpg"
            result = self.upload_image(
                source,
                filename=filename,
                folder=folder,
                public=public,
                optimize=optimize
            )
            results.append(result)

        successful = sum(1 for r in results if r.success)
        self.logger.info(f"Batch upload completed: {successful}/{len(results)} successful")

        return results

    def get_image_info(self, blob_name: str) -> Optional[ImageMetadata]:
        """Get detailed information about an image"""
        try:
            blob = self.bucket.blob(blob_name)

            if not blob.exists():
                return None

            # Download image to extract metadata
            image_data = blob.download_as_bytes()
            metadata = self._extract_image_metadata(image_data, blob.name)

            # Add GCS-specific info
            blob.reload()
            metadata.created_at = blob.time_created
            metadata.public_url = blob.public_url if getattr(blob, 'public_url_set', False) else None

            return metadata

        except Exception as e:
            self.logger.error(f"Failed to get image info for {blob_name}: {e}")
            return None

    def create_thumbnail(
            self,
            blob_name: str,
            size: Tuple[int, int] = (150, 150),
            suffix: str = "_thumb"
    ) -> Optional[str]:
        """Create a thumbnail version of an image"""
        try:
            # Download original image
            original_blob = self.bucket.blob(blob_name)
            image_data = original_blob.download_as_bytes()

            # Create thumbnail
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail(size, Image.Resampling.LANCZOS)

            # Save thumbnail
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)

            # Generate thumbnail blob name
            path = Path(blob_name)
            thumb_name = f"{path.parent}/{path.stem}{suffix}{path.suffix}"

            # Upload thumbnail
            thumb_blob = self.bucket.blob(thumb_name)
            thumb_blob.content_type = 'image/jpeg'
            thumb_blob.upload_from_string(output.getvalue())

            self.logger.info(f"Created thumbnail: {thumb_name}")
            return thumb_name

        except Exception as e:
            self.logger.error(f"Failed to create thumbnail for {blob_name}: {e}")
            return None


@lru_cache
def get_google_bucket_manager():

    settings = get_settings()

    # bucket_name: str,
    # credentials_path: dict = None,
    # project_id: Optional[str] = None,
    # default_folder: str = "images",
    # auto_optimize: bool = True,
    # max_image_size: Tuple[int, int] = (2048, 2048),
    # default_quality: int = 85

    credentials = get_gcp_service_account_credentials()

    manager = GCSImageManager(
        bucket_name=settings.BUCKET_NAME,
        credentials=credentials,
        project_id="neemble-eat",
        default_folder="uploads",
        auto_optimize=True,
        max_image_size=(1920, 1080)
    )
    return manager