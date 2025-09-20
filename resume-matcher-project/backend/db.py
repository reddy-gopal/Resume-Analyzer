import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Define the location of our new SQLite database file ---
DATABASE_URL = "sqlite:///./evaluations.db"

# The connect_args is needed for SQLite to allow it to be used in a multithreaded
# app like Streamlit.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

from .models.evaluation import Evaluation

def init_db():
    # This function creates all tables that inherit from Base
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()