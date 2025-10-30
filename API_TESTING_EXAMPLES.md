# API Testing Examples

This document provides quick examples for testing the Chat API.

## Setup

1. Start the server:
```bash
uvicorn blog.main:app --reload
```

2. The API will be available at: `http://localhost:8000`
3. Interactive API docs: `http://localhost:8000/docs`

## Step-by-Step Testing

### 1. Register Users

Register User 1:
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice",
    "email": "alice@example.com",
    "password": "password123"
  }'
```

Register User 2:
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bob",
    "email": "bob@example.com",
    "password": "password123"
  }'
```

### 2. Login and Get Token

Login as Alice:
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@example.com&password=password123"
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**Save the access_token for use in subsequent requests!**

### 3. Create a Chat Room

```bash
curl -X POST "http://localhost:8000/chat/rooms" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice & Bob Chat",
    "is_group": false,
    "member_ids": [2]
  }'
```

Response:
```json
{
  "id": 1,
  "name": "Alice & Bob Chat",
  "is_group": false,
  "created_at": "2025-10-30T05:00:00.000000"
}
```

### 4. Send Messages

Send first message:
```bash
curl -X POST "http://localhost:8000/chat/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hi Bob! How are you?",
    "chat_room_id": 1
  }'
```

Send another message:
```bash
curl -X POST "http://localhost:8000/chat/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This chat API is amazing!",
    "chat_room_id": 1
  }'
```

### 5. Get Messages

Get all messages from the chat room:
```bash
curl -X GET "http://localhost:8000/chat/rooms/1/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
[
  {
    "id": 1,
    "content": "Hi Bob! How are you?",
    "sender_id": 1,
    "chat_room_id": 1,
    "created_at": "2025-10-30T05:00:00.000000",
    "is_read": false
  },
  {
    "id": 2,
    "content": "This chat API is amazing!",
    "sender_id": 1,
    "chat_room_id": 1,
    "created_at": "2025-10-30T05:00:10.000000",
    "is_read": false
  }
]
```

### 6. Get All Chat Rooms

```bash
curl -X GET "http://localhost:8000/chat/rooms" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 7. Mark Messages as Read

Login as Bob and mark messages as read:
```bash
# First, login as Bob to get his token
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=bob@example.com&password=password123"

# Then mark messages as read
curl -X PUT "http://localhost:8000/chat/rooms/1/read" \
  -H "Authorization: Bearer BOB_ACCESS_TOKEN"
```

### 8. WebSocket Connection

For real-time messaging, connect to WebSocket:

**WebSocket URL:**
```
ws://localhost:8000/chat/ws/1?token=YOUR_ACCESS_TOKEN
```

**Send a message via WebSocket:**
```json
{
  "type": "message",
  "content": "Hello in real-time!",
  "sender_id": 1
}
```

**Receive messages:**
```json
{
  "type": "message",
  "id": 3,
  "content": "Hello in real-time!",
  "sender_id": 1,
  "chat_room_id": 1,
  "created_at": "2025-10-30T05:00:20.000000",
  "is_read": false
}
```

## Testing with Python

```python
import requests
import websocket
import json

BASE_URL = "http://localhost:8000"

# Register
response = requests.post(f"{BASE_URL}/register", json={
    "name": "Test User",
    "email": "test@example.com",
    "password": "password123"
})
print("User created:", response.json())

# Login
response = requests.post(f"{BASE_URL}/login", data={
    "username": "test@example.com",
    "password": "password123"
})
token = response.json()["access_token"]
print("Token:", token)

# Create chat room
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(f"{BASE_URL}/chat/rooms", headers=headers, json={
    "name": "Test Room",
    "is_group": False,
    "member_ids": [2]
})
room_id = response.json()["id"]
print("Chat room created:", room_id)

# Send message
response = requests.post(f"{BASE_URL}/chat/messages", headers=headers, json={
    "content": "Hello from Python!",
    "chat_room_id": room_id
})
print("Message sent:", response.json())

# Get messages
response = requests.get(f"{BASE_URL}/chat/rooms/{room_id}/messages", headers=headers)
print("Messages:", response.json())

# WebSocket connection
ws_url = f"ws://localhost:8000/chat/ws/{room_id}?token={token}"
ws = websocket.create_connection(ws_url)

# Send message via WebSocket
ws.send(json.dumps({
    "type": "message",
    "content": "WebSocket message!",
    "sender_id": 1
}))

# Receive message
result = ws.recv()
print("Received:", result)

ws.close()
```

## Testing with JavaScript/Node.js

```javascript
const fetch = require('node-fetch');
const WebSocket = require('ws');

const BASE_URL = 'http://localhost:8000';

async function testAPI() {
  // Register
  const registerResponse = await fetch(`${BASE_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'JS User',
      email: 'jsuser@example.com',
      password: 'password123'
    })
  });
  console.log('User created:', await registerResponse.json());

  // Login
  const loginResponse = await fetch(`${BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'username=jsuser@example.com&password=password123'
  });
  const { access_token } = await loginResponse.json();
  console.log('Token:', access_token);

  // Create chat room
  const roomResponse = await fetch(`${BASE_URL}/chat/rooms`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'JS Test Room',
      is_group: false,
      member_ids: [2]
    })
  });
  const { id: roomId } = await roomResponse.json();
  console.log('Room created:', roomId);

  // Send message
  const messageResponse = await fetch(`${BASE_URL}/chat/messages`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      content: 'Hello from JavaScript!',
      chat_room_id: roomId
    })
  });
  console.log('Message sent:', await messageResponse.json());

  // WebSocket
  const ws = new WebSocket(`ws://localhost:8000/chat/ws/${roomId}?token=${access_token}`);

  ws.on('open', () => {
    console.log('WebSocket connected');
    ws.send(JSON.stringify({
      type: 'message',
      content: 'WebSocket from JS!',
      sender_id: 1
    }));
  });

  ws.on('message', (data) => {
    console.log('Received:', JSON.parse(data));
  });
}

testAPI();
```

## Common Issues

### Authentication Error
**Problem:** `{"detail": "Not authenticated"}`
**Solution:** Make sure you include the `Authorization: Bearer YOUR_TOKEN` header

### WebSocket Connection Failed
**Problem:** WebSocket connection closes immediately
**Solution:** Verify the token is valid and not expired (tokens expire after 30 minutes)

### User Not Member of Chat Room
**Problem:** `{"detail": "You are not a member of this chat room"}`
**Solution:** Create a chat room with the user as a member, or ensure the user is added to the room

### Token Expired
**Problem:** `{"detail": "Could not validate credentials"}`
**Solution:** Login again to get a new token

## Next Steps

1. Test with your Jetpack Compose Android app
2. Implement real-time messaging with WebSocket
3. Add file upload capabilities
4. Implement push notifications
5. Add message search functionality

For more details, see [JETPACK_COMPOSE_CHAT_GUIDE.md](JETPACK_COMPOSE_CHAT_GUIDE.md)
