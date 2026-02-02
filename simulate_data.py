import os
import sys
import random
from datetime import datetime, timedelta
import pytz

# Add src directory to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from database import SessionLocal, engine
import models, crud, schemas

# Set Helsinki timezone
helsinki_tz = pytz.timezone('Europe/Helsinki')

def simulate():
    db = SessionLocal()
    print("Starting simulation of 2000+ health records...")

    # 1. Create 50 simulated patients
    patients = []
    for i in range(50):
        patient_in = schemas.PatientCreate(
            name=f"Patient_{i+1:03d}",
            age=random.randint(20, 85),
            gender=random.choice(["Male", "Female"]),
            contact_info=f"patient{i+1}@example.com"
        )
        p = crud.create_patient(db, patient_in)
        patients.append(p)
    
    print(f"Successfully created {len(patients)} patients.")

    # 2. Generate indicators for each patient for the past 90 days
    # (One record every 2-3 days, totaling approximately 2000 records)
    total_indicators = 0
    start_date = datetime.now(helsinki_tz) - timedelta(days=90)

    for p in patients:
        current_date = start_date
        # Define health baseline for this specific patient
        base_sbp = random.randint(110, 150)
        base_dbp = random.randint(70, 95)
        base_glucose = random.uniform(4.5, 8.5)

        while current_date < datetime.now(helsinki_tz):
            # Simulate data fluctuations
            indicator_in = schemas.HealthIndicatorCreate(
                patient_id=p.id,
                blood_pressure_sys=base_sbp + random.randint(-10, 20),
                blood_pressure_dia=base_dbp + random.randint(-5, 10),
                glucose=round(base_glucose + random.uniform(-1.0, 3.0), 1),
                recorded_at=current_date
            )
            # Call crud method (this automatically triggers risk assessment and follow-up generation)
            crud.create_patient_indicator(db, indicator_in)
            total_indicators += 1
            
            # Random interval of 2-3 days
            current_date += timedelta(days=random.randint(2, 3))

    db.close()
    print(f"Simulation complete! Total indicator records generated: {total_indicators}")
    print("Risk assessments and follow-up tasks have been automatically generated.")

if __name__ == "__main__":
    simulate()
