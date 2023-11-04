from sqlalchemy import Column, Float, Integer, String, Boolean, ForeignKey, Date, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel


class User(BaseModel):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)

    payment_forms = relationship("PaymentForm", back_populates="user")


class PaymentForm(BaseModel):
    __tablename__ = 'payment_forms'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    amount = Column(Float)
    currency = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", back_populates="payment_forms")
    payments = relationship("Payment", back_populates="payment_forms")


class Payment(BaseModel):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, index=True)
    applicant_name = Column(String(100))
    amount = Column(Float)
    created_at = Column(Date)
    form_id = Column(Integer, ForeignKey('payment_forms.id', ondelete="CASCADE"))

    payment_forms = relationship("PaymentForm", back_populates="payments")
