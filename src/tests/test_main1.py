import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app
from database import Base, get_db
import pytest

# Use In-Memory SQLite for Testing
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

def test_create_patient():
    response = client.post(
        "/patients/",
        json={"name": "John Doe", "age": 45, "gender": "Male", "contact_info": "123456789"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    assert "id" in data

def test_read_patients():
    client.post(
        "/patients/",
        json={"name": "Jane Doe", "age": 30, "gender": "Female"}
    )
    response = client.get("/patients/")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_read_patient_detail():
    create_resp = client.post(
        "/patients/",
        json={"name": "Alice", "age": 25, "gender": "Female"}
    )
    patient_id = create_resp.json()["id"]
    
    response = client.get(f"/patients/{patient_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Alice"