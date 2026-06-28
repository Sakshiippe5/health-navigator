# agents/appointment_scheduler.py
#
# APPOINTMENT SCHEDULER AGENT
#
# Flow:
#   assess_urgency → [router] → emergency_plan    → prepare_patient → END
#                             → routine_schedule  → prepare_patient → END
#
# This agent can work:
#   1. Standalone — user provides symptoms + urgency directly
#   2. Connected — receives output from Symptom Checker agent

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from agents.state import AppointmentSchedulerState
from core.config import GROQ_API_KEY
import json
import re
from typing import Dict, Any, List

# ── Initialize LLM ────────────────────────────────────────────────────────────
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0.1
)


# ── Node 1: Assess Urgency ────────────────────────────────────────────────────

def assess_urgency(state: AppointmentSchedulerState) -> AppointmentSchedulerState:
    """
    NODE 1 — Converts urgency level into concrete timeframe.

    Maps abstract urgency to real scheduling decisions:
    EMERGENCY → call ambulance now
    HIGH      → see doctor within 24 hours
    MEDIUM    → appointment within 1 week
    LOW       → routine appointment within 1 month
    """

    print(f"⏰ Scheduler: Assessing urgency level: {state['urgency_level']}...")

    urgency = state["urgency_level"].upper()
    specialist = state["specialist_needed"]
    symptoms = state["symptoms"]
    conditions = state.get("possible_conditions", [])

    prompt = f"""You are a medical scheduling coordinator.

Patient information:
- Symptoms: {symptoms}
- Urgency level: {urgency}
- Specialist needed: {specialist}
- Possible conditions: {conditions}
- Patient age: {state.get('patient_age', 'unknown')}

Determine the appropriate appointment scheduling parameters.

Respond ONLY with valid JSON:
{{
    "timeframe": "<specific timeframe e.g. 'Immediately - call 911', 'Within 24 hours', 'Within 3-5 days', 'Within 2-4 weeks'>",
    "appointment_type": "<Emergency Room|Urgent Care|Priority Consultation|Routine Consultation>",
    "is_emergency": <true if EMERGENCY or HIGH severity, false otherwise>,
    "reasoning": "<one sentence explaining the urgency assessment>"
}}

ONLY return JSON. No other text."""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        raw = re.sub(r'```json|```', '', raw).strip()
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Safe defaults based on urgency
        is_emergency = urgency in ["EMERGENCY", "HIGH"]
        result = {
            "timeframe": "Immediately" if is_emergency else "Within 1 week",
            "appointment_type": "Emergency Room" if is_emergency else "Routine Consultation",
            "is_emergency": is_emergency,
            "reasoning": "Default assessment"
        }

    print(f"📅 Timeframe: {result.get('timeframe')}")
    print(f"🏥 Type: {result.get('appointment_type')}")

    return {
        **state,
        "timeframe": result.get("timeframe"),
        "appointment_type": result.get("appointment_type"),
        "is_emergency": result.get("is_emergency", False),
        "current_step": "urgency_assessed",
        "messages": state.get("messages", []) + [
            f"Urgency assessed: {result.get('appointment_type')} — {result.get('timeframe')}"
        ]
    }


# ── Node 2a: Emergency Plan ───────────────────────────────────────────────────

def emergency_plan(state: AppointmentSchedulerState) -> AppointmentSchedulerState:
    """
    NODE 2a — For EMERGENCY and HIGH urgency cases.

    Provides immediate action steps — what to do RIGHT NOW.
    No scheduling options — this is crisis management.
    """

    print(f"🚨 Scheduler: Creating emergency plan...")

    prompt = f"""You are a medical emergency coordinator.

Patient has {state['urgency_level']} urgency symptoms: {state['symptoms']}
Specialist needed: {state['specialist_needed']}
Possible conditions: {state.get('possible_conditions', [])}
Timeframe: {state.get('timeframe')}

Create an immediate action plan for this patient.

Respond ONLY with valid JSON:
{{
    "immediate_steps": [
        "<step 1 — most urgent first>",
        "<step 2>",
        "<step 3>",
        "<step 4>"
    ],
    "who_to_call": "<specific instruction e.g. 'Call 911 immediately' or 'Call your cardiologist's emergency line'>",
    "while_waiting": [
        "<what to do while waiting for help>",
        "<another action>"
    ]
}}

ONLY return JSON. No other text."""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        raw = re.sub(r'```json|```', '', raw).strip()
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "immediate_steps": ["Call emergency services immediately"],
            "who_to_call": "Call 911",
            "while_waiting": ["Stay calm", "Do not drive yourself"]
        }

    # Combine into scheduling_steps
    all_steps = result.get("immediate_steps", [])
    all_steps.insert(0, result.get("who_to_call", "Call emergency services"))
    all_steps.extend([f"While waiting: {s}" for s in result.get("while_waiting", [])])

    return {
        **state,
        "scheduling_steps": all_steps,
        "scheduling_options": ["Emergency Room", "Call 911", "Urgent Care"],
        "current_step": "emergency_planned",
        "messages": state.get("messages", []) + ["Emergency plan created"]
    }


