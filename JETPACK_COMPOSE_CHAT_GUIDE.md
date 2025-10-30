# Building a Chat App with Jetpack Compose

This guide will help you learn how to build a chatting app using Jetpack Compose for Android that integrates with this FastAPI backend.

## Backend API Overview

This FastAPI backend provides a complete chat/messaging system with the following features:

### Features
- User authentication (JWT tokens)
- Create and manage chat rooms (direct messages and group chats)
- Send and receive messages
- Real-time messaging via WebSocket
- Message read status tracking
- Pagination support for message history

## API Endpoints

### Authentication
- `POST /login` - Login and get JWT token

### Chat Rooms
- `POST /chat/rooms` - Create a new chat room
- `GET /chat/rooms` - Get all chat rooms for current user
- `GET /chat/rooms/{id}` - Get specific chat room details

### Messages
- `POST /chat/messages` - Send a message
- `GET /chat/rooms/{id}/messages` - Get messages from a chat room (with pagination)
- `PUT /chat/rooms/{id}/read` - Mark all messages as read

### WebSocket
- `WS /chat/ws/{chat_room_id}?token={jwt_token}` - Real-time chat connection

## Jetpack Compose Implementation Guide

### Step 1: Project Setup

Add dependencies to your `build.gradle` (app level):

```gradle
dependencies {
    // Jetpack Compose
    implementation "androidx.compose.ui:ui:1.5.4"
    implementation "androidx.compose.material3:material3:1.1.2"
    implementation "androidx.compose.ui:ui-tooling-preview:1.5.4"
    implementation "androidx.activity:activity-compose:1.8.0"
    
    // ViewModel
    implementation "androidx.lifecycle:lifecycle-viewmodel-compose:2.6.2"
    implementation "androidx.lifecycle:lifecycle-runtime-compose:2.6.2"
    
    // Networking
    implementation "com.squareup.retrofit2:retrofit:2.9.0"
    implementation "com.squareup.retrofit2:converter-gson:2.9.0"
    implementation "com.squareup.okhttp3:okhttp:4.12.0"
    implementation "com.squareup.okhttp3:logging-interceptor:4.12.0"
    
    // WebSocket
    implementation "com.squareup.okhttp3:okhttp:4.12.0"
    
    // Coroutines
    implementation "org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3"
    
    // Navigation
    implementation "androidx.navigation:navigation-compose:2.7.5"
    
    // Data Store (for token storage)
    implementation "androidx.datastore:datastore-preferences:1.0.0"
}
```

### Step 2: Create Data Models

```kotlin
// ChatModels.kt
data class User(
    val id: Int,
    val name: String,
    val email: String
)

data class ChatRoom(
    val id: Int,
    val name: String?,
    val is_group: Boolean,
    val created_at: String
)

data class Message(
    val id: Int,
    val content: String,
    val sender_id: Int,
    val chat_room_id: Int,
    val created_at: String,
    val is_read: Boolean
)

data class MessageCreate(
    val content: String,
    val chat_room_id: Int
)

data class ChatRoomCreate(
    val name: String?,
    val is_group: Boolean,
    val member_ids: List<Int>
)

data class LoginRequest(
    val username: String,
    val password: String
)

data class LoginResponse(
    val access_token: String,
    val token_type: String
)

data class WebSocketMessage(
    val type: String, // "message", "join", "leave", "typing"
    val id: Int? = null,
    val content: String? = null,
    val sender_id: Int? = null,
    val chat_room_id: Int? = null,
    val created_at: String? = null,
    val is_read: Boolean? = null
)
```

### Step 3: Create API Service

```kotlin
// ApiService.kt
import retrofit2.Response
import retrofit2.http.*

interface ChatApiService {
    
    @POST("login")
    @FormUrlEncoded
    suspend fun login(
        @Field("username") username: String,
        @Field("password") password: String
    ): Response<LoginResponse>
    
    @POST("chat/rooms")
    suspend fun createChatRoom(
        @Header("Authorization") token: String,
        @Body chatRoom: ChatRoomCreate
    ): Response<ChatRoom>
    
    @GET("chat/rooms")
    suspend fun getChatRooms(
        @Header("Authorization") token: String
    ): Response<List<ChatRoom>>
    
    @GET("chat/rooms/{id}")
    suspend fun getChatRoom(
        @Header("Authorization") token: String,
        @Path("id") roomId: Int
    ): Response<ChatRoom>
    
    @POST("chat/messages")
    suspend fun sendMessage(
        @Header("Authorization") token: String,
        @Body message: MessageCreate
    ): Response<Message>
    
    @GET("chat/rooms/{id}/messages")
    suspend fun getMessages(
        @Header("Authorization") token: String,
        @Path("id") roomId: Int,
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0
    ): Response<List<Message>>
    
    @PUT("chat/rooms/{id}/read")
    suspend fun markAsRead(
        @Header("Authorization") token: String,
        @Path("id") roomId: Int
    ): Response<Map<String, String>>
}
```

