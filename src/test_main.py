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

def test_create_and_update_patient(auth_headers):
    # Create
    response = client.post(
        "/patients/",
        json={"name": "John Doe", "age": 45, "gender": "Male", "contact_info": "123456789"},
        headers=auth_headers
    )
    assert response.status_code == 200
    patient_id = response.json()["id"]
    
    # Update
    response = client.put(
        f"/patients/{patient_id}",
        json={"name": "John Updated", "age": 46},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "John Updated"
    assert response.json()["age"] == 46

def test_followup_list_and_update(auth_headers):
    # 1. Create patient and trigger follow-up
    create_resp = client.post(
        "/patients/",
        json={"name": "Followup Test", "age": 60, "gender": "Male"},
        headers=auth_headers
    )
    patient_id = create_resp.json()["id"]
    
    client.post("/indicators/", json={
        "patient_id": patient_id,
        "blood_pressure_sys": 170,
        "blood_pressure_dia": 100,
        "glucose": 12.0
    }, headers=auth_headers)
    
    # 2. Query grouped follow-up list
    response = client.get("/followups/", headers=auth_headers)
    assert response.status_code == 200
    groups = response.json()
    assert len(groups) >= 1
    assert groups[0]["patient"]["id"] == patient_id
    followup_id = groups[0]["followups"][0]["id"]
    
    # 3. Update follow-up status
    response = client.patch(
        f"/followups/{followup_id}",
        json={"status": "Completed"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Completed"

def test_user_auth_flow():
    # 1. Register
    response = client.post(
        "/users/",
        json={"username": "doctor1", "password": "shortpassword", "full_name": "Dr. Smith"}
    )
    assert response.status_code == 200
    
    # 2. Login to get Token
    response = client.post(
        "/token",
        data={"username": "doctor1", "password": "shortpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
    
    # 3. Get Me
    token = response.json()["access_token"]
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "doctor1"

def test_risk_assessment_trigger(auth_headers):
    create_resp = client.post(
        "/patients/",
        json={"name": "Risk Test", "age": 60, "gender": "Male"},
        headers=auth_headers
    )
    patient_id = create_resp.json()["id"]
    
    client.post("/indicators/", json={
        "patient_id": patient_id,
        "blood_pressure_sys": 170,
        "blood_pressure_dia": 105,
        "glucose": 12.0
    }, headers=auth_headers)
    
    response = client.get(f"/patients/{patient_id}", headers=auth_headers)
    data = response.json()
    assert data["assessments"][0]["risk_level"] == "High"

def test_dashboard_info(auth_headers):
    # Create some data
    client.post("/patients/", json={"name": "P1", "age": 20, "gender": "M"}, headers=auth_headers)
    client.post("/patients/", json={"name": "P2", "age": 40, "gender": "F"}, headers=auth_headers)
    
    response = client.get("/dashboard/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "counts" in data
    assert "risk_distribution" in data
    assert "weekly_patient_registrations" in data
    assert "age_distribution" in data
    assert data["counts"]["total_patients"] >= 2
