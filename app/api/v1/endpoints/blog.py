from typing import List

from fastapi import APIRouter, HTTPException, Request

from app.services.notion_service import get_notion_service
from app.schema.notion import BlogPostMeta, BlogPost

router = APIRouter()
notion = get_notion_service()

@router.get("/", response_model=List[BlogPostMeta])
def get_blog_posts():
    posts = notion.get_database_entries(only_published=True)
    return posts


@router.get("/{slug}", response_model=BlogPost)
def get_blog_post(slug: str, request: Request):
    scheme = request.url.scheme
    host = request.headers.get("host")
    base_url = f"{scheme}://{host}"

    post = notion.get_post_by_slug(slug, base_url=base_url)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
