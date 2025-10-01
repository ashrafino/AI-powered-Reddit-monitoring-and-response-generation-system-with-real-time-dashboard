from pydantic import BaseModel
from typing import Optional, List

class ClientConfigBase(BaseModel):
    reddit_username: Optional[str] = None
    reddit_subreddits: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    is_active: bool = True

class ClientConfigCreate(ClientConfigBase):
    client_id: int

class ClientConfigUpdate(ClientConfigBase):
    client_id: int | None = None

class ClientConfigOut(ClientConfigBase):
    id: int
    client_id: int

    class Config:
        from_attributes = True



