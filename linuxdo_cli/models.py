from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class Topic(BaseModel):
    id: int
    title: str
    fancy_title: Optional[str] = None
    slug: str
    posts_count: int
    reply_count: int
    highest_post_number: int
    image_url: Optional[str] = None
    created_at: datetime
    last_posted_at: datetime
    bumped: bool
    bumped_at: datetime
    archetype: str
    unseen: bool
    pinned: bool
    unpinned: Optional[bool] = None
    visible: bool
    closed: bool
    archived: bool
    bookmarked: Optional[bool] = None
    liked: Optional[bool] = None
    views: int
    like_count: int
    has_summary: bool
    last_poster_username: str
    category_id: int
    pinned_globally: bool

class TopicList(BaseModel):
    topics: List[Topic]
    more_topics_url: Optional[str] = None

class LatestTopicsResponse(BaseModel):
    topic_list: TopicList

class TopicDetail(BaseModel):
    id: int
    title: str
    fancy_title: Optional[str] = None
    posts_count: int
    created_at: datetime
    views: int
    like_count: int
    last_posted_at: datetime
    post_stream: dict
    category_id: int
