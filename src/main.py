from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

try:
    from . import models, schemas, crud, database, auth
except ImportError:
    import models, schemas, crud, database, auth

# 初始化数据库表
models.Base.metadata.create_all(bind=database.engine)

# 定义 OAuth2 方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="Community Health Dashboard API")

@app.get("/")
def read_root():
    return {"message": "Welcome to Community Health Dashboard API"}

# --- Authentication Endpoints ---

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Patient Endpoints ---

@app.post("/patients/", response_model=schemas.Patient)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    return crud.create_patient(db=db, patient=patient)

@app.get("/patients/", response_model=List[schemas.Patient])
def read_patients(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    return crud.get_patients(db, skip=skip, limit=limit)

@app.get("/patients/{patient_id}", response_model=schemas.PatientDetail)
def read_patient(patient_id: int, db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    db_patient = crud.get_patient(db, patient_id=patient_id)
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

@app.put("/patients/{patient_id}", response_model=schemas.Patient)
def update_patient(patient_id: int, patient_update: schemas.PatientUpdate, db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    db_patient = crud.update_patient(db, patient_id=patient_id, patient_update=patient_update)
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

# --- Health Indicator Endpoints ---

@app.post("/indicators/", response_model=schemas.HealthIndicator)
def create_indicator(indicator: schemas.HealthIndicatorCreate, db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    return crud.create_patient_indicator(db=db, indicator=indicator)

# --- Follow-up Endpoints ---

@app.get("/followups/", response_model=List[schemas.FollowUp])
def read_follow_ups(status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    return crud.get_follow_ups(db, status=status, skip=skip, limit=limit)

@app.patch("/followups/{follow_up_id}", response_model=schemas.FollowUp)
def update_follow_up(follow_up_id: int, follow_up_update: schemas.FollowUpUpdate, db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    db_followup = crud.update_follow_up(db, follow_up_id=follow_up_id, follow_up_update=follow_up_update)
    if db_followup is None:
        raise HTTPException(status_code=404, detail="Follow-up task not found")
    return db_followup
