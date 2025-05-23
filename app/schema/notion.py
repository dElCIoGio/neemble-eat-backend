from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal, Union
from datetime import date, datetime


class BlogPostMeta(BaseModel):
    id: str
    title: str
    slug: str
    published: bool
    date: Optional[datetime] = None
    tags: Optional[List[str]] = []
    status: Optional[Union[str, None]] = Field(default="Not Started")
    cover: Optional[str] = None
    excerpt: Optional[str] = ""


    @field_validator("date")
    def validate_date(cls, v):
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return None


class NotionText(BaseModel):
    content: str
    link: Optional[str] = None
    annotations: Optional[dict] = {}


class NotionBlock(BaseModel):
    id: str
    type: str
    text: Optional[List[NotionText]] = None
    has_children: bool
    raw: Optional[dict] = None
    children: Optional[List["NotionBlock"]] = None

NotionBlock.model_rebuild()

class BlogPost(BaseModel):
    meta: BlogPostMeta
    html: str
