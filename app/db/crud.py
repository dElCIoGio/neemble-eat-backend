
from beanie import Document, PydanticObjectId
from beanie.odm.operators.find.logical import LogicalOperatorForListOfExpressions
from bson import ObjectId
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union, Mapping

from motor.motor_asyncio import AsyncIOMotorCollection
from openai import BaseModel
from pydantic import Field
from pymongo import DESCENDING

from app.schema.collection_id.object_id import PyObjectId
from app.utils.time import now_in_luanda

T = TypeVar("T", bound=Document)

def to_object_id(_id: str) -> PydanticObjectId:
    try:
        _id = PydanticObjectId(
            ObjectId(_id)
        )
        return _id
    except:
        raise ValueError("Invalid ObjectId")


class PaginationResult[T](BaseModel):
    items: List[T]
    next_cursor: Optional[PyObjectId] = Field(default=None, alias="nextCursor")
    total_count: int = Field(..., alias="totalCount")
    has_more: bool = Field(..., alias="hasMore")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }



class MongoCrud(Generic[T]):

    def __init__(self, model: Type[T]):
        if not issubclass(model, Document):
            raise ValueError("model must be a Beanie Document")
        self.model = model

    def _sort_by_created_at(self, documents: List[T], descending: bool = True) -> List[T]:
        return sorted(documents, key=lambda doc: doc.created_at, reverse=descending)

    def _validate(self, raw:  Mapping[str, Any]) -> T:
        return self.model.model_validate(raw)

    def _get_collection(self) -> AsyncIOMotorCollection:
        return self.model.get_motor_collection()

    async def get_document_count(self) -> int:
        return await self._get_collection().count_documents({})

    async def create(self, data: Dict[str, Any]) -> T:
        data["created_at"] = now_in_luanda()
        data["updated_at"] = now_in_luanda()

        document = self.model(**data)
        return await document.insert()

    async def get_all(self) -> List[T]:
        documents = await self._get_collection().find().to_list()
        return [self._validate(doc) for doc in documents]

    async def get_many(self, ids: List[str]) -> List[T]:
        try:
            object_ids = [to_object_id(id) for id in ids]
            collection = self._get_collection()
            documents = await collection.find(
                {"_id": {"$in": object_ids}}
            ).to_list()
            return [self._validate(doc) for doc in documents]
        except Exception as error:
            print("Error trying to fetch it all")
            print(error)

    async def get(self, _id: str) -> Optional[T]:
        try:
            raw = await self._get_collection().find_one({"_id": ObjectId(_id)})
            if not raw:
                return None
            document = self._validate(raw)
            return document
        except Exception as e:
            print(f"❌ Failed to retrieve document by id {_id}: {e}")
            return None

    async def get_by_slug(self, slug: str, slug_field: str = "slug") -> Optional[T]:
        try:
            raw = await self.model.get_motor_collection().find_one({slug_field: slug})
            if not raw:
                return None
            return self.model.model_validate(raw)
        except Exception as e:
            print(f"❌ Failed to retrieve document by slug {slug}: {e}")
            return None

    async def get_by_fields(
            self, filters: Dict[str, Any] | LogicalOperatorForListOfExpressions, skip: int = 0, limit: int = 100
    ) -> List[T]:
        documents = await self._get_collection().find(filters).skip(skip).limit(limit).to_list()
        return [self._validate(doc) for doc in documents]

    async def update(self, _id: str, data: Dict[str, Any]) -> Optional[T]:
        collection = self._get_collection()

        # Optional: ensure updated_at is applied
        if "updated_at" in self.model.model_fields:
            data["updatedAt"] = now_in_luanda()

        result = await collection.update_one(
            {"_id": ObjectId(_id)},
            {"$set": data}
        )

        if result.matched_count == 0:
            return None

        # Return the updated document
        updated_doc = await self.get(_id)
        return updated_doc


    async def delete(self, _id: str) -> bool:
        document = await self.get(_id)
        if document:
            await self._get_collection().delete_one({"_id": ObjectId(_id)})
            return True
        return False

    async def paginate(self,
                       filters: Dict[str, Any],
                       limit: int = 10,
                       cursor: Optional[str] = None,
                       descending: bool = False) -> PaginationResult[T]:

        query = filters.copy()

        sort_direction = -1 if descending else 1

        if cursor:
            query["_id"] = {'$lt' if descending else '$gt': ObjectId(cursor)}

        collection = self._get_collection()

        raw = await collection.find(query).sort({"_id": sort_direction}).limit(limit + 1).to_list()

        documents = [self._validate(doc) for doc in raw]

        items = documents[:limit]

        has_more = len(documents) > limit

        next_cursor = str(items[-1].id) if has_more else None

        total_count = await self.model.find(filters).count()

        return PaginationResult[T](
            items=items,
            next_cursor=next_cursor,
            totalCount=total_count,
            hasMore=has_more
        )
