from sqlmodel import Field, SQLModel, JSON, Column, DATETIME
from datetime import datetime
from pydantic import BaseModel

class Video(SQLModel, table=True):
    """
    A video record to be saved in the database
    """
    id: str | None = Field(default=None, primary_key=True, index=True)
    title: str 
    channel_name: str
    duration: str  
    description: str | None = None
    category: str | None = None
    published_at: datetime = Field(sa_column=Column(DATETIME))
    view_count: int 
    thumbnail_link: str
    watched: bool = False
    liked: bool = False
    embeddings: list[float] | None = Field(default=None, sa_column=Column(JSON)) # JSON column should map to TEXT datatype in sqlite
    tags: list[str] | None = Field(default=None, sa_column=Column(JSON))

    #
    # class Config:
    #     arbitrary_types_allowed = True

class VideoData(BaseModel):
    """
    Validation model used for 'building' a Video object from incomplete data from API calls
    """
    id: str
    title: str
    channel_name: str
    description: str
    published_at: str    
    thumbnail_link: str
    duration: str | None = None
    view_count: int | None = None
    tags: list[str] | None = None
    category: str | None = None
