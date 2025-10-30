from .database import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime


class Blog(Base):
    __tablename__ = 'blogs'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    body = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))  # Foreign key to link to User table

    creator = relationship("User", back_populates="blogs")
   

class User(Base):
    # User model representing a user in the database
    # 
    # This model defines the structure for storing user information including
    # authentication credentials and basic profile data.
    #
    # Attributes:
    #     id (int): Primary key, auto-incrementing unique identifier for the user
    #     name (str): User's display name
    #     email (str): User's email address, must be unique across all users
    #     password (str): User's hashed password for authentication
    #
    # Table: users
    # Indexes: id (primary), email (unique)
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    blogs = relationship("Blog", back_populates="creator")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    chat_rooms = relationship("ChatRoom", secondary="chat_room_members", back_populates="members")


class ChatRoom(Base):
    """
    ChatRoom model representing a chat room in the database.
    
    A chat room can be a direct message (1-on-1) or a group chat (multiple users).
    
    Attributes:
        id (int): Primary key, auto-incrementing unique identifier for the chat room
        name (str): Optional name for the chat room (mainly for group chats)
        is_group (bool): Whether this is a group chat or direct message
        created_at (datetime): Timestamp when the chat room was created
    
    Table: chat_rooms
    Indexes: id (primary)
    """
    __tablename__ = 'chat_rooms'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    is_group = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    messages = relationship("Message", back_populates="chat_room", cascade="all, delete-orphan")
    members = relationship("User", secondary="chat_room_members", back_populates="chat_rooms")


class ChatRoomMember(Base):
    """
    Association table for many-to-many relationship between ChatRoom and User.
    
    Attributes:
        id (int): Primary key
        chat_room_id (int): Foreign key to chat_rooms table
        user_id (int): Foreign key to users table
        joined_at (datetime): Timestamp when user joined the chat room
    
    Table: chat_room_members
    """
    __tablename__ = 'chat_room_members'
    id = Column(Integer, primary_key=True, index=True)
    chat_room_id = Column(Integer, ForeignKey("chat_rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)


class Message(Base):
    """
    Message model representing a chat message in the database.
    
    Attributes:
        id (int): Primary key, auto-incrementing unique identifier for the message
        content (str): The text content of the message
        sender_id (int): Foreign key to the user who sent the message
        chat_room_id (int): Foreign key to the chat room where message was sent
        created_at (datetime): Timestamp when the message was created
        is_read (bool): Whether the message has been read
    
    Table: messages
    Indexes: id (primary), sender_id, chat_room_id
    """
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chat_room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_read = Column(Boolean, default=False)
    
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    chat_room = relationship("ChatRoom", back_populates="messages")