### Step 4: Setup Retrofit

```kotlin
// NetworkModule.kt
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object NetworkModule {
    private const val BASE_URL = "http://your-server-ip:8000/"
    
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }
    
    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    val apiService: ChatApiService = retrofit.create(ChatApiService::class.java)
}
```

### Step 5: Create WebSocket Manager

```kotlin
// WebSocketManager.kt
import com.google.gson.Gson
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import okhttp3.*
import okio.ByteString

class WebSocketManager(private val token: String) {
    private var webSocket: WebSocket? = null
    private val gson = Gson()
    
    private val _messages = MutableStateFlow<WebSocketMessage?>(null)
    val messages: StateFlow<WebSocketMessage?> = _messages
    
    private val _connectionState = MutableStateFlow(false)
    val connectionState: StateFlow<Boolean> = _connectionState
    
    fun connect(chatRoomId: Int) {
        val client = OkHttpClient()
        val wsUrl = "ws://your-server-ip:8000/chat/ws/$chatRoomId?token=$token"
        
        val request = Request.Builder()
            .url(wsUrl)
            .build()
        
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                _connectionState.value = true
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                val message = gson.fromJson(text, WebSocketMessage::class.java)
                _messages.value = message
            }
            
            override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                // Handle binary messages if needed
            }
            
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(1000, null)
                _connectionState.value = false
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                _connectionState.value = false
            }
        })
    }
    
    fun sendMessage(content: String, chatRoomId: Int, senderId: Int) {
        val message = mapOf(
            "type" to "message",
            "content" to content,
            "chat_room_id" to chatRoomId,
            "sender_id" to senderId
        )
        webSocket?.send(gson.toJson(message))
    }
    
    fun sendTyping(chatRoomId: Int, senderId: Int) {
        val message = mapOf(
            "type" to "typing",
            "chat_room_id" to chatRoomId,
            "sender_id" to senderId
        )
        webSocket?.send(gson.toJson(message))
    }
    
    fun disconnect() {
        webSocket?.close(1000, "Closing connection")
        webSocket = null
        _connectionState.value = false
    }
}
```

### Step 6: Create Repository

```kotlin
// ChatRepository.kt
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class ChatRepository(private val apiService: ChatApiService) {
    
    suspend fun login(username: String, password: String): Result<LoginResponse> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.login(username, password)
                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!)
                } else {
                    Result.failure(Exception("Login failed: ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    suspend fun getChatRooms(token: String): Result<List<ChatRoom>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getChatRooms("Bearer $token")
                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!)
                } else {
                    Result.failure(Exception("Failed to get chat rooms"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    suspend fun getMessages(token: String, roomId: Int, limit: Int = 50, offset: Int = 0): Result<List<Message>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getMessages("Bearer $token", roomId, limit, offset)
                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!)
                } else {
                    Result.failure(Exception("Failed to get messages"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    suspend fun sendMessage(token: String, content: String, chatRoomId: Int): Result<Message> {
        return withContext(Dispatchers.IO) {
            try {
                val messageCreate = MessageCreate(content, chatRoomId)
                val response = apiService.sendMessage("Bearer $token", messageCreate)
                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!)
                } else {
                    Result.failure(Exception("Failed to send message"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    suspend fun createChatRoom(token: String, name: String?, isGroup: Boolean, memberIds: List<Int>): Result<ChatRoom> {
        return withContext(Dispatchers.IO) {
            try {
                val chatRoomCreate = ChatRoomCreate(name, isGroup, memberIds)
                val response = apiService.createChatRoom("Bearer $token", chatRoomCreate)
                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!)
                } else {
                    Result.failure(Exception("Failed to create chat room"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
}
```

### Step 7: Create ViewModel

