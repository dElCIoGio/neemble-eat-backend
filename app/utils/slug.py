import re
from typing import Type
from beanie import Document


def slugify(text: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', text.lower())
    slug = re.sub(r'-{2,}', '-', slug).strip('-')
    return slug


async def generate_unique_slug(name: str, model: Type[Document], slug_field: str = "slug") -> str:
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    existing = await model.find_one({slug_field: slug})
    while existing:
        counter += 1
        slug = f"{base_slug}-{counter}"
        existing = await model.find_one({slug_field: slug})
    return slug
