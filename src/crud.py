from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from datetime import datetime, timedelta

try:
    from . import models, schemas, risk_engine, auth
except ImportError:
    import models, schemas, risk_engine, auth

# Patient Operations
def get_patient(db: Session, patient_id: int):
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()

def get_patients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Patient).offset(skip).limit(limit).all()

def create_patient(db: Session, patient: schemas.PatientCreate):
    db_patient = models.Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def update_patient(db: Session, patient_id: int, patient_update: schemas.PatientUpdate):
    db_patient = get_patient(db, patient_id)
    if not db_patient:
        return None
    update_data = patient_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_patient, key, value)
    db.commit()
    db.refresh(db_patient)
    return db_patient

# Health Indicator & Risk Assessment Operations
def create_patient_indicator(db: Session, indicator: schemas.HealthIndicatorCreate):
    # 1. Save health indicator
    db_indicator = models.HealthIndicator(**indicator.model_dump())
    db.add(db_indicator)
    
    # 2. Trigger Risk Engine (US-04)
    risk_level = risk_engine.calculate_risk_level(
        indicator.blood_pressure_sys,
        indicator.blood_pressure_dia,
        indicator.glucose
    )
    
    # 3. Create Risk Assessment record
    db_assessment = models.RiskAssessment(
        patient_id=indicator.patient_id,
        risk_level=risk_level,
        notes=f"Auto-generated based on BP {indicator.blood_pressure_sys}/{indicator.blood_pressure_dia} and Glucose {indicator.glucose}"
    )
    db.add(db_assessment)
    
    # 4. Generate Follow-up Task (US-07)
    db_followup = risk_engine.generate_follow_up_task(indicator.patient_id, risk_level)
    db.add(db_followup)
    
    db.commit()
    db.refresh(db_indicator)
    return db_indicator

# Follow-up Operations
def get_follow_ups(db: Session, status: Optional[str] = None, skip: int = 0, limit: int = 100):
    query = db.query(models.FollowUp)
    if status:
        query = query.filter(models.FollowUp.status == status)
    return query.offset(skip).limit(limit).all()

def update_follow_up(db: Session, follow_up_id: int, follow_up_update: schemas.FollowUpUpdate):
    db_followup = db.query(models.FollowUp).filter(models.FollowUp.id == follow_up_id).first()
    if not db_followup:
        return None
    update_data = follow_up_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_followup, key, value)
    db.commit()
    db.refresh(db_followup)
    return db_followup

# User Operations
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Add the logic to calculate averages and determine trends
def get_patient_trend(db: Session, patient_id: int, days: int = 30):
    # Calculate the start date for the period
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Query indicators for the patient within the period
    indicators = db.query(models.HealthIndicator).filter(
        models.HealthIndicator.patient_id == patient_id,
        models.HealthIndicator.recorded_at >= start_date
    ).all()
    
    if not indicators:
        return None
    
    # Calculate averages
    avg_sbp = sum(i.blood_pressure_sys for i in indicators) / len(indicators)
    avg_dbp = sum(i.blood_pressure_dia for i in indicators) / len(indicators)
    avg_glucose = sum(i.glucose for i in indicators) / len(indicators)
    
    # Simple trend logic (this can be made more complex later)
    # For now, we'll label it based on the latest risk assessment
    latest_assessment = db.query(models.RiskAssessment).filter(
        models.RiskAssessment.patient_id == patient_id
    ).order_by(models.RiskAssessment.assessment_date.desc()).first()
    
    status = "Stable"
    if latest_assessment:
        if latest_assessment.risk_level == "High":
            status = "Deteriorating"
        elif latest_assessment.risk_level == "Low":
            status = "Improving"
            
    return {
        "patient_id": patient_id,
        "period_days": days,
        "avg_sbp": round(avg_sbp, 1),
        "avg_dbp": round(avg_dbp, 1),
        "avg_glucose": round(avg_glucose, 2),
        "record_count": len(indicators),
        "status": status
    }
