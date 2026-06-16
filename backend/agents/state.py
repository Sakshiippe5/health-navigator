# agents/state.py
#
# RESPONSIBILITY: Define the STATE that flows through our agents.
#
# WHY a separate state file?
# Every node in a LangGraph graph reads from and writes to state.
# Defining it once here means every node imports the same structure.
# Think of state as the "memory" of the agent during one run.

from typing import TypedDict, List, Optional


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