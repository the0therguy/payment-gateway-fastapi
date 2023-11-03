from fastapi import FastAPI, status, Response, Depends
from fastapi.exceptions import HTTPException
from database import engine, SessionLocal
from sqlalchemy.orm import Session
import models.models as models
import schemas
from utils.auth import get_password_hash, verify_password, create_access_token
from models.base import Base
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta
from pydantic import ValidationError
from jose import jwt

app = FastAPI()

Base.metadata.create_all(bind=engine)


# Singleton design pattern
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/sign_in")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    try:
        payload = jwt.decode(
            token, 'this is a key', algorithms="HS256"
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not validate credentials",
        )
    return db.query(models.User).filter(models.User.email == token_data.sub).first()


@app.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    email = user_in.email
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="Book not found")
    user_dict = user_in.dict(exclude={"password"})
    password = get_password_hash(user_in.password)
    user_dict.update({"password": password})
    new_user = models.User(**user_dict)
    db.add(new_user)
    db.commit()
    # new_generated_id = await user.create(schemas.UserInDB(**user_dict))
    return user_in


@app.post("/sign_in", response_model=schemas.Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_info = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user_info or not verify_password(form_data.password, user_info.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(user_info.email, access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/payment_forms", response_model=schemas.PaymentFormResponse)
async def create_payment_form(payment_form: schemas.PaymentFormCreate, token: str = Depends(get_current_user),
                              db: Session = Depends(get_db)):
    # Validate the OAuth2 token here (replace with your actual token validation logic)

    # Create a new PaymentForm in the database
    db_payment_form = models.PaymentForm(**payment_form.dict(), user_id=token.id)
    db.add(db_payment_form)
    db.commit()
    db.refresh(db_payment_form)
    return schemas.PaymentFormResponse(**db_payment_form.__dict__)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
