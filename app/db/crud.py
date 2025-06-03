from beanie import Document, PydanticObjectId
from bson import ObjectId
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union
from datetime import datetime


from app.core.dependencies import get_mongo
from app.schema.collection_id.object_id import PyObjectId

T = TypeVar("T", bound=Document)

def to_object_id(_id: str) -> PydanticObjectId:
    try:
        _id = PydanticObjectId(
            ObjectId(_id)
        )
        return _id
    except:
        raise ValueError("Invalid ObjectId")



class MongoCrud(Generic[T]):

    def __init__(self, model: Type[T]):
        if not issubclass(model, Document):
            raise ValueError("model must be a Beanie Document")
        self.model = model


    async def create(self, data: Dict[str, Any]) -> T:
        data["created_at"] = datetime.now()
        data["updated_at"] = datetime.now()

        document = self.model(**data)
        return await document.insert()

    async def get_all(self) -> List[T]:
        return await self.model.find().to_list()

    async def get_many(self, ids: List[str]) -> List[T]:
        object_ids = [to_object_id(id) for id in ids]
        return await self.model.find(
            self.model.id.in_(object_ids)
        ).to_list()

    async def get(self, _id: str) -> Optional[T]:
        try:
            raw = await self.model.get_motor_collection().find_one({"_id": ObjectId(_id)})
            if not raw:
                return None
            document = self.model.model_validate(raw)
            return document
        except Exception as e:
            print(f"❌ Failed to retrieve document by id {_id}: {e}")
            return None

    async def get_by_fields(
            self, filters: Dict[str, Any], skip: int = 0, limit: int = 10
    ) -> List[T]:
        return await self.model.find(filters).skip(skip).limit(limit).to_list()

    async def update(self, _id: str, data: Dict[str, Any]) -> Optional[T]:
        collection = self.model.get_motor_collection()

        # Optional: ensure updated_at is applied
        if "updated_at" in self.model.model_fields:
            data["updatedAt"] = datetime.now()

        result = await collection.update_one(
            {"_id": ObjectId(_id)},
            {"$set": data}
        )

        if result.matched_count == 0:
            return None

        # Return the updated document
        updated_doc = await self.get(_id)
        print("UPDATED DOCUMENT:", updated_doc)
        return updated_doc


    async def delete(self, _id: str) -> bool:
        document = await self.model.get(_id)
        if document:
            await document.delete()
            return True
        return False

    async def paginate(self, filters: Dict[str, Any], skip: int = 0, limit: int = 10, cursor: Optional[Union[str, datetime]] = None) -> Dict[str, Any]:
        query = filters.copy()

        if cursor:
            if isinstance(cursor, str):  # If using `_id` for pagination
                query["_id"] = {"$gt": cursor}
            elif isinstance(cursor, datetime):  # If using `created_at` for pagination
                query["created_at"] = {"$gt": cursor}

        documents = await self.model.find(query).sort("created_at").skip(skip).limit(limit).to_list()

        next_cursor = None
        if documents:
            next_cursor = documents[-1].created_at  # Use `created_at` as the cursor

        total_count = await self.model.find(filters).count()

        return {
            "items": documents,
            "next_cursor": next_cursor,
            "total_count": total_count,
        }

