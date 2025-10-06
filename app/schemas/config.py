from pydantic import BaseModel
from typing import Optional, List

class ClientConfigBase(BaseModel):
    reddit_username: Optional[str] = None
    reddit_subreddits: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    is_active: bool = True
    
    # Scheduling fields
    scan_interval_minutes: Optional[int] = 5
    scan_start_hour: Optional[int] = 0
    scan_end_hour: Optional[int] = 23
    scan_days: Optional[str] = "1,2,3,4,5,6,7"

class ClientConfigCreate(ClientConfigBase):
    client_id: int

class ClientConfigUpdate(ClientConfigBase):
    client_id: int | None = None

class ClientConfigOut(ClientConfigBase):
    id: int
    client_id: int

    class Config:
        from_attributes = True



