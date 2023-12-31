from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
import os
from dotenv import load_dotenv

load_dotenv()

try:
    SQLALCHEMY_URL: str = os.environ.get("DATABASE_URL")
    engine = create_engine(SQLALCHEMY_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)
    Base = declarative_base()

except OperationalError as e:
    print(e)
