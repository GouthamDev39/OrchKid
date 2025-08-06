from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import psycopg as db
from psycopg.rows import dict_row
from config import settings

import time


SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOSTNAME}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
# SQLALCHEMY_DATABASE_URL = "postgresql://batman:pswd@localhost:5432/job_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit = False, autoflush= False, bind= engine)

Base = declarative_base()#we usethis class to inherit to create each db models 

def get_db():#dependency
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()