```kotlin
// ChatViewModel.kt
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

class ChatViewModel(
    private val repository: ChatRepository,
    private val token: String
) : ViewModel() {
    
    private val _chatRooms = MutableStateFlow<List<ChatRoom>>(emptyList())
    val chatRooms: StateFlow<List<ChatRoom>> = _chatRooms
    
    private val _messages = MutableStateFlow<List<Message>>(emptyList())
    val messages: StateFlow<List<Message>> = _messages
    
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading
    
    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error
    
    private var webSocketManager: WebSocketManager? = null
    val wsMessages: StateFlow<WebSocketMessage?> get() = webSocketManager?.messages ?: MutableStateFlow(null)
    val wsConnectionState: StateFlow<Boolean> get() = webSocketManager?.connectionState ?: MutableStateFlow(false)
    
    fun loadChatRooms() {
        viewModelScope.launch {
            _isLoading.value = true
            repository.getChatRooms(token).fold(
                onSuccess = { rooms ->
                    _chatRooms.value = rooms
                    _isLoading.value = false
                },
                onFailure = { error ->
                    _error.value = error.message
                    _isLoading.value = false
                }
            )
        }
    }
    
    fun loadMessages(chatRoomId: Int) {
        viewModelScope.launch {
            _isLoading.value = true
            repository.getMessages(token, chatRoomId).fold(
                onSuccess = { msgs ->
                    _messages.value = msgs
                    _isLoading.value = false
                },
                onFailure = { error ->
                    _error.value = error.message
                    _isLoading.value = false
                }
            )
        }
    }
    
    fun sendMessage(content: String, chatRoomId: Int) {
        viewModelScope.launch {
            repository.sendMessage(token, content, chatRoomId).fold(
                onSuccess = { message ->
                    // Message sent successfully
                    _messages.value = _messages.value + message
                },
                onFailure = { error ->
                    _error.value = error.message
                }
            )
        }
    }
    
    fun connectWebSocket(chatRoomId: Int) {
        webSocketManager = WebSocketManager(token)
        webSocketManager?.connect(chatRoomId)
        
        // Collect WebSocket messages and add to local messages list
        viewModelScope.launch {
            wsMessages.collect { wsMessage ->
                wsMessage?.let {
                    if (it.type == "message" && it.id != null) {
                        val message = Message(
                            id = it.id,
                            content = it.content ?: "",
                            sender_id = it.sender_id ?: 0,
                            chat_room_id = it.chat_room_id ?: 0,
                            created_at = it.created_at ?: "",
                            is_read = it.is_read ?: false
                        )
                        // Add to messages if not already present
                        if (_messages.value.none { msg -> msg.id == message.id }) {
                            _messages.value = _messages.value + message
                        }
                    }
                }
            }
        }
    }
    
    fun disconnectWebSocket() {
        webSocketManager?.disconnect()
        webSocketManager = null
    }
    
    override fun onCleared() {
        super.onCleared()
        disconnectWebSocket()
    }
}
```

### Step 8: Create UI Screens

```kotlin
// ChatListScreen.kt
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatListScreen(
    viewModel: ChatViewModel,
    onChatRoomClick: (Int) -> Unit
) {
    val chatRooms by viewModel.chatRooms.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    
    LaunchedEffect(Unit) {
        viewModel.loadChatRooms()
    }
    
    Scaffold(
        topBar = {
            TopAppBar(title = { Text("Chats") })
        }
    ) { paddingValues ->
        Box(modifier = Modifier.padding(paddingValues)) {
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier
                        .fillMaxSize()
                        .wrapContentSize()
                )
            } else {
                LazyColumn {
                    items(chatRooms) { chatRoom ->
                        ChatRoomItem(
                            chatRoom = chatRoom,
                            onClick = { onChatRoomClick(chatRoom.id) }
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun ChatRoomItem(chatRoom: ChatRoom, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp)
            .clickable(onClick = onClick)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = chatRoom.name ?: "Direct Message",
                style = MaterialTheme.typography.titleMedium
            )
            Text(
                text = if (chatRoom.is_group) "Group Chat" else "Direct Message",
                style = MaterialTheme.typography.bodySmall
            )
        }
    }
}
```

```kotlin
// ChatScreen.kt
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    viewModel: ChatViewModel,
    chatRoomId: Int,
    currentUserId: Int,
    onBackClick: () -> Unit
) {
    val messages by viewModel.messages.collectAsState()
    val isConnected by viewModel.wsConnectionState.collectAsState()
    var messageText by remember { mutableStateOf("") }
    val listState = rememberLazyListState()
    
    LaunchedEffect(chatRoomId) {
        viewModel.loadMessages(chatRoomId)
        viewModel.connectWebSocket(chatRoomId)
    }
    
    // Auto-scroll to bottom when new messages arrive
    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(messages.size - 1)
        }
    }
    
    DisposableEffect(Unit) {
        onDispose {
            viewModel.disconnectWebSocket()
        }
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Column {
                        Text("Chat")
                        if (isConnected) {
                            Text(
                                "Connected",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, "Back")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .padding(paddingValues)
                .fillMaxSize()
        ) {
            // Messages list
            LazyColumn(
                state = listState,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                contentPadding = PaddingValues(8.dp)
            ) {
                items(messages) { message ->
                    MessageBubble(
                        message = message,
                        isCurrentUser = message.sender_id == currentUserId
                    )
                }
            }
            
            // Message input
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = messageText,
                    onValueChange = { messageText = it },
                    modifier = Modifier.weight(1f),
                    placeholder = { Text("Type a message...") }
                )
                
                Spacer(modifier = Modifier.width(8.dp))
                
                IconButton(
                    onClick = {
                        if (messageText.isNotBlank()) {
                            viewModel.sendMessage(messageText, chatRoomId)
                            messageText = ""
                        }
                    },
                    enabled = messageText.isNotBlank()
                ) {
                    Icon(Icons.Default.Send, "Send")
                }
            }
        }
    }
}

@Composable
fun MessageBubble(message: Message, isCurrentUser: Boolean) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = if (isCurrentUser) Arrangement.End else Arrangement.Start
    ) {
        Card(
            colors = CardDefaults.cardColors(
                containerColor = if (isCurrentUser) 
                    MaterialTheme.colorScheme.primary 
                else 
                    MaterialTheme.colorScheme.surfaceVariant
            )
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    text = message.content,
                    color = if (isCurrentUser) 
                        MaterialTheme.colorScheme.onPrimary 
                    else 
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = message.created_at.substring(11, 16), // Show time
                    style = MaterialTheme.typography.bodySmall,
                    color = if (isCurrentUser) 
                        MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.7f)
                    else 
                        MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                )
            }
        }
    }
}
```

