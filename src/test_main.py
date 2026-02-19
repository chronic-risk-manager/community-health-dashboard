import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from database import Base, get_db
import pytest

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_headers():
    # Register and login to get token
    client.post(
        "/users/",
        json={"username": "testuser", "password": "testpassword", "full_name": "Test User"}
    )
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# --- Root Endpoint ---
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Community Health Dashboard API"}

# --- Authentication & User Endpoints ---
def test_user_auth_flow():
    # 1. Register
    response = client.post(
        "/users/",
        json={"username": "doctor1", "password": "shortpassword", "full_name": "Dr. Smith"}
    )
    assert response.status_code == 200
    
    # 2. Register duplicate username (Edge Case)
    response = client.post(
        "/users/",
        json={"username": "doctor1", "password": "anotherpassword", "full_name": "Dr. Smith"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"
    
    # 3. Login to get Token
    response = client.post(
        "/token",
        data={"username": "doctor1", "password": "shortpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    # 4. Login with wrong password (Edge Case)
    response = client.post(
        "/token",
        data={"username": "doctor1", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    
    # 5. Get Me
    token = client.post("/token", data={"username": "doctor1", "password": "shortpassword"}).json()["access_token"]
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "doctor1"

# --- Patient Endpoints ---
def test_patient_operations(auth_headers):
    # 1. Create
    response = client.post(
        "/patients/",
        json={"name": "John Doe", "age": 45, "gender": "Male", "contact_info": "123456789"},
        headers=auth_headers
    )
    assert response.status_code == 200
    patient_id = response.json()["id"]
    
    # 2. Read List
    response = client.get("/patients/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1
    
    # 3. Read Detail
    response = client.get(f"/patients/{patient_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"
    
    # 4. Update
    response = client.put(
        f"/patients/{patient_id}",
        json={"name": "John Updated", "age": 46},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "John Updated"
    
    # 5. Read Non-existent Patient (Edge Case)
    response = client.get("/patients/999", headers=auth_headers)
    assert response.status_code == 404

# --- Health Indicator & Trend Endpoints ---
def test_indicators_and_trends(auth_headers):
    # 1. Create Patient
    create_resp = client.post(
        "/patients/",
        json={"name": "Trend Test", "age": 50, "gender": "Female"},
        headers=auth_headers
    )
    patient_id = create_resp.json()["id"]
    
    # 2. Add Indicators
    for i in range(3):
        client.post("/indicators/", json={
            "patient_id": patient_id,
            "blood_pressure_sys": 120 + i*10,
            "blood_pressure_dia": 80 + i*5,
            "glucose": 5.5 + i*0.5
        }, headers=auth_headers)
    
    # 3. Get Trend
    response = client.get(f"/patients/{patient_id}/trend", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["record_count"] == 3
    assert data["avg_sbp"] == 130.0
    
    # 4. Trend for patient with no data (Edge Case)
    response = client.get("/patients/999/trend", headers=auth_headers)
    assert response.status_code == 404

# --- Follow-up Endpoints ---
def test_followup_logic(auth_headers):
    # 1. Create patient and trigger high risk follow-up
    create_resp = client.post(
        "/patients/",
        json={"name": "Risk Test", "age": 65, "gender": "Male"},
        headers=auth_headers
    )
    patient_id = create_resp.json()["id"]
    
    client.post("/indicators/", json={
        "patient_id": patient_id,
        "blood_pressure_sys": 170,
        "blood_pressure_dia": 105,
        "glucose": 12.0
    }, headers=auth_headers)
    
    # 2. Check grouped follow-ups
    response = client.get("/followups/", headers=auth_headers)
    assert response.status_code == 200
    groups = response.json()
    assert any(g["patient"]["id"] == patient_id for g in groups)
    
    # 3. Add new indicator should complete previous follow-up
    client.post("/indicators/", json={
        "patient_id": patient_id,
        "blood_pressure_sys": 120,
        "blood_pressure_dia": 80,
        "glucose": 5.0
    }, headers=auth_headers)
    
    # Check if the first follow-up is now completed
    response = client.get(f"/patients/{patient_id}", headers=auth_headers)
    follow_ups = response.json()["follow_ups"]
    assert any(f["status"] == "Completed" for f in follow_ups)
    
    # 4. Update follow-up manually
    followup_id = follow_ups[-1]["id"]
    response = client.patch(
        f"/followups/{followup_id}",
        json={"status": "Completed"},
        headers=auth_headers
    )
    assert response.status_code == 200

# --- Dashboard Endpoint ---
def test_dashboard_data(auth_headers):
    # 1. Create some diverse data
    client.post("/patients/", json={"name": "Young", "age": 20, "gender": "M"}, headers=auth_headers)
    client.post("/patients/", json={"name": "Old", "age": 80, "gender": "F"}, headers=auth_headers)
    
    # 2. Get Dashboard
    response = client.get("/dashboard/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["counts"]["total_patients"] >= 2
    assert len(data["age_distribution"]) >= 1
    assert "risk_distribution" in data
