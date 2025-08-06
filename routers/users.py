import utils, schemas, oauth
from db_stuffs import models, database
from fastapi import APIRouter,Depends, status, HTTPException, Response
from fastapi.security import  OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

router = APIRouter(tags=["Authenticattion"])


@router.post("/login")
def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.runner == request.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Runner {request.username} does not exist"
        )
    
    if not utils.verify(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect password"
        )
    
    access_token = oauth.create_access_token(data={"sub": user.runner})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
def register(request: schemas.CreateUser, db: Session = Depends(database.get_db)):
    hashed_password = utils.hash(request.password)
    new_user = models.User(runner=request.runner, password=hashed_password, is_superuser=request.is_superuser)
    existing_user = db.query(models.User).filter(models.User.runner == request.runner).first() 
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Runner {request.runner} already exists"
        ) 
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return schemas.UserResponse(id=new_user.id, runner=new_user.runner, is_superuser=request.is_superuser)


@router.get("/users/me", response_model=schemas.UserResponse)
def get_current_user(response: Response, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth.get_current_user)):
    if not current_user:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"detail": "Not authenticated"}
    
    return schemas.UserResponse(id=current_user.id, runner=current_user.runner)


@router.get("/users", response_model=list[schemas.UserResponse])
def get_all_users(db: Session = Depends(database.get_db)):
    users = db.query(models.User).all()
    return [schemas.UserResponse(id=user.id, runner=user.runner,  is_superuser=user.is_superuser) for user in users]
    

@router.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas.UserResponse(id=user.id, runner=user.runne)


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


