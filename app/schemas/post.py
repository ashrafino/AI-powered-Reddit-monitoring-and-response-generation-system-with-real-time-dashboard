from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AIResponseOut(BaseModel):
    id: int
    post_id: int
    client_id: int
    content: str
    score: int
    copied: bool
    compliance_ack: bool
    created_at: datetime

    class Config:
        from_attributes = True

class MatchedPostOut(BaseModel):
    id: int
    client_id: int
    subreddit: str
    reddit_post_id: str
    title: str
    url: str
    author: str
    content: Optional[str] = None
    keywords_matched: Optional[str] = None
    score: Optional[int] = 0
    num_comments: Optional[int] = 0
    flagged: bool
    reviewed: bool
    created_at: datetime
    responses: List[AIResponseOut] = []

    class Config:
        from_attributes = True



