from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Health Indicator Schemas
class HealthIndicatorBase(BaseModel):
    blood_pressure_sys: int
    blood_pressure_dia: int
    glucose: float

class HealthIndicatorCreate(HealthIndicatorBase):
    patient_id: int

class HealthIndicator(HealthIndicatorBase):
    id: int
    recorded_at: datetime

    class Config:
        from_attributes = True

# Patient Schemas
class PatientBase(BaseModel):
    name: str
    age: int
    gender: str
    contact_info: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Risk Assessment Schemas
class RiskAssessmentBase(BaseModel):
    risk_level: str
    notes: Optional[str] = None

class RiskAssessment(RiskAssessmentBase):
    id: int
    assessment_date: datetime

    class Config:
        from_attributes = True

# Follow Up Schemas
class FollowUpBase(BaseModel):
    task_description: str
    status: str
    due_date: datetime

class FollowUp(FollowUpBase):
    id: int
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Detailed Patient Schema
class PatientDetail(Patient):
    indicators: List[HealthIndicator] = []
    assessments: List[RiskAssessment] = []
    follow_ups: List[FollowUp] = []