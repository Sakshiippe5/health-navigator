# agents/state.py
from typing import TypedDict, List, Optional, Dict


class SymptomCheckerState(TypedDict):
    """State for the Symptom Checker Agent."""

    # Input
    symptoms: str
    patient_age: Optional[int]
    medical_history: Optional[str]

    # Filled by analyze node
    severity_score: Optional[int]
    symptom_categories: Optional[List[str]]
    needs_followup: Optional[bool]

    # Filled by follow_up node
    follow_up_questions: Optional[List[str]]
    user_answers: Optional[str]

    # Filled by assess node
    possible_conditions: Optional[List[str]]
    recommended_action: Optional[str]
    urgency_level: Optional[str]
    specialist_needed: Optional[str]

    # Internal
    messages: List[str]
    current_step: Optional[str]
    error: Optional[str]


class DrugInteractionState(TypedDict):
    """State for the Drug Interaction Detector Agent."""

    # Input
    medications: List[str]
    patient_age: Optional[int]
    conditions: Optional[str]

    # Filled by validate node
    validated_drugs: Optional[List[str]]
    invalid_drugs: Optional[List[str]]

    # Filled by check node
    interactions: Optional[List[Dict]]
    has_dangerous: Optional[bool]
    checked_pairs: Optional[List[str]]

    # Filled by report node
    final_report: Optional[str]
    overall_risk: Optional[str]
    recommendations: Optional[List[str]]

    # Internal
    messages: List[str]
    current_step: Optional[str]
    error: Optional[str]


class AppointmentSchedulerState(TypedDict):
    """State for the Appointment Scheduler Agent."""

    # Input
    symptoms: str
    urgency_level: str
    specialist_needed: str
    possible_conditions: Optional[List[str]]
    patient_age: Optional[int]
    location: Optional[str]

    # Filled by assess_urgency
    timeframe: Optional[str]
    appointment_type: Optional[str]
    is_emergency: Optional[bool]

    # Filled by emergency_plan OR routine_schedule
    scheduling_steps: Optional[List[str]]
    scheduling_options: Optional[List[str]]

    # Filled by prepare_patient
    preparation_steps: Optional[List[str]]
    questions_to_ask: Optional[List[str]]
    red_flags: Optional[List[str]]
    what_to_bring: Optional[List[str]]

    # Internal
    messages: List[str]
    current_step: Optional[str]
    error: Optional[str]