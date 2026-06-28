# agents/state.py
#
# RESPONSIBILITY: Define the STATE that flows through our agents.
#
# WHY a separate state file?
# Every node in a LangGraph graph reads from and writes to state.
# Defining it once here means every node imports the same structure.
# Think of state as the "memory" of the agent during one run.

from typing import TypedDict, List, Optional, Dict


class SymptomCheckerState(TypedDict):
    """
    State for the Symptom Checker Agent.
    Every field is optional because different nodes fill different parts.

    Flow:
    Node 1 (analyze)    → fills: symptoms, severity_score
    Node 2 (follow_up)  → fills: follow_up_questions, user_answers
    Node 3 (assess)     → fills: assessment, recommendation, urgency_level
    """

    # Input
    symptoms: str                          # what user described
    patient_age: Optional[int]             # if provided
    medical_history: Optional[str]         # if provided

    # Filled by analyze node
    severity_score: Optional[int]          # 1-10 scale
    symptom_categories: Optional[List[str]] # ["cardiac", "respiratory"]
    needs_followup: Optional[bool]         # does agent need more info?

    # Filled by follow_up node
    follow_up_questions: Optional[List[str]]  # questions to ask user
    user_answers: Optional[str]               # user's responses

    # Filled by assess node
    possible_conditions: Optional[List[str]]
    recommended_action: Optional[str]
    urgency_level: Optional[str]           # EMERGENCY/HIGH/MEDIUM/LOW
    specialist_needed: Optional[str]       # "Cardiologist", "GP", etc.

    # Internal tracking
    messages: List[str]                    # conversation so far
    current_step: Optional[str]            # which node we're in
    error: Optional[str]                   # if something went wrong


    # Add to agents/state.py

class DrugInteractionState(TypedDict):
    """
    State for the Drug Interaction Detector Agent.

    Flow:
    Node 1 (validate)  → fills: validated_drugs, invalid_drugs
    Node 2 (check)     → fills: interactions, has_dangerous
    Node 3 (report)    → fills: final_report, overall_risk
    """

    # Input
    medications: List[str]           # raw drug names from user
    patient_age: Optional[int]
    conditions: Optional[str]        # existing medical conditions

    # Filled by validate node
    validated_drugs: Optional[List[str]]   # cleaned drug names
    invalid_drugs: Optional[List[str]]     # unrecognized names

    # Filled by check node
    interactions: Optional[List[Dict]]     # list of interaction objects
    has_dangerous: Optional[bool]          # any severe interactions?
    checked_pairs: Optional[List[str]]     # pairs we checked

    # Filled by report node
    final_report: Optional[str]            # human readable summary
    overall_risk: Optional[str]            # SAFE/LOW/MODERATE/HIGH/CRITICAL
    recommendations: Optional[List[str]]   # action items for patient

    # Internal
    messages: List[str]
    current_step: Optional[str]
    error: Optional[str]

    class AppointmentSchedulerState(TypedDict):
        """
        State for the Appointment Scheduler Agent.

        Can work standalone OR receive input from Symptom Checker.

        Flow:
        Node 1 (assess_urgency)   → fills: timeframe, appointment_type
        Node 2a (emergency_plan)  → fills: emergency_steps
        Node 2b (routine_schedule)→ fills: scheduling_options
        Node 3 (prepare_patient)  → fills: preparation, questions, red_flags
        """

    # Input — can come from symptom checker or directly
    symptoms: str
    urgency_level: str              # EMERGENCY/HIGH/MEDIUM/LOW
    specialist_needed: str          # "Cardiologist", "GP", etc.
    possible_conditions: Optional[List[str]]
    patient_age: Optional[int]
    location: Optional[str]         # for future use

    # Filled by assess_urgency
    timeframe: Optional[str]        # "Within 2 hours", "Within a week"
    appointment_type: Optional[str] # "Emergency", "Urgent", "Routine"
    is_emergency: Optional[bool]    # routes the graph

    # Filled by emergency_plan OR routine_schedule
    scheduling_steps: Optional[List[str]]   # what to do right now
    scheduling_options: Optional[List[str]] # types of appointments available

    # Filled by prepare_patient
    preparation_steps: Optional[List[str]]  # what to do before appointment
    questions_to_ask: Optional[List[str]]   # ask the doctor
    red_flags: Optional[List[str]]          # go to ER if these happen
    what_to_bring: Optional[List[str]]      # documents, reports, medications

    # Internal
    messages: List[str]
    current_step: Optional[str]
    error: Optional[str]