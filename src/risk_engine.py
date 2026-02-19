from datetime import datetime, timedelta, timezone
try:
    from . import models
except ImportError:
    import models

def calculate_risk_level(sys_bp: int, dia_bp: int, glucose: float) -> str:
    """
    Calculate risk level based on blood pressure and glucose (US-04).
    Standard reference:
    - High: sys >= 160 or dia >= 100 or glucose >= 11.1
    - Med: 140 <= sys < 160 or 90 <= dia < 100 or 7.0 <= glucose < 11.1
    - Low: Otherwise
    """
    if sys_bp >= 160 or dia_bp >= 100 or glucose >= 11.1:
        return "High"
    elif sys_bp >= 140 or dia_bp >= 90 or (7.0 <= glucose < 11.1):
        return "Med"
    else:
        return "Low"

def generate_follow_up_task(patient_id: int, risk_level: str) -> models.FollowUp:
    """
    Automatically generate follow-up task based on risk level (US-07).
    - High: Follow-up within 3 days
    - Med: Follow-up within 7 days
    - Low: Follow-up within 30 days (Routine check)
    """
    now = datetime.now(timezone.utc)
    if risk_level == "High":
        due_date = now + timedelta(days=3)
        description = "Urgent follow-up required due to high risk indicators."
    elif risk_level == "Med":
        due_date = now + timedelta(days=7)
        description = "Routine follow-up for medium risk monitoring."
    else:
        due_date = now + timedelta(days=30)
        description = "Standard monthly health check."

    return models.FollowUp(
        patient_id=patient_id,
        task_description=description,
        status="Pending",
        due_date=due_date
    )
