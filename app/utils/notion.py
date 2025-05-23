from typing import Dict, Any, List, Optional
import html
from app.schema.notion import BlogPostMeta, NotionText, NotionBlock


def parse_post_meta(page: BlogPostMeta) -> BlogPostMeta:

    return BlogPostMeta(
        id=page["id"],
        title=page["properties"]["Title"]["title"][0]["plain_text"],
        slug=page["properties"]["Slug"]["rich_text"][0]["plain_text"],
        published=page["properties"]["Published"]["checkbox"],
        date=page["properties"]["Date"]["date"]["start"] if page["properties"]["Date"]["date"] else None,
        tags=[tag["name"] for tag in page["properties"]["Tags"]["multi_select"]]
    )

def parse_block(block: Dict[str, Any]) -> NotionBlock:
    block_type = block["type"]
    text_elements = block.get(block_type, {}).get("text", [])

    parsed_text = [
        NotionText(
            content=t["plain_text"],
            link=t.get("href"),
            #annotations=t.get("annotations", {})
        )
        for t in text_elements
    ] if text_elements else None

    return NotionBlock(
        id=block["id"],
        type=block_type,
        text=parsed_text,
        has_children=block.get("has_children", False),
        raw=block
    )


def render_text(text: List[NotionText], base_url: str, escape: bool = True) -> str:
    html_out = ""
    for segment in text:
        content = html.escape(segment.content) if escape else segment.content
        link = segment.link
        ann = segment.annotations if hasattr(segment, "annotations") else {}

        classes = []
        if ann.get("bold"):
            classes.append("font-bold")
        if ann.get("italic"):
            classes.append("italic")
        if ann.get("underline"):
            classes.append("underline")
        if ann.get("strikethrough"):
            classes.append("line-through")
        if ann.get("code"):
            classes.append("bg-gray-100 px-1 rounded text-sm font-mono")

        class_attr = f' class="{' '.join(classes)}"' if classes else ""
        wrapped_content = f"<span{class_attr}>{content}</span>"

        if not link:
            html_out += wrapped_content
        elif link.startswith(base_url):
            internal_path = link.replace(base_url, "") or "/"
            html_out += f'<a href="{internal_path}" data-internal="true">{wrapped_content}</a>'
        else:
            html_out += f'<a href="{link}" target="_blank" rel="noopener noreferrer">{wrapped_content}</a>'

    return html_out

def extract_excerpt(blocks: List[NotionBlock]) -> Optional[str]:
    for block in blocks:
        if block.type == "paragraph" and block.text:
            raw_text = " ".join(t.content for t in block.text)
            if raw_text.strip():
                return raw_text.strip()[:160]  # limit to 160 characters
    return None

def render_block(block: NotionBlock, base_url: str) -> str:
    t = block.type
    text_html = render_text(block.text or [], base_url, escape=(t != "code"))

    children_html = ""
    if block.children:
        children_html = render_blocks_to_html(block.children, base_url)

    match t:
        case "paragraph":
            if not text_html.strip():
                return ""
            return f"<p class='notion-paragraph'>{text_html}</p>"
        case "heading_1":
            return f"<h1 class='notion-heading1'>{text_html}</h1>"
        case "heading_2":
            return f"<h2 class='notion-heading2'>{text_html}</h2>"
        case "heading_3":
            return f"<h3 class='notion-heading3'>{text_html}</h3>"
        case "quote":
            return f"<blockquote class='notion-quote'>{text_html}</blockquote>"
        case "callout":
            icon = block.raw.get("callout", {}).get("icon", {}).get("emoji", "")
            return f"<div class='notion-callout'>{icon} {text_html}</div>"
        case "bulleted_list_item" | "numbered_list_item":
            return f"<li class='notion-list-item'>{text_html}{children_html}</li>"
        case "divider":
            return "<hr class='notion-divider' />"
        case "code":
            lang = block.raw.get("code", {}).get("language", "")
            return f"<pre class='notion-code'><code class='language-{lang}'>{text_html}</code></pre>"
        case "image":
            image_data = block.raw.get("image", {})
            url = image_data.get("external", {}).get("url") or image_data.get("file", {}).get("url")
            caption_data = image_data.get("caption", [])
            alt = caption_data[0].get("plain_text", "") if caption_data else ""
            alt_escaped = html.escape(alt)
            return f"<figure class='notion-image'><img src='{url}' alt='{alt_escaped}' class='mx-auto w-[600px] max-w-full rounded-md shadow-sm' /><figcaption class='text-center text-sm mt-2 text-gray-500'>{alt_escaped}</figcaption></figure>"
        case "toggle":
            return f"<details class='notion-toggle'><summary>{text_html}</summary>{children_html}</details>"
        case _:
            return f"<p class='notion-paragraph'>{text_html}</p>{children_html}"

def render_blocks_to_html(blocks: List[NotionBlock], base_url: str) -> str:
    html_parts = []
    current_list_type = None
    current_list_items = []

    for block in blocks:
        if block.type in ["bulleted_list_item", "numbered_list_item"]:
            tag = "ul" if block.type == "bulleted_list_item" else "ol"

            if current_list_type != tag:
                if current_list_items:
                    html_parts.append(f"<{current_list_type} class='notion-list'>" + "".join(current_list_items) + f"</{current_list_type}>")
                    current_list_items = []
                current_list_type = tag

            current_list_items.append(render_block(block, base_url))
        else:
            if current_list_items:
                html_parts.append(f"<{current_list_type} class='notion-list'>" + "".join(current_list_items) + f"</{current_list_type}>")
                current_list_items = []
                current_list_type = None

            html_parts.append(render_block(block, base_url))

    if current_list_items:
        html_parts.append(f"<{current_list_type} class='notion-list'>" + "".join(current_list_items) + f"</{current_list_type}>")

    return "".join(html_parts)
