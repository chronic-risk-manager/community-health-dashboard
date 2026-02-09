from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy import func, case

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
    
    # 4. Automatically complete previous pending follow-ups for this patient
    db.query(models.FollowUp).filter(
        models.FollowUp.patient_id == indicator.patient_id,
        models.FollowUp.status == "Pending"
    ).update({
        "status": "Completed",
        "completed_at": datetime.utcnow()
    }, synchronize_session=False)
    
    # 5. Generate new Follow-up Task (US-07)
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

def get_grouped_follow_ups(db: Session, status: Optional[str] = None):
    query = db.query(models.FollowUp)
    if status:
        query = query.filter(models.FollowUp.status == status)
    
    followups = query.all()
    
    # Group by patient
    grouped: Dict[int, schemas.PatientFollowUpGroup] = {}
    for f in followups:
        if f.patient_id not in grouped:
            grouped[f.patient_id] = schemas.PatientFollowUpGroup(
                patient=schemas.PatientBrief.model_validate(f.patient),
                followups=[]
            )
        grouped[f.patient_id].followups.append(schemas.FollowUp.model_validate(f))
    
    return list(grouped.values())

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

# Trend Analysis
def get_patient_trend(db: Session, patient_id: int, days: int = 30):
    start_date = datetime.utcnow() - timedelta(days=days)
    indicators = db.query(models.HealthIndicator).filter(
        models.HealthIndicator.patient_id == patient_id,
        models.HealthIndicator.recorded_at >= start_date
    ).all()
    
    if not indicators:
        return None
    
    avg_sbp = sum(i.blood_pressure_sys for i in indicators) / len(indicators)
    avg_dbp = sum(i.blood_pressure_dia for i in indicators) / len(indicators)
    avg_glucose = sum(i.glucose for i in indicators) / len(indicators)
    
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

# Dashboard Operations
def get_dashboard_info(db: Session):
    # 1. Counts
    total_patients = db.query(func.count(models.Patient.id)).scalar()
    
    # High risk patients (latest assessment is High)
    subquery = db.query(
        models.RiskAssessment.patient_id,
        func.max(models.RiskAssessment.assessment_date).label('max_date')
    ).group_by(models.RiskAssessment.patient_id).subquery()
    
    high_risk_count = db.query(func.count(models.RiskAssessment.id)).join(
        subquery, 
        (models.RiskAssessment.patient_id == subquery.c.patient_id) & 
        (models.RiskAssessment.assessment_date == subquery.c.max_date)
    ).filter(models.RiskAssessment.risk_level == "High").scalar()
    
    upcoming_followups = db.query(func.count(models.FollowUp.id)).filter(
        models.FollowUp.status == "Pending",
        models.FollowUp.due_date >= datetime.utcnow()
    ).scalar()
    
    # 2. Risk Distribution
    risk_dist = db.query(
        models.RiskAssessment.risk_level,
        func.count(models.RiskAssessment.id)
    ).join(
        subquery,
        (models.RiskAssessment.patient_id == subquery.c.patient_id) &
        (models.RiskAssessment.assessment_date == subquery.c.max_date)
    ).group_by(models.RiskAssessment.risk_level).all()
    
    risk_map = {"High": 0, "Med": 0, "Low": 0}
    for level, count in risk_dist:
        if level in risk_map:
            risk_map[level] = count
            
    # 3. Weekly Registrations (Last 4 weeks)
    four_weeks_ago = datetime.utcnow() - timedelta(weeks=4)
    weekly_reg = db.query(
        func.strftime('%Y-%W', models.Patient.created_at).label('week'),
        func.count(models.Patient.id)
    ).filter(models.Patient.created_at >= four_weeks_ago).group_by('week').all()
    
    weekly_data = [{"week": w, "count": c} for w, c in weekly_reg]
    
    # 4. Age Distribution
    age_dist = db.query(
        case(
            (models.Patient.age < 18, "0-17"),
            (models.Patient.age < 35, "18-34"),
            (models.Patient.age < 55, "35-54"),
            (models.Patient.age < 75, "55-74"),
            else_="75+"
        ).label('age_range'),
        func.count(models.Patient.id)
    ).group_by('age_range').all()
    
    age_data = [{"range": r, "count": c} for r, c in age_dist]
    
    return {
        "counts": {
            "total_patients": total_patients,
            "high_risk_patients": high_risk_count,
            "upcoming_followups": upcoming_followups
        },
        "risk_distribution": {
            "high": risk_map["High"],
            "medium": risk_map["Med"],
            "low": risk_map["Low"]
        },
        "weekly_patient_registrations": weekly_data,
        "age_distribution": age_data
    }
