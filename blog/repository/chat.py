from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from datetime import datetime

from .. import models, schemas


def create_chat_room(db: Session, chat_room_data: schemas.ChatRoomCreate, current_user_id: int):
    """Create a new chat room and add members"""
    # Create the chat room
    new_chat_room = models.ChatRoom(
        name=chat_room_data.name,
        is_group=chat_room_data.is_group
    )
    db.add(new_chat_room)
    db.flush()  # Flush to get the ID
    
    # Add current user as a member
    member_ids = set(chat_room_data.member_ids)
    member_ids.add(current_user_id)
    
    # Add all members
    for user_id in member_ids:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        member = models.ChatRoomMember(
            chat_room_id=new_chat_room.id,
            user_id=user_id
        )
        db.add(member)
    
    db.commit()
    db.refresh(new_chat_room)
    return new_chat_room


def get_user_chat_rooms(db: Session, user_id: int):
    """Get all chat rooms for a user"""
    chat_rooms = db.query(models.ChatRoom).join(
        models.ChatRoomMember
    ).filter(
        models.ChatRoomMember.user_id == user_id
    ).all()
    return chat_rooms


def get_chat_room(db: Session, chat_room_id: int, user_id: int):
    """Get a specific chat room with validation that user is a member"""
    # Check if user is a member of the chat room
    membership = db.query(models.ChatRoomMember).filter(
        models.ChatRoomMember.chat_room_id == chat_room_id,
        models.ChatRoomMember.user_id == user_id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat room"
        )
    
    chat_room = db.query(models.ChatRoom).filter(
        models.ChatRoom.id == chat_room_id
    ).first()
    
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat room with id {chat_room_id} not found"
        )
    
    return chat_room


def create_message(db: Session, message_data: schemas.MessageCreate, sender_id: int):
    """Create a new message in a chat room"""
    # Verify user is a member of the chat room
    membership = db.query(models.ChatRoomMember).filter(
        models.ChatRoomMember.chat_room_id == message_data.chat_room_id,
        models.ChatRoomMember.user_id == sender_id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat room"
        )
    
    # Create the message
    new_message = models.Message(
        content=message_data.content,
        sender_id=sender_id,
        chat_room_id=message_data.chat_room_id
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


def get_chat_room_messages(db: Session, chat_room_id: int, user_id: int, limit: int = 50, offset: int = 0):
    """Get messages from a chat room with pagination"""
    # Verify user is a member
    membership = db.query(models.ChatRoomMember).filter(
        models.ChatRoomMember.chat_room_id == chat_room_id,
        models.ChatRoomMember.user_id == user_id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat room"
        )
    
    messages = db.query(models.Message).filter(
        models.Message.chat_room_id == chat_room_id
    ).order_by(
        models.Message.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    # Reverse to get chronological order
    return list(reversed(messages))


def mark_messages_as_read(db: Session, chat_room_id: int, user_id: int):
    """Mark all messages in a chat room as read for the current user"""
    # Verify user is a member
    membership = db.query(models.ChatRoomMember).filter(
        models.ChatRoomMember.chat_room_id == chat_room_id,
        models.ChatRoomMember.user_id == user_id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat room"
        )
    
    # Mark messages as read (excluding messages sent by the user)
    db.query(models.Message).filter(
        models.Message.chat_room_id == chat_room_id,
        models.Message.sender_id != user_id,
        models.Message.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    return {"message": "Messages marked as read"}