# ── Node 2b: Routine Schedule ─────────────────────────────────────────────────

def routine_schedule(state: AppointmentSchedulerState) -> AppointmentSchedulerState:
    """
    NODE 2b — For MEDIUM and LOW urgency cases.

    Provides scheduling options and booking guidance.
    More relaxed — patient has time to plan properly.
    """

    print(f"📅 Scheduler: Creating routine schedule...")

    prompt = f"""You are a medical scheduling coordinator.

Patient needs a {state['appointment_type']} with a {state['specialist_needed']}.
Symptoms: {state['symptoms']}
Timeframe: {state.get('timeframe')}
Patient age: {state.get('patient_age', 'unknown')}

Create a practical scheduling plan.

Respond ONLY with valid JSON:
{{
    "scheduling_steps": [
        "<step 1 to book appointment>",
        "<step 2>",
        "<step 3>"
    ],
    "scheduling_options": [
        "<option 1 e.g. 'Book through your GP referral'>",
        "<option 2 e.g. 'Call specialist clinic directly'>",
        "<option 3 e.g. 'Use online booking portal'>"
    ],
    "timing_advice": "<specific advice about when to book>"
}}

ONLY return JSON. No other text."""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        raw = re.sub(r'```json|```', '', raw).strip()
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "scheduling_steps": [
                "Contact your GP for a referral",
                f"Ask for {state['specialist_needed']} referral",
                f"Book appointment within {state.get('timeframe', '1 week')}"
            ],
            "scheduling_options": [
                "GP referral",
                "Direct specialist booking",
                "Online portal"
            ],
            "timing_advice": f"Book within {state.get('timeframe', '1 week')}"
        }

    return {
        **state,
        "scheduling_steps": result.get("scheduling_steps", []),
        "scheduling_options": result.get("scheduling_options", []),
        "current_step": "routine_scheduled",
        "messages": state.get("messages", []) + ["Routine schedule created"]
    }


# ── Node 3: Prepare Patient ───────────────────────────────────────────────────

def prepare_patient(state: AppointmentSchedulerState) -> AppointmentSchedulerState:
    """
    NODE 3 — Final node for ALL cases.

    Generates preparation checklist:
    - What to bring to appointment
    - How to prepare physically
    - Questions to ask the doctor
    - Red flags to watch for
    """

    print(f"📋 Scheduler: Preparing patient checklist...")

    prompt = f"""You are a medical coordinator preparing a patient for their appointment.

Appointment details:
- Specialist: {state['specialist_needed']}
- Type: {state.get('appointment_type')}
- Symptoms: {state['symptoms']}
- Possible conditions: {state.get('possible_conditions', [])}
- Patient age: {state.get('patient_age', 'unknown')}

Create a comprehensive preparation guide.

Respond ONLY with valid JSON:
{{
    "what_to_bring": [
        "<document or item 1>",
        "<document or item 2>",
        "<document or item 3>",
        "<document or item 4>"
    ],
    "preparation_steps": [
        "<how to prepare physically/mentally>",
        "<dietary or activity restrictions>",
        "<medication instructions>"
    ],
    "questions_to_ask": [
        "<important question 1 for the specialist>",
        "<important question 2>",
        "<important question 3>",
        "<important question 4>"
    ],
    "red_flags": [
        "<symptom that means go to ER immediately>",
        "<another warning sign>"
    ]
}}

ONLY return JSON. No other text."""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        raw = re.sub(r'```json|```', '', raw).strip()
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "what_to_bring": [
                "List of current medications",
                "Previous medical reports",
                "Insurance documents",
                "Photo ID"
            ],
            "preparation_steps": ["Get adequate rest before appointment"],
            "questions_to_ask": [
                "What is the diagnosis?",
                "What are my treatment options?"
            ],
            "red_flags": ["Seek emergency care if symptoms worsen significantly"]
        }

    return {
        **state,
        "what_to_bring": result.get("what_to_bring", []),
        "preparation_steps": result.get("preparation_steps", []),
        "questions_to_ask": result.get("questions_to_ask", []),
        "red_flags": result.get("red_flags", []),
        "current_step": "complete",
        "messages": state.get("messages", []) + [
            "Patient preparation complete"
        ]
    }


