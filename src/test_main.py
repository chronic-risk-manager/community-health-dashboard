
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from database import Base, get_db
import pytest

# 使用内存中的 SQLite 进行测试
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

def test_create_and_update_patient():
    # 创建
    response = client.post(
        "/patients/",
        json={"name": "John Doe", "age": 45, "gender": "Male", "contact_info": "123456789"}
    )
    assert response.status_code == 200
    patient_id = response.json()["id"]
    
    # 更新
    response = client.put(
        f"/patients/{patient_id}",
        json={"name": "John Updated", "age": 46}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "John Updated"
    assert response.json()["age"] == 46

def test_followup_list_and_update():
    # 1. 创建患者并触发随访
    create_resp = client.post(
        "/patients/",
        json={"name": "Followup Test", "age": 60, "gender": "Male"}
    )
    patient_id = create_resp.json()["id"]
    
    client.post("/indicators/", json={
        "patient_id": patient_id,
        "blood_pressure_sys": 170,
        "blood_pressure_dia": 100,
        "glucose": 12.0
    })
    
    # 2. 查询全局随访列表
    response = client.get("/followups/")
    assert response.status_code == 200
    followups = response.json()
    assert len(followups) >= 1
    followup_id = followups[0]["id"]
    
    # 3. 更新随访状态
    response = client.patch(
        f"/followups/{followup_id}",
        json={"status": "Completed"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Completed"

def test_user_auth_flow():
    # 1. 注册
    response = client.post(
        "/users/",
        json={"username": "doctor1", "password": "shortpassword", "full_name": "Dr. Smith"}
    )
    assert response.status_code == 200
    
    # 2. 登录获取 Token
    response = client.post(
        "/token",
        data={"username": "doctor1", "password": "shortpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_risk_assessment_trigger():
    create_resp = client.post(
        "/patients/",
        json={"name": "Risk Test", "age": 60, "gender": "Male"}
    )
    patient_id = create_resp.json()["id"]
    
    client.post("/indicators/", json={
        "patient_id": patient_id,
        "blood_pressure_sys": 170,
        "blood_pressure_dia": 105,
        "glucose": 12.0
    })
    
    response = client.get(f"/patients/{patient_id}")
    data = response.json()
    assert data["assessments"][0]["risk_level"] == "High"
