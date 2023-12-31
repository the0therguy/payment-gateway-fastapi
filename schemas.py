import datetime

from pydantic import BaseModel, EmailStr
from pydantic.types import constr
from typing import Optional


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    email: str
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    password: Optional[str]


class UserOut(UserBase):
    id: int

    class Config:
        orm_mode = True


class UserInDB(UserBase):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None


class PaymentFormBase(BaseModel):
    name: str
    description: str
    amount: float
    currency: str


class PaymentFormCreate(PaymentFormBase):
    pass


class PaymentFormUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    amount: Optional[float]
    currency: Optional[str]


class PaymentFormOut(BaseModel):
    id: int
    name: str
    description: str
    amount: float
    currency: str


class PaymentBase(BaseModel):
    applicant_name: str
    amount: float
    created_at: datetime.date = datetime.date.today()


class PaymentCreate(PaymentBase):
    pass


class PaymentOut(PaymentBase):
    id: int

    class Config:
        orm_mode = True


class PaymentHistory(BaseModel):
    payment_id: int
    applicant_name: str
    amount: float
    created_at: datetime.date
    payment_form_id: int

    class Config:
        orm_mode = True
