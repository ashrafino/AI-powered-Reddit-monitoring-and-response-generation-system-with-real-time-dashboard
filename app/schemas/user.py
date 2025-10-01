from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    role: Optional[str] = Field(default="client")

class UserCreate(UserBase):
    password: str
    client_name: Optional[str] = None
    create_client_if_missing: bool = True

class UserOut(UserBase):
    id: int
    client_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True



