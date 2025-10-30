# Blog API with Chat Functionality

A FastAPI-based REST API for blog management and real-time chat/messaging, designed to be used with mobile applications (including Jetpack Compose Android apps).

## Features

### Blog Management
- User authentication with JWT tokens
- Create, read, update, and delete blog posts
- User profiles
- Author-blog relationships

### Chat/Messaging System
- Create chat rooms (direct messages and group chats)
- Send and receive messages
- Real-time messaging via WebSocket
- Message history with pagination
- Message read status tracking
- Member management for chat rooms

## Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **SQLite** - Database (easily replaceable with PostgreSQL/MySQL)
- **JWT** - Token-based authentication
- **WebSocket** - Real-time bidirectional communication
- **Pydantic** - Data validation using Python type annotations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/saiaditya00/blog-api.git
cd blog-api
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
uvicorn blog.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /login` - Login with username and password, returns JWT token

### Users
- `POST /user/` - Create a new user
- `GET /user/{id}` - Get user by ID

### Blogs
- `POST /blog/` - Create a new blog post
- `GET /blog/` - Get all blog posts
- `GET /blog/{id}` - Get blog post by ID
- `PUT /blog/{id}` - Update blog post
- `DELETE /blog/{id}` - Delete blog post

### Chat Rooms
- `POST /chat/rooms` - Create a new chat room
- `GET /chat/rooms` - Get all chat rooms for current user
- `GET /chat/rooms/{id}` - Get specific chat room

### Messages
- `POST /chat/messages` - Send a message to a chat room
- `GET /chat/rooms/{id}/messages` - Get messages from a chat room (with pagination)
- `PUT /chat/rooms/{id}/read` - Mark all messages as read in a chat room

### WebSocket
- `WS /chat/ws/{chat_room_id}?token={jwt_token}` - WebSocket endpoint for real-time chat

## WebSocket Usage

Connect to the WebSocket endpoint:
```
ws://localhost:8000/chat/ws/{chat_room_id}?token={your_jwt_token}
```

Send messages in JSON format:
```json
{
  "type": "message",
  "content": "Hello!",
  "sender_id": 1
}
```

Receive messages:
```json
{
  "type": "message",
  "id": 1,
  "content": "Hello!",
  "sender_id": 1,
  "chat_room_id": 1,
  "created_at": "2025-10-30T05:00:00",
  "is_read": false
}
```

Message types:
- `message` - Chat message
- `typing` - User typing indicator
- `join` - User joined the chat
- `leave` - User left the chat

## Building a Jetpack Compose App

See the comprehensive guide: [JETPACK_COMPOSE_CHAT_GUIDE.md](JETPACK_COMPOSE_CHAT_GUIDE.md)

This guide includes:
- Complete Jetpack Compose implementation
- Android project setup
- Data models and API service
- WebSocket integration
- UI components and screens
- ViewModel and Repository patterns
- Navigation setup
- Testing instructions

## Example Usage

### 1. Create a User
```bash
curl -X POST "http://localhost:8000/user/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword"
  }'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@example.com&password=securepassword"
```

### 3. Create a Chat Room
```bash
curl -X POST "http://localhost:8000/chat/rooms" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "General Discussion",
    "is_group": true,
    "member_ids": [1, 2, 3]
  }'
```

### 4. Send a Message
```bash
curl -X POST "http://localhost:8000/chat/messages" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello everyone!",
    "chat_room_id": 1
  }'
```

### 5. Get Messages
```bash
curl -X GET "http://localhost:8000/chat/rooms/1/messages?limit=50&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Database Schema

### Tables

**users**
- id (Primary Key)
- name
- email (Unique)
- password (Hashed)

**blogs**
- id (Primary Key)
- title
- body
- user_id (Foreign Key to users)

**chat_rooms**
- id (Primary Key)
- name (Optional, for group chats)
- is_group (Boolean)
- created_at (Timestamp)

**chat_room_members**
- id (Primary Key)
- chat_room_id (Foreign Key to chat_rooms)
- user_id (Foreign Key to users)
- joined_at (Timestamp)

**messages**
- id (Primary Key)
- content
- sender_id (Foreign Key to users)
- chat_room_id (Foreign Key to chat_rooms)
- created_at (Timestamp)
- is_read (Boolean)

## Project Structure

```
blog-api/
├── blog/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and router setup
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── token.py             # JWT token handling
│   ├── oauth2.py            # OAuth2 authentication
│   ├── hashing.py           # Password hashing utilities
│   ├── repository/          # Data access layer
│   │   ├── blog.py
│   │   ├── user.py
│   │   └── chat.py
│   └── routers/             # API endpoints
│       ├── blog.py
│       ├── user.py
│       ├── authentication.py
│       └── chat.py
├── requirements.txt
├── README.md
└── JETPACK_COMPOSE_CHAT_GUIDE.md
```

## Security Considerations

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- Token expiration (30 minutes by default)
- User authorization for chat room access
- SQL injection prevention via ORM

**Note:** The current `SECRET_KEY` in `token.py` is for development only. In production:
1. Use a strong, randomly generated secret key
2. Store it in environment variables
3. Never commit it to version control

## Development

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black blog/

# Lint
flake8 blog/
```

## Deployment

For production deployment:

1. Update the `SECRET_KEY` in environment variables
2. Use a production database (PostgreSQL recommended)
3. Set up HTTPS/WSS for secure connections
4. Configure CORS properly
5. Use a production ASGI server (Uvicorn with Gunicorn)
6. Set up proper logging and monitoring

Example production command:
```bash
gunicorn blog.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Roadmap

- [ ] Add file/image upload support
- [ ] Implement push notifications
- [ ] Add message reactions
- [ ] User presence/status indicators
- [ ] Message search functionality
- [ ] End-to-end encryption
- [ ] Voice/video call support
- [ ] Message editing and deletion
- [ ] User blocking and reporting

## Acknowledgments

- FastAPI for the excellent web framework
- SQLAlchemy for powerful ORM capabilities
- The Python community for amazing tools and libraries
