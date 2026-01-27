from sqlalchemy.orm import Session
import models, schemas
from core import risk_engine


def get_patient(db: Session, patient_id: int):
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()

def get_patients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Patient).offset(skip).limit(limit).all()

def create_patient(db: Session, patient: schemas.PatientCreate):
    db_patient = models.Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def create_patient_indicator(db: Session, indicator: schemas.HealthIndicatorCreate):
    # 1. Save health indicator
    db_indicator = models.HealthIndicator(**indicator.dict())
    db.add(db_indicator)
    
    # 2. Trigger risk assessment (US-04)
    risk_level = risk_engine.calculate_risk_level(
        indicator.blood_pressure_sys, 
        indicator.blood_pressure_dia, 
        indicator.glucose
    )
    db_assessment = models.RiskAssessment(
        patient_id=indicator.patient_id,
        risk_level=risk_level,
        notes=f"Auto-assessed based on BP: {indicator.blood_pressure_sys}/{indicator.blood_pressure_dia}, Glucose: {indicator.glucose}"
    )
    db.add(db_assessment)
    
    # 3. Automatically generate follow-up task (US-07)
    db_follow_up = risk_engine.generate_follow_up_task(indicator.patient_id, risk_level)
    db.add(db_follow_up)
    
    db.commit()
    db.refresh(db_indicator)
    return db_indicator