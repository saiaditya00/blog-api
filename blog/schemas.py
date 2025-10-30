from pydantic import BaseModel
from typing import Optional, List, ForwardRef
from datetime import datetime

class BlogBase(BaseModel):
    title: str
    body: str

class Blog(BlogBase):
    class Config:
        orm_mode = True

class User(BaseModel):
    name: str
    email: str
    password: str   

class ShowUser(BaseModel):
    name: str
    email: str
    blogs: List['Blog'] = []
    class Config:
        orm_mode = True

class ShowBlog(BaseModel):
    title: str
    body: str
    creator: ShowUser
    class Config:
        orm_mode = True


class Login(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


# Chat Schemas
class MessageCreate(BaseModel):
    """Schema for creating a new message"""
    content: str
    chat_room_id: int


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: int
    content: str
    sender_id: int
    chat_room_id: int
    created_at: datetime
    is_read: bool
    
    class Config:
        orm_mode = True


class ChatRoomCreate(BaseModel):
    """Schema for creating a new chat room"""
    name: Optional[str] = None
    is_group: bool = False
    member_ids: List[int]  # List of user IDs to add to the chat room


class ChatRoomResponse(BaseModel):
    """Schema for chat room response"""
    id: int
    name: Optional[str] = None
    is_group: bool
    created_at: datetime
    
    class Config:
        orm_mode = True


class ChatRoomWithMessages(BaseModel):
    """Schema for chat room with messages"""
    id: int
    name: Optional[str] = None
    is_group: bool
    created_at: datetime
    messages: List[MessageResponse] = []
    
    class Config:
        orm_mode = True


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""
    type: str  # "message", "join", "leave", "typing"
    content: Optional[str] = None
    chat_room_id: Optional[int] = None
    sender_id: Optional[int] = None
    timestamp: Optional[datetime] = None



