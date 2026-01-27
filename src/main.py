import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

project_root = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)      
sys.path.insert(0, project_root)     

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas, crud
from database import SessionLocal, engine, get_db

# create database Table
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Community Health Dashboard API")

@app.get("/")
def read_root():
    return {"message": "Welcome to Community Health Dashboard API"}

@app.post("/patients/", response_model=schemas.Patient)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    return crud.create_patient(db=db, patient=patient)

@app.get("/patients/", response_model=List[schemas.Patient])
def read_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    patients = crud.get_patients(db, skip=skip, limit=limit)
    return patients

@app.get("/patients/{patient_id}", response_model=schemas.PatientDetail)
def read_patient(patient_id: int, db: Session = Depends(get_db)):
    db_patient = crud.get_patient(db, patient_id=patient_id)
    if db_patient is None:
        raise HTTPException(status_code=44, detail="Patient not found")
    return db_patient

@app.post("/indicators/", response_model=schemas.HealthIndicator)
def create_indicator(indicator: schemas.HealthIndicatorCreate, db: Session = Depends(get_db)):
    return crud.create_patient_indicator(db=db, indicator=indicator)