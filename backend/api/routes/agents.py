# api/routes/agents.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from agents.symptom_checker import check_symptoms

router = APIRouter()


class SymptomRequest(BaseModel):
    symptoms: str = Field(
        ...,
        min_length=5,
        description="Describe your symptoms in detail"
    )
    patient_age: Optional[int] = Field(
        default=None,
        ge=0,
        le=120
    )
    medical_history: Optional[str] = Field(
        default=None,
        description="Any relevant medical history"
    )


@router.post("/agents/symptom-check",
             summary="AI Symptom Checker Agent")
def symptom_check(request: SymptomRequest):
    """
    Runs the LangGraph symptom checker agent.
    The agent analyzes symptoms, asks follow-up questions
    if needed, and returns a structured assessment.

    ⚠️ This is NOT a replacement for professional medical advice.
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
    