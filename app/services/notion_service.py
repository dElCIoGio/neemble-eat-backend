import json
from datetime import datetime
from functools import lru_cache

from notion_client import Client
from typing import List, Optional, Dict, Any
from app.schema.notion import BlogPostMeta, BlogPost, NotionBlock, NotionText

from app.core.dependencies import get_settings
from app.utils.notion import render_blocks_to_html, extract_excerpt


class NotionService:
    def __init__(self, api_key: str, database_id: str):
        self.client = Client(auth=api_key)
        self.database_id = database_id

    def get_database_entries(self, only_published: bool = True) -> List[BlogPostMeta]:
        """
        Fetches blog post metadata from the Notion database.
        """
        query_filter = {
            "property": "Published",
            "checkbox": {"equals": True}
        } if only_published else {}

        response = self.client.databases.query(
            database_id=self.database_id,
            filter=query_filter
        )
        pages = response.get("results", [])
        return [self._parse_post_meta(p) for p in pages]

    def get_post_by_slug(self, slug: str, base_url: str) -> Optional[BlogPost]:
        if slug.startswith("ART-"):
            slug_number = int(slug.replace("ART-", ""))
        else:
            raise ValueError("Invalid slug format")

        response = self.client.databases.query(
            database_id=self.database_id,
            filter={
                "property": "Slug",
                "unique_id": {
                    "equals": slug_number
                }
            }
        )
        results = response.get("results", [])
        if not results:
            return None

        page = results[0]
        blocks = self.get_page_content(page["id"])  # ✅ You already have the blocks here
        html = render_blocks_to_html(blocks, base_url)
        excerpt = extract_excerpt(blocks)  # ✅ Add this here

        meta = self._parse_post_meta(page)
        meta.excerpt = excerpt  # ✅ Inject excerpt into BlogPostMeta

        return BlogPost(
            meta=meta,
            html=html
        )


    def _parse_post_meta(self, page: Dict[str, Any]) -> BlogPostMeta:
        props = page["properties"]

        # Title
        title = props["Title"]["title"][0]["plain_text"] if props["Title"]["title"] else None

        # Slug (Rich Text)
        slug = f'{props["Slug"]["unique_id"]["prefix"]}-{str(props["Slug"]["unique_id"]["number"])}'

        # Published (Checkbox)
        published = props["Published"]["checkbox"]

        # Tags (Multi-select)
        tags = [tag["name"] for tag in props["Tags"]["multi_select"]]

        # Status (Status object)
        status = props["Status"]["status"]["name"] if props["Status"]["status"] else None

        # Date
        date = props["Date"]["date"]["start"] if props["Date"]["date"] else None

        raw_date = page["properties"]["Date"]["date"]
        raw_cover = page.get("cover")

        cover = None
        if raw_cover:
            if raw_cover["type"] == "external":
                cover = raw_cover["external"]["url"]
            elif raw_cover["type"] == "file":
                cover = raw_cover["file"]["url"]

        return BlogPostMeta(
            id=page["id"],
            title=page["properties"]["Title"]["title"][0]["plain_text"],
            slug=slug,
            published=page["properties"]["Published"]["checkbox"],
            date=raw_date["start"] if raw_date else None,
            status=status,
            tags=[tag["name"] for tag in page["properties"]["Tags"]["multi_select"]],
            cover=cover
        )

    def _parse_block(self, block: dict) -> NotionBlock:
        block_type = block["type"]
        rich_text = block.get(block_type, {}).get("rich_text", [])

        parsed_text = [
            NotionText(
                content=item["plain_text"],
                link=item.get("href"),
                annotations=item.get("annotations", {})  # ✅ Make sure annotations are captured
            )
            for item in rich_text
        ] if rich_text else []

        return NotionBlock(
            id=block["id"],
            type=block_type,
            text=parsed_text,
            has_children=block.get("has_children", False),
            raw=block
        )

    def get_page_content(self, block_id: str) -> List[NotionBlock]:
        return self._fetch_blocks_recursive(block_id)

    def _fetch_blocks_recursive(self, parent_id: str) -> List[NotionBlock]:
        blocks = self.client.blocks.children.list(block_id=parent_id)["results"]
        parsed = []

        for block in blocks:
            parsed_block = self._parse_block(block)

            if parsed_block.has_children:
                children = self._fetch_blocks_recursive(block["id"])
                parsed_block.children = children  # ⬅️ add children recursively

            parsed.append(parsed_block)

        return parsed


@lru_cache
def get_notion_service() -> NotionService:
    settings = get_settings()
    return NotionService(
        settings.NOTION_INTERNAL_INTEGRATION_SECRET,
        settings.NOTION_BLOG_DATABASE
    )