from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
try:
    from .database import Base
except ImportError:
    from database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_utc_now)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    gender = Column(String)
    contact_info = Column(String)
    created_at = Column(DateTime, default=get_utc_now)

    # Relationships
    indicators = relationship("HealthIndicator", back_populates="patient")
    assessments = relationship("RiskAssessment", back_populates="patient")
    follow_ups = relationship("FollowUp", back_populates="patient")

class HealthIndicator(Base):
    __tablename__ = "health_indicators"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    blood_pressure_sys = Column(Integer)
    blood_pressure_dia = Column(Integer)
    glucose = Column(Float)
    recorded_at = Column(DateTime, default=get_utc_now)

    patient = relationship("Patient", back_populates="indicators")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    risk_level = Column(String)  # High, Med, Low
    assessment_date = Column(DateTime, default=get_utc_now)
    notes = Column(String)

    patient = relationship("Patient", back_populates="assessments")

class FollowUp(Base):
    __tablename__ = "follow_ups"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    task_description = Column(String)
    status = Column(String, default="Pending")  # Pending, Completed
    due_date = Column(DateTime)
    completed_at = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="follow_ups")
