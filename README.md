# 🏥 Chronic Risk Manager

A community-based chronic disease risk management backend system built
with **FastAPI** and **SQLite**.\
This project aims to automatically assess and classify patients' chronic
disease risks through an intelligent risk evaluation engine.

## 🚀 Quick Start (Local Setup)

Make sure you have **Python 3.10+** installed.

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd CHRONIC_RISK_MANAGER
```

### 2. Create and activate virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start backend service

```bash
uvicorn src.main:app --reload
```

After startup, visit: http://localhost:8000/docs for API documentation.

## 📊 Project Structure

```text
CHRONIC_RISK_MANAGER/
├── src/
│   ├── api/v1/
│   │   ├── indicators.py
│   │   └── patient.py
│   ├── core/
│   │   └── risk_engine.py
│   ├── tests/
│   │   ├── test_main1.py
│   │   └── test_main2.py
│   ├── crud.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
├── data/
│   └── community_health.db
├── powerbi/
├── requirements.txt
└── README.md
```

## 🛠️ Technology Stack

Component Technology Description

---

Backend Framework FastAPI High-performance async web framework
Database SQLite Lightweight embedded database
ORM SQLAlchemy Python ORM toolkit
Data Validation Pydantic Runtime type checking
Testing Pytest Python testing framework
Visualization Power BI Business intelligence reporting tool

## 🔍 Core Modules

### 1. Risk Evaluation Engine (`src/core/risk_engine.py`)

- Chronic disease risk prediction algorithm\
- Multi-factor evaluation model\
- Automatic risk level classification

### 2. RESTful APIs (`src/api/v1/`)

- Patient management (CRUD)\
- Health indicator collection and risk calculation\
- Data export and reporting

### 3. Data Layer

- `models.py`: database table definitions\
- `schemas.py`: API request/response schemas\
- `crud.py`: reusable data access methods

## 📡 API Documentation

- Swagger UI: http://localhost:8000/docs\
- ReDoc: http://localhost:8000/redoc\
- OpenAPI JSON: http://localhost:8000/openapi.json

### Example Endpoints

```http
GET /api/v1/patients/
GET /api/v1/patients/{patient_id}

POST /api/v1/indicators/calculate
Content-Type: application/json

{
  "patient_id": 1,
  "indicators": {...}
}
```

## 🧪 Running Tests

```bash
pytest src/tests/
pytest src/tests/test_main1.py -v
pytest src/tests/test_main2.py -v
pytest --cov=src src/tests/
```

## 📈 Data Analytics & Visualization

Power BI templates are located in the `powerbi/` directory and support:

- Patient risk distribution visualization\
- Community health trend analysis\
- Chronic disease management effectiveness evaluation

## ⚙️ Configuration

### Database configuration (`src/database.py`)

```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/community_health.db"
```
