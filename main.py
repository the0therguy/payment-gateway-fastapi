# Import necessary modules and set up the FastAPI app
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
from sqlalchemy.orm import joinedload
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Create the database tables
Base.metadata.create_all(bind=engine)


# Function to get a database session (Singleton design pattern)
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


# OAuth2 token scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/sign_in")


# Function to send payment notifications via email
def send_payment_notification(email, amount):
    # Configure your SMTP server and email settings (use environment variables)
    smtp_server = os.environ.get("smtp_server")
    smtp_port = 587
    smtp_username = os.environ.get("smtp_username")
    smtp_password = os.environ.get("smtp_password")

    # Create the email message
    subject = "Payment Notification"
    body = f"Payment of ${amount} has been made using your form."
    sender_email = smtp_username
    receiver_email = email

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, receiver_email, message.as_string())


# Function to get the current user based on the provided token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    try:
        payload = jwt.decode(token, os.environ.get('SECRET_KEY'), algorithms=os.environ.get('ALGORITHM'))
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not validate credentials",
        )
    return db.query(models.User).filter(models.User.email == token_data.sub).first()


# Endpoint to handle user signup
@app.post("/signup", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
async def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    email = user_in.email
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="User already exists")
    user_dict = user_in.dict(exclude={"password"})
    password = get_password_hash(user_in.password)
    user_dict.update({"password": password})
    new_user = models.User(**user_dict)
    db.add(new_user)
    db.commit()
    return schemas.UserOut(**{
        "name": new_user.name,
        "email": new_user.email,
        "id": new_user.id
    })


# Endpoint to handle user sign-in and issue access tokens
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


# Endpoint to create a payment form
@app.post("/payment_forms", response_model=schemas.PaymentFormOut, status_code=status.HTTP_201_CREATED)
async def create_payment_form(payment_form: schemas.PaymentFormCreate, token: str = Depends(get_current_user),
                              db: Session = Depends(get_db)):
    # Create a new PaymentForm in the database
    db_payment_form = models.PaymentForm(**payment_form.dict(), user_id=token.id)
    db.add(db_payment_form)
    db.commit()

    return schemas.PaymentFormOut(
        id=db_payment_form.id,
        name=db_payment_form.name,
        description=db_payment_form.description,
        amount=db_payment_form.amount,
        currency=db_payment_form.currency
    )


# Endpoint to create a payment and send payment notification
@app.post("/payments/{payment_form_id}", response_model=schemas.PaymentOut, status_code=status.HTTP_201_CREATED)
async def create_payment(payment: schemas.PaymentCreate, payment_form_id: int, db: Session = Depends(get_db)):
    payment_form = db.query(models.PaymentForm).filter(models.PaymentForm.id == payment_form_id).first()

    if not payment_form:
        raise HTTPException(status_code=404, detail="PaymentForm not found")

    # Create the Payment with the specified payment_form_id
    db_payment = models.Payment(**payment.dict(), form_id=payment_form_id)
    db.add(db_payment)
    db.commit()
    send_payment_notification(email=payment_form.user.email, amount=db_payment.amount)

    return db_payment


# Endpoint to get payment history for the current user
@app.get("/payment_history", response_model=list[schemas.PaymentHistory], status_code=status.HTTP_200_OK)
async def get_payment_history(token: str = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get all payments for the user
    payments = db.query(models.Payment).join(models.PaymentForm).join(models.User).filter(
        models.User.id == token.id).all()
    payment_history = []
    for payment in payments:
        payment_history.append(
            schemas.PaymentHistory(payment_id=payment.id, payment_form_id=payment.form_id, amount=payment.amount,
                                   applicant_name=payment.applicant_name, created_at=payment.created_at))

    return payment_history
