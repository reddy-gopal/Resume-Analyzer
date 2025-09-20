from sqlalchemy import Column, Integer, String, DateTime, JSON
from backend.db import Base
import datetime

class Evaluation(Base):
    __tablename__ = 'evaluations'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True) # Added username
    resume_filename = Column(String, index=True)
    job_description_summary = Column(String)
    overall_score = Column(Integer)
    matching_skills = Column(JSON)
    missing_skills = Column(JSON)
    feedback = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)