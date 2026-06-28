# api/routes/agents.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from agents.symptom_checker import check_symptoms
from agents.drug_interaction import check_drug_interactions
from agents.appointment_scheduler import schedule_appointment

router = APIRouter()


# ── Symptom Checker Schema ────────────────────────────────────────────────────
class SymptomRequest(BaseModel):
    symptoms: str = Field(
        ...,
        min_length=5,
        description="Describe your symptoms in detail"
    )
    patient_age: Optional[int] = Field(default=None, ge=0, le=120)
    medical_history: Optional[str] = Field(
        default=None,
        description="Any relevant medical history"
    )


# ── Drug Interaction Schema ───────────────────────────────────────────────────
class DrugInteractionRequest(BaseModel):
    medications: List[str] = Field(
        ...,
        min_length=2,
        description="List of at least 2 medication names"
    )
    patient_age: Optional[int] = Field(default=None, ge=0, le=120)
    conditions: Optional[str] = Field(
        default=None,
        description="Existing medical conditions"
    )


# ── Symptom Checker Endpoint ──────────────────────────────────────────────────
@router.post(
    "/agents/symptom-check",
    summary="AI Symptom Checker Agent"
)
def symptom_check(request: SymptomRequest):
    """
    Runs the LangGraph symptom checker agent.
    Analyzes symptoms and returns structured triage assessment.

    ⚠️ Not a replacement for professional medical advice.
    """
    try:
        result = check_symptoms(
            symptoms=request.symptoms,
            patient_age=request.patient_age,
            medical_history=request.medical_history
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )


# ── Drug Interaction Endpoint ─────────────────────────────────────────────────
@router.post(
    "/agents/drug-interactions",
    summary="Drug Interaction Detector Agent"
)
def drug_interaction_check(request: DrugInteractionRequest):
    """
    Checks all combinations of provided medications for
    dangerous interactions using a LangGraph agent.

    ⚠️ Not a replacement for professional medical advice.
    """
    if len(request.medications) < 2:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least 2 medications to check."
        )

    try:
        result = check_drug_interactions(
            medications=request.medications,
            patient_age=request.patient_age,
            conditions=request.conditions
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )
    
    class AppointmentRequest(BaseModel):
    symptoms: str = Field(..., min_length=5)
    urgency_level: str = Field(
        ...,
        description="EMERGENCY, HIGH, MEDIUM, or LOW"
    )
    specialist_needed: str = Field(
        ...,
        description="Type of specialist needed"
    )
    possible_conditions: Optional[List[str]] = None
    patient_age: Optional[int] = Field(default=None, ge=0, le=120)

# Add new endpoint
@router.post(
    "/agents/schedule-appointment",
    summary="Appointment Scheduler Agent"
)
def appointment_schedule(request: AppointmentRequest):
    """
    Creates a complete appointment plan including:
    - Timeframe and appointment type
    - Scheduling steps
    - Preparation checklist
    - Questions to ask the doctor
    - Red flag warnings

    ⚠️ Not a replacement for professional medical advice.
    """
    valid_urgency = ["EMERGENCY", "HIGH", "MEDIUM", "LOW"]
    if request.urgency_level.upper() not in valid_urgency:
        raise HTTPException(
            status_code=400,
            detail=f"urgency_level must be one of: {valid_urgency}"
        )

    try:
        result = schedule_appointment(
            symptoms=request.symptoms,
            urgency_level=request.urgency_level.upper(),
            specialist_needed=request.specialist_needed,
            possible_conditions=request.possible_conditions,
            patient_age=request.patient_age
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )