from fastapi import FastAPI
from . import models, database
from .routers import blog, user, authentication, chat 
 


app = FastAPI()

# Create database tables
models.Base.metadata.create_all(bind=database.engine)   

# Include routers
app.include_router(blog.router)
app.include_router(user.router)
app.include_router(authentication.router)
app.include_router(chat.router)







