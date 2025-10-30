from fastapi import APIRouter, status, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime

from .. import schemas, database, oauth2, models
from ..repository import chat

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

# Get database dependency
get_db = database.get_db


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        # Store active connections by chat_room_id
        self.active_connections: dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, chat_room_id: int):
        await websocket.accept()
        if chat_room_id not in self.active_connections:
            self.active_connections[chat_room_id] = []
        self.active_connections[chat_room_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, chat_room_id: int):
        if chat_room_id in self.active_connections:
            if websocket in self.active_connections[chat_room_id]:
                self.active_connections[chat_room_id].remove(websocket)
            if not self.active_connections[chat_room_id]:
                del self.active_connections[chat_room_id]
    
    async def broadcast_to_room(self, message: dict, chat_room_id: int):
        if chat_room_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[chat_room_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.disconnect(conn, chat_room_id)


manager = ConnectionManager()


# REST API Endpoints

@router.post("/rooms", status_code=status.HTTP_201_CREATED, response_model=schemas.ChatRoomResponse)
def create_chat_room(
    request: schemas.ChatRoomCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Create a new chat room"""
    return chat.create_chat_room(db, request, current_user.id)


@router.get("/rooms", response_model=List[schemas.ChatRoomResponse])
def get_chat_rooms(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Get all chat rooms for the current user"""
    return chat.get_user_chat_rooms(db, current_user.id)


@router.get("/rooms/{chat_room_id}", response_model=schemas.ChatRoomResponse)
def get_chat_room(
    chat_room_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Get a specific chat room"""
    return chat.get_chat_room(db, chat_room_id, current_user.id)


@router.post("/messages", status_code=status.HTTP_201_CREATED, response_model=schemas.MessageResponse)
async def send_message(
    request: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Send a message to a chat room"""
    message = chat.create_message(db, request, current_user.id)
    
    # Broadcast to WebSocket connections in the room
    await manager.broadcast_to_room({
        "type": "message",
        "id": message.id,
        "content": message.content,
        "sender_id": message.sender_id,
        "chat_room_id": message.chat_room_id,
        "created_at": message.created_at.isoformat(),
        "is_read": message.is_read
    }, request.chat_room_id)
    
    return message


@router.get("/rooms/{chat_room_id}/messages", response_model=List[schemas.MessageResponse])
def get_messages(
    chat_room_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Get messages from a chat room with pagination"""
    return chat.get_chat_room_messages(db, chat_room_id, current_user.id, limit, offset)


@router.put("/rooms/{chat_room_id}/read", status_code=status.HTTP_200_OK)
def mark_as_read(
    chat_room_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Mark all messages in a chat room as read"""
    return chat.mark_messages_as_read(db, chat_room_id, current_user.id)


# WebSocket endpoint for real-time chat
@router.websocket("/ws/{chat_room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_room_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time chat
    
    Connect with: ws://host:port/chat/ws/{chat_room_id}?token={jwt_token}
    
    Message format:
    {
        "type": "message|typing|join|leave",
        "content": "message content",
        "sender_id": 1
    }
    """
    try:
        # Verify token and get user
        user = oauth2.get_current_user_from_token(token, db)
        
        # Verify user is a member of the chat room
        membership = db.query(models.ChatRoomMember).filter(
            models.ChatRoomMember.chat_room_id == chat_room_id,
            models.ChatRoomMember.user_id == user.id
        ).first()
        
        if not membership:
            await websocket.close(code=4003, reason="Not a member of this chat room")
            return
        
        # Accept connection
        await manager.connect(websocket, chat_room_id)
        
        # Send join notification
        await manager.broadcast_to_room({
            "type": "join",
            "sender_id": user.id,
            "chat_room_id": chat_room_id,
            "timestamp": datetime.utcnow().isoformat()
        }, chat_room_id)
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "message":
                # Save message to database
                message = chat.create_message(
                    db,
                    schemas.MessageCreate(
                        content=message_data.get("content"),
                        chat_room_id=chat_room_id
                    ),
                    user.id
                )
                
                # Broadcast to all connections in the room
                await manager.broadcast_to_room({
                    "type": "message",
                    "id": message.id,
                    "content": message.content,
                    "sender_id": message.sender_id,
                    "chat_room_id": message.chat_room_id,
                    "created_at": message.created_at.isoformat(),
                    "is_read": message.is_read
                }, chat_room_id)
            
            elif message_data.get("type") == "typing":
                # Broadcast typing indicator
                await manager.broadcast_to_room({
                    "type": "typing",
                    "sender_id": user.id,
                    "chat_room_id": chat_room_id,
                    "timestamp": datetime.utcnow().isoformat()
                }, chat_room_id)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_room_id)
        # Broadcast leave notification
        try:
            await manager.broadcast_to_room({
                "type": "leave",
                "sender_id": user.id,
                "chat_room_id": chat_room_id,
                "timestamp": datetime.utcnow().isoformat()
            }, chat_room_id)
        except:
            pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, chat_room_id)
        try:
            await websocket.close()
        except:
            pass
