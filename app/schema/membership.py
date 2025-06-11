from pydantic import BaseModel, Field

class MembershipCreate(BaseModel):
    user_id: str = Field(..., alias="userId")
    role_id: str = Field(..., alias="roleId")

class MembershipUpdate(BaseModel):
    role_id: str = Field(..., alias="roleId")