### Step 9: Setup Navigation

```kotlin
// Navigation.kt
import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument

@Composable
fun ChatAppNavigation(viewModel: ChatViewModel, currentUserId: Int) {
    val navController = rememberNavController()
    
    NavHost(navController = navController, startDestination = "chat_list") {
        composable("chat_list") {
            ChatListScreen(
                viewModel = viewModel,
                onChatRoomClick = { chatRoomId ->
                    navController.navigate("chat/$chatRoomId")
                }
            )
        }
        
        composable(
            route = "chat/{chatRoomId}",
            arguments = listOf(navArgument("chatRoomId") { type = NavType.IntType })
        ) { backStackEntry ->
            val chatRoomId = backStackEntry.arguments?.getInt("chatRoomId") ?: 0
            ChatScreen(
                viewModel = viewModel,
                chatRoomId = chatRoomId,
                currentUserId = currentUserId,
                onBackClick = { navController.popBackStack() }
            )
        }
    }
}
```

## Testing the Integration

### 1. Start the Backend Server
```bash
cd /home/runner/work/blog-api/blog-api
python3 -m uvicorn blog.main:app --host 0.0.0.0 --port 8000
```

### 2. Create Test Users
Use the API or a tool like Postman to create test users:
```bash
curl -X POST "http://localhost:8000/user/" \
  -H "Content-Type: application/json" \
  -d '{"name":"User1","email":"user1@test.com","password":"password123"}'
```

### 3. Login and Get Token
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1@test.com&password=password123"
```

### 4. Test Chat Endpoints
Create a chat room:
```bash
curl -X POST "http://localhost:8000/chat/rooms" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Chat","is_group":false,"member_ids":[2]}'
```

Send a message:
```bash
curl -X POST "http://localhost:8000/chat/messages" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello!","chat_room_id":1}'
```

## Key Concepts to Learn

### 1. **State Management in Jetpack Compose**
- Using `StateFlow` for reactive data
- `collectAsState()` to observe state in Compose
- ViewModel lifecycle management

### 2. **Networking**
- Retrofit for REST API calls
- OkHttp for WebSocket connections
- Coroutines for async operations

### 3. **Real-time Communication**
- WebSocket connections for instant messaging
- Handling connection states
- Broadcasting messages to multiple clients

### 4. **UI/UX Best Practices**
- Message bubbles with sender/receiver distinction
- Auto-scrolling to new messages
- Loading states and error handling
- Connection status indicators

### 5. **Authentication**
- JWT token storage (use DataStore or EncryptedSharedPreferences)
- Token refresh mechanisms
- Secure credential handling

## Next Steps

1. **Add more features:**
   - Image/file sharing
   - Voice messages
   - Message reactions
   - User typing indicators
   - Message search

2. **Improve UX:**
   - Pull-to-refresh for message history
   - Offline message queue
   - Push notifications
   - Read receipts

3. **Security:**
   - End-to-end encryption
   - Message deletion
   - User blocking
   - Report functionality

4. **Testing:**
   - Unit tests for ViewModels and Repositories
   - UI tests with Compose Testing
   - Integration tests for API calls

## Resources

- [Jetpack Compose Documentation](https://developer.android.com/jetpack/compose)
- [Retrofit Documentation](https://square.github.io/retrofit/)
- [WebSocket with OkHttp](https://square.github.io/okhttp/4.x/okhttp/okhttp3/-web-socket/)
- [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-overview.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Conclusion

This guide provides a complete foundation for building a chat app with Jetpack Compose. The backend API handles authentication, message storage, and real-time communication, while the Android app provides a modern, reactive UI using Compose.

Start by implementing the basic features (login, chat list, and messaging) and gradually add more advanced features as you become comfortable with the architecture.
