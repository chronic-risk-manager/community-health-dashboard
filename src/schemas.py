from pydantic import BaseModel, ConfigDict
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
    model_config = ConfigDict(from_attributes=True)

# Risk Assessment Schemas
class RiskAssessmentBase(BaseModel):
    risk_level: str
    notes: Optional[str] = None

class RiskAssessment(RiskAssessmentBase):
    id: int
    assessment_date: datetime
    model_config = ConfigDict(from_attributes=True)

# Follow-up Schemas
class FollowUpBase(BaseModel):
    task_description: str
    status: str
    due_date: datetime

class FollowUpUpdate(BaseModel):
    status: Optional[str] = None
    completed_at: Optional[datetime] = None

class FollowUp(FollowUpBase):
    id: int
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# Patient Schemas
class PatientBase(BaseModel):
    name: str
    age: int
    gender: str
    contact_info: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    contact_info: Optional[str] = None

class Patient(PatientBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PatientDetail(Patient):
    indicators: List[HealthIndicator] = []
    assessments: List[RiskAssessment] = []
    follow_ups: List[FollowUp] = []
    model_config = ConfigDict(from_attributes=True)

# User & Auth Schemas
class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class HealthTrend(BaseModel):
    patient_id: int
    period_days: int
    avg_sbp: float
    avg_dbp: float
    avg_glucose: float
    record_count: int
    status: str  # e.g., "Improving", "Stable", "Deteriorating"

    class Config:
        from_attributes = True
