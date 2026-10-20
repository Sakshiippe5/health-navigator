# api/routes/agents.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from agents.symptom_checker import check_symptoms
from agents.drug_interaction import check_drug_interactions
from agents.appointment_scheduler import schedule_appointment
from services.health_pipeline import run_health_pipeline
from services.document_service import save_agent_result, get_user_agent_results
from database.connection import get_db
from database.models import User
from core.dependencies import get_current_user

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class SymptomRequest(BaseModel):
    symptoms: str = Field(..., min_length=5)
    patient_age: Optional[int] = Field(default=None, ge=0, le=120)
    medical_history: Optional[str] = None


class DrugInteractionRequest(BaseModel):
    medications: List[str] = Field(..., min_length=2)
    patient_age: Optional[int] = Field(default=None, ge=0, le=120)
    conditions: Optional[str] = None


class AppointmentRequest(BaseModel):
    symptoms: str = Field(..., min_length=5)
    urgency_level: str = Field(..., description="EMERGENCY, HIGH, MEDIUM, or LOW")
    specialist_needed: str = Field(..., description="Type of specialist needed")
    possible_conditions: Optional[List[str]] = None
    patient_age: Optional[int] = Field(default=None, ge=0, le=120)


class HealthPipelineRequest(BaseModel):
    symptoms: str = Field(..., min_length=5)
    medications: Optional[List[str]] = None
    patient_age: Optional[int] = Field(default=None, ge=0, le=120)
    medical_history: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/agents/symptom-check", summary="AI Symptom Checker Agent")
def symptom_check(
    request: SymptomRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Runs the LangGraph symptom checker agent."""
    try:
        result = check_symptoms(
            symptoms=request.symptoms,
            patient_age=request.patient_age,
            medical_history=request.medical_history
        )

        save_agent_result(
            db=db,
            user_id=current_user.id,
            agent_type="symptom",
            input_data={
                "symptoms": request.symptoms,
                "patient_age": request.patient_age,
                "medical_history": request.medical_history
            },
            result_data=result,
            urgency_level=result.get("urgency_level")
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.post("/agents/drug-interactions", summary="Drug Interaction Detector")
def drug_interaction_check(
    request: DrugInteractionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Checks all medication combinations for dangerous interactions."""
    if len(request.medications) < 2:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least 2 medications."
        )

    try:
        result = check_drug_interactions(
            medications=request.medications,
            patient_age=request.patient_age,
            conditions=request.conditions
        )

        save_agent_result(
            db=db,
            user_id=current_user.id,
            agent_type="drug",
            input_data={
                "medications": request.medications,
                "patient_age": request.patient_age,
                "conditions": request.conditions
            },
            result_data=result,
            urgency_level=result.get("overall_risk")
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.post("/agents/schedule-appointment", summary="Appointment Scheduler Agent")
def appointment_schedule(
    request: AppointmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a complete appointment plan."""
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
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.post("/agents/health-assessment", summary="Complete Health Assessment Pipeline")
def complete_health_assessment(
    request: HealthPipelineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Runs ALL 3 agents and returns a unified report."""
    try:
        result = run_health_pipeline(
            symptoms=request.symptoms,
            medications=request.medications,
            patient_age=request.patient_age,
            medical_history=request.medical_history
        )

        save_agent_result(
            db=db,
            user_id=current_user.id,
            agent_type="pipeline",
            input_data={
                "symptoms": request.symptoms,
                "medications": request.medications,
                "patient_age": request.patient_age,
                "medical_history": request.medical_history
            },
            result_data=result,
            urgency_level=result.get("overall_urgency")
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@router.get("/agents/history", summary="Get past agent assessments")
def get_agent_history(
    agent_type: str = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the current user's past agent assessments."""
    results = get_user_agent_results(
        db=db,
        user_id=current_user.id,
        agent_type=agent_type,
        limit=limit
    )

    return {
        "total": len(results),
        "history": [
            {
                "id": r.id,
                "agent_type": r.agent_type,
                "urgency_level": r.urgency_level,
                "input_data": r.input_data,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in results
        ]
    }