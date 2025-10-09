from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session
from .. import schemas, database,oauth2
from  ..repository import blog

router = APIRouter(
    prefix="/blog",
    tags=["Blogs"]
)

# Get database dependency
get_db = database.get_db

@router.post("/", status_code=status.HTTP_201_CREATED)
def create(request: schemas.Blog, db: Session = Depends(get_db), _: schemas.User = Depends(oauth2.get_current_user)):
    return blog.create(request, db)

@router.get("/", response_model=list[schemas.ShowBlog])
def getAllBlogs(db: Session = Depends(get_db), _: schemas.User = Depends(oauth2.get_current_user)):
    return blog.get_all(db)



@router.get("/{id}", status_code=status.HTTP_200_OK, response_model=schemas.Blog)
def show(id: int, db: Session = Depends(get_db), _: schemas.User = Depends(oauth2.get_current_user)):
   return blog.get_one(db, id)



@router.put("/{id}", status_code=status.HTTP_202_ACCEPTED)
def updateBlog(id: int, request: schemas.Blog, db: Session = Depends(get_db), _: schemas.User = Depends(oauth2.get_current_user)):
    return blog.update(id, request, db)




@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def deleteBlog(id: int, db: Session = Depends(get_db), _: schemas.User = Depends(oauth2.get_current_user)):
   return blog.destroy(db, id)