# 🏥 Chronic Risk Manager

A community-based chronic disease risk management backend system built with **FastAPI** and **SQLite**. This project automatically assesses and classifies patients' chronic disease risks through an intelligent risk evaluation engine and manages follow-up tasks for medical staff.

## 🚀 Quick Start (Local Setup)

Make sure you have **Python 3.10+** installed.

### 1. Clone the repository
```bash
git clone https://github.com/chronic-risk-manager/community-health-dashboard.git
cd community-health-dashboard
```

### 2. Create and activate virtual environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start backend service
```bash
uvicorn src.main:app --reload
```
After startup, visit: [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI | High-performance async web framework |
| **Database** | SQLite | Lightweight embedded relational database |
| **ORM** | SQLAlchemy | Python SQL toolkit and Object Relational Mapper |
| **Authentication** | JWT (JOSE) | Secure token-based authentication |
| **Data Validation** | Pydantic | Runtime type checking and data validation |
| **Testing** | Pytest | Python testing framework |

---

## 📊 Project Structure

```text
CHRONIC_RISK_MANAGER/
├── src/
│   ├── auth.py          # JWT Authentication & Password Hashing
│   ├── crud.py          # Database CRUD operations
│   ├── database.py      # Database connection & session management
│   ├── main.py          # FastAPI application entry point
│   ├── models.py        # SQLAlchemy database models
│   ├── risk_engine.py   # Core Risk Assessment logic
│   ├── schemas.py       # Pydantic data validation models
│   ├── test_main.py     # Automated test suite
│   └── data/            # SQLite database storage
├── requirements.txt     # Project dependencies
└── README.md            # Project documentation
```

---

## 🔍 Core Features

### 1. Intelligent Risk Engine (`src/risk_engine.py`)
- **Automatic Assessment**: Analyzes Blood Pressure and Glucose levels to determine risk levels (High, Medium, Low).
- **Task Generation**: Automatically creates follow-up tasks based on the calculated risk level.

### 2. Secure Authentication (`src/auth.py`)
- **Doctor Login**: Secure login system for medical staff using JWT tokens.
- **Password Protection**: Uses `passlib` with SHA-256 hashing for secure password storage.

### 3. Comprehensive Patient Management
- **CRUD Operations**: Create, Read, Update, and List patients.
- **Global Follow-ups**: A centralized list for doctors to manage all pending follow-up tasks.

---

## 📡 API Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Key Endpoints
- `POST /token`: Login to get access token.
- `POST /patients/`: Register a new patient.
- `POST /indicators/`: Submit health data (triggers risk engine).
- `GET /followups/`: View all pending follow-up tasks.

---

## 🧪 Running Tests
```bash
pytest src/test_main.py -v
```

## 📈 Future Roadmap
- **Phase 3**: Generate 2,000+ simulated clinical records for performance testing.
- **Phase 4**: Implement advanced health trend analysis APIs.
- **Phase 5**: Integrate Power BI for community-wide health visualization.