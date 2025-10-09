from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from .. import models, schemas
from sqlalchemy.exc import IntegrityError
from ..hashing import Hash


def create(db: Session, request: schemas.Blog):
     # Check if user with this email already exists
    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    new_user = models.User(
        name=request.name,
        email=request.email,
        password=Hash.bcrypt(request.password)  # Hash the password before storing
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return new_user



def get(db: Session, id: int):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with id {id} not found')
    return user