# ── Router ────────────────────────────────────────────────────────────────────

def route_by_urgency(state: AppointmentSchedulerState) -> str:
    """
    Routes to emergency_plan or routine_schedule
    based on is_emergency flag set in Node 1.
    """
    if state.get("is_emergency"):
        print("🚨 Routing to emergency plan")
        return "emergency_plan"
    else:
        print("📅 Routing to routine schedule")
        return "routine_schedule"


# ── Build Graph ───────────────────────────────────────────────────────────────

def build_appointment_scheduler():
    """
    Graph structure:
    assess_urgency → [router] → emergency_plan   → prepare_patient → END
                              → routine_schedule → prepare_patient → END

    Note: prepare_patient is shared by BOTH paths.
    This is called a "merge" — two paths converging to one node.
    """

    graph = StateGraph(AppointmentSchedulerState)

    # Add all nodes
    graph.add_node("assess_urgency", assess_urgency)
    graph.add_node("emergency_plan", emergency_plan)
    graph.add_node("routine_schedule", routine_schedule)
    graph.add_node("prepare_patient", prepare_patient)

    # Entry point
    graph.set_entry_point("assess_urgency")

    # Conditional routing after urgency assessment
    graph.add_conditional_edges(
        "assess_urgency",
        route_by_urgency,
        {
            "emergency_plan": "emergency_plan",
            "routine_schedule": "routine_schedule"
        }
    )

    # Both paths merge into prepare_patient
    graph.add_edge("emergency_plan", "prepare_patient")
    graph.add_edge("routine_schedule", "prepare_patient")
    graph.add_edge("prepare_patient", END)

    return graph.compile()


# ── Public Function ───────────────────────────────────────────────────────────

def schedule_appointment(
    symptoms: str,
    urgency_level: str,
    specialist_needed: str,
    possible_conditions: List[str] = None,
    patient_age: int = None,
) -> Dict[str, Any]:
    """
    Main entry point for the appointment scheduler.
    Can receive output directly from symptom checker.
    """

    app = build_appointment_scheduler()

    initial_state = {
        "symptoms": symptoms,
        "urgency_level": urgency_level,
        "specialist_needed": specialist_needed,
        "possible_conditions": possible_conditions or [],
        "patient_age": patient_age,
        "location": None,
        "messages": [],
        "current_step": "start",
        "timeframe": None,
        "appointment_type": None,
        "is_emergency": None,
        "scheduling_steps": None,
        "scheduling_options": None,
        "preparation_steps": None,
        "questions_to_ask": None,
        "red_flags": None,
        "what_to_bring": None,
        "error": None,
    }

    final_state = app.invoke(initial_state)

    return {
        "specialist_needed": specialist_needed,
        "urgency_level": urgency_level,
        "timeframe": final_state.get("timeframe"),
        "appointment_type": final_state.get("appointment_type"),
        "is_emergency": final_state.get("is_emergency"),
        "scheduling": {
            "steps": final_state.get("scheduling_steps", []),
            "options": final_state.get("scheduling_options", [])
        },
        "preparation": {
            "what_to_bring": final_state.get("what_to_bring", []),
            "steps": final_state.get("preparation_steps", []),
            "questions_to_ask": final_state.get("questions_to_ask", []),
            "red_flags": final_state.get("red_flags", [])
        },
        "steps_taken": final_state.get("messages", [])
    }