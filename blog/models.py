from .database import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship


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