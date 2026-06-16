# agents/symptom_checker.py
#
# THE SYMPTOM CHECKER AGENT
#
# This agent uses LangGraph to create a multi-step
# symptom assessment flow:
#
#   analyze_symptoms → [serious?] → follow_up → assess
#                    → [not serious?] → quick_assess
#
# Each step is a NODE. LangGraph decides which node
# runs next based on the current STATE.

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import SymptomCheckerState
from core.config import GROQ_API_KEY
import json
import re
from typing import Dict, Any

# ── Initialize LLM ────────────────────────────────────────────────────────────
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0.1    # Very low = consistent, focused medical responses
)


# ── Node 1: Analyze Symptoms ──────────────────────────────────────────────────

def analyze_symptoms(state: SymptomCheckerState) -> SymptomCheckerState:
    """
    NODE 1 — First step the agent takes.

    Reads the user's symptoms and determines:
    - Severity score (1-10)
    - Which body systems are involved
    - Whether we need follow-up questions

    Returns updated state with analysis results.
    """

    print(f"🔍 Agent: Analyzing symptoms...")

    symptoms = state["symptoms"]
    age = state.get("patient_age", "unknown")
    history = state.get("medical_history", "none provided")

    # Ask LLM to analyze symptoms in structured JSON format
    # We use JSON so we can parse the response programmatically
    prompt = f"""You are a medical triage assistant. Analyze these symptoms and respond ONLY with valid JSON.

Patient symptoms: {symptoms}
Patient age: {age}
Medical history: {history}

Respond with this exact JSON structure:
{{
    "severity_score": <number 1-10, where 10 is most severe>,
    "symptom_categories": [<list of body systems involved, e.g. "cardiac", "respiratory", "neurological">],
    "needs_followup": <true if you need more information, false if symptoms are clear>,
    "initial_concern": "<one sentence about what concerns you most>"
}}

ONLY return the JSON. No other text."""

    response = llm.invoke([HumanMessage(content=prompt)])

    # Parse the JSON response
    try:
        # Clean response — remove markdown code blocks if present
        raw = response.content.strip()
        raw = re.sub(r'```json|```', '', raw).strip()
        analysis = json.loads(raw)
    except json.JSONDecodeError:
        # If parsing fails, use safe defaults
        analysis = {
            "severity_score": 5,
            "symptom_categories": ["general"],
            "needs_followup": True,
            "initial_concern": "Unable to parse symptoms clearly"
        }

    # Update state with analysis results
    return {
        **state,                # keep everything already in state
        "severity_score": analysis.get("severity_score", 5),
        "symptom_categories": analysis.get("symptom_categories", []),
        "needs_followup": analysis.get("needs_followup", True),
        "current_step": "analyzed",
        "messages": state.get("messages", []) + [
            f"Analysis: severity={analysis.get('severity_score')}, "
            f"categories={analysis.get('symptom_categories')}"
        ]
    }


# ── Node 2: Generate Follow-up Questions ─────────────────────────────────────

def generate_followup(state: SymptomCheckerState) -> SymptomCheckerState:
    """
    NODE 2 — Only runs if needs_followup is True.

    Generates targeted follow-up questions based on
    the symptoms and categories detected in Node 1.

    In a real app, these questions would be sent to the user.
    For now, the LLM answers them too (simulating a patient).
    """

    print(f"❓ Agent: Generating follow-up questions...")

    symptoms = state["symptoms"]
    categories = state.get("symptom_categories", [])
    severity = state.get("severity_score", 5)

    prompt = f"""You are a medical triage assistant gathering more information.

Patient reported: {symptoms}
Concerning systems: {categories}
Initial severity: {severity}/10

Generate 3 targeted follow-up questions to better assess this patient.
Then provide realistic patient answers for each question.

Respond ONLY with valid JSON:
{{
    "questions": [
        "<question 1>",
        "<question 2>",
        "<question 3>"
    ],
    "patient_answers": "<realistic combined answer from patient>"
}}

ONLY return the JSON. No other text."""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        raw = re.sub(r'```json|```', '', raw).strip()
        followup = json.loads(raw)
    except json.JSONDecodeError:
        followup = {
            "questions": ["How long have you had these symptoms?"],
            "patient_answers": "About 2 hours"
        }

    return {
        **state,
        "follow_up_questions": followup.get("questions", []),
        "user_answers": followup.get("patient_answers", ""),
        "current_step": "followup_complete",
        "messages": state.get("messages", []) + [
            f"Follow-up questions generated: {len(followup.get('questions', []))}"
        ]
    }


# ── Node 3: Generate Final Assessment ────────────────────────────────────────

def generate_assessment(state: SymptomCheckerState) -> SymptomCheckerState:
    """
    NODE 3 — Final step for cases needing follow-up.

    Uses ALL collected information to generate:
    - List of possible conditions
    - Urgency level
    - Recommended action
    - Specialist needed
    """

    print(f"📋 Agent: Generating full assessment...")

    symptoms = state["symptoms"]
    severity = state.get("severity_score", 5)
    categories = state.get("symptom_categories", [])
    answers = state.get("user_answers", "")
    questions = state.get("follow_up_questions", [])

    prompt = f"""You are a medical triage assistant making a final assessment.

Original symptoms: {symptoms}
Severity score: {severity}/10
Body systems involved: {categories}
Follow-up questions asked: {questions}
Patient answers: {answers}

Based on ALL this information, provide a comprehensive triage assessment.

Respond ONLY with valid JSON:
{{
    "possible_conditions": [<list of 2-3 possible conditions>],
    "urgency_level": "<EMERGENCY|HIGH|MEDIUM|LOW>",
    "recommended_action": "<clear action for patient to take>",
    "specialist_needed": "<type of doctor, or 'General Practitioner'>",
    "reasoning": "<brief explanation of your assessment>"
}}

ONLY return the JSON. No other text."""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        raw = re.sub(r'```json|```', '', raw).strip()
        assessment = json.loads(raw)
    except json.JSONDecodeError:
        assessment = {
            "possible_conditions": ["Unknown - requires in-person evaluation"],
            "urgency_level": "MEDIUM",
            "recommended_action": "Please consult a doctor for proper evaluation",
            "specialist_needed": "General Practitioner",
            "reasoning": "Unable to make definitive assessment"
        }

    return {
        **state,
        "possible_conditions": assessment.get("possible_conditions", []),
        "urgency_level": assessment.get("urgency_level", "MEDIUM"),
        "recommended_action": assessment.get("recommended_action", ""),
        "specialist_needed": assessment.get("specialist_needed", ""),
        "current_step": "complete",
        "messages": state.get("messages", []) + [
            f"Assessment complete: urgency={assessment.get('urgency_level')}"
        ]
    }


# ── Node 4: Quick Assessment (for mild symptoms) ──────────────────────────────

def quick_assess(state: SymptomCheckerState) -> SymptomCheckerState:
    """
    NODE 4 — Runs when needs_followup is False.

    For clear, mild symptoms that don't need extra questions.
    Faster path through the graph.
    """

    print(f"⚡ Agent: Quick assessment for mild symptoms...")

    symptoms = state["symptoms"]
    severity = state.get("severity_score", 3)

    prompt = f"""You are a medical triage assistant. These symptoms appear mild and clear.

Symptoms: {symptoms}
Severity: {severity}/10

Provide a quick assessment.

Respond ONLY with valid JSON:
{{
    "possible_conditions": [<1-2 likely conditions>],
    "urgency_level": "LOW",
    "recommended_action": "<home care advice or when to see doctor>",
    "specialist_needed": "General Practitioner if needed",
    "reasoning": "<brief explanation>"
}}

ONLY return the JSON. No other text."""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        raw = re.sub(r'```json|```', '', raw).strip()
        assessment = json.loads(raw)
    except json.JSONDecodeError:
        assessment = {
            "possible_conditions": ["Minor illness"],
            "urgency_level": "LOW",
            "recommended_action": "Rest and monitor symptoms",
            "specialist_needed": "General Practitioner if no improvement",
            "reasoning": "Mild symptoms"
        }

    return {
        **state,
        "possible_conditions": assessment.get("possible_conditions", []),
        "urgency_level": assessment.get("urgency_level", "LOW"),
        "recommended_action": assessment.get("recommended_action", ""),
        "specialist_needed": assessment.get("specialist_needed", ""),
        "current_step": "complete",
        "messages": state.get("messages", []) + ["Quick assessment complete"]
    }


# ── Router Function ───────────────────────────────────────────────────────────

def route_after_analysis(state: SymptomCheckerState) -> str:
    """
    ROUTER — Decides which node runs after analyze_symptoms.

    This is the "brain" of the graph — it reads the state
    and returns the NAME of the next node to run.

    LangGraph calls this after analyze_symptoms completes
    and routes to the returned node name.
    """

    severity = state.get("severity_score", 5)
    needs_followup = state.get("needs_followup", True)

    # High severity → always do full follow-up
    if severity >= 7:
        print(f"🚨 High severity ({severity}/10) → full follow-up")
        return "generate_followup"

    # Medium severity + needs follow-up → get more info
    if needs_followup and severity >= 4:
        print(f"⚠️ Medium severity ({severity}/10) → follow-up needed")
        return "generate_followup"

    # Low severity, clear symptoms → quick path
    print(f"✅ Low severity ({severity}/10) → quick assessment")
    return "quick_assess"


# ── Build the Graph ───────────────────────────────────────────────────────────

def build_symptom_checker() -> StateGraph:
    """
    Assembles all nodes and edges into a LangGraph graph.

    GRAPH STRUCTURE:
    START → analyze_symptoms → [router] → generate_followup → generate_assessment → END
                                       → quick_assess → END
    """

    # Create the graph with our state type
    graph = StateGraph(SymptomCheckerState)

    # Add all nodes
    # Each node is a function that takes state and returns updated state
    graph.add_node("analyze_symptoms", analyze_symptoms)
    graph.add_node("generate_followup", generate_followup)
    graph.add_node("generate_assessment", generate_assessment)
    graph.add_node("quick_assess", quick_assess)

    # Define edges (flow between nodes)
    # set_entry_point = first node to run
    graph.set_entry_point("analyze_symptoms")

    # Conditional edge — router function decides next node
    graph.add_conditional_edges(
        "analyze_symptoms",        # from this node
        route_after_analysis,      # call this function to decide
        {
            # function return value → node name to go to
            "generate_followup": "generate_followup",
            "quick_assess": "quick_assess"
        }
    )

    # Fixed edges — always go to these nodes after
    graph.add_edge("generate_followup", "generate_assessment")
    graph.add_edge("generate_assessment", END)
    graph.add_edge("quick_assess", END)

    # Compile = validate and prepare the graph for execution
    return graph.compile()


# ── Public Function ───────────────────────────────────────────────────────────

def check_symptoms(
    symptoms: str,
    patient_age: int = None,
    medical_history: str = None
) -> Dict[str, Any]:
    """
    Main entry point for the symptom checker.
    This is what the API route will call.

    Args:
        symptoms: Patient's described symptoms
        patient_age: Optional age
        medical_history: Optional medical history

    Returns:
        Complete assessment dict
    """

    # Build the graph
    app = build_symptom_checker()

    # Initial state — only input fields filled
    initial_state = {
        "symptoms": symptoms,
        "patient_age": patient_age,
        "medical_history": medical_history,
        "messages": [],
        "current_step": "start",
        # All other fields start as None
        "severity_score": None,
        "symptom_categories": None,
        "needs_followup": None,
        "follow_up_questions": None,
        "user_answers": None,
        "possible_conditions": None,
        "urgency_level": None,
        "recommended_action": None,
        "specialist_needed": None,
        "error": None,
    }

    # Run the graph — LangGraph handles the flow automatically
    final_state = app.invoke(initial_state)

    # Return clean result
    return {
        "symptoms_reported": symptoms,
        "severity_score": final_state.get("severity_score"),
        "symptom_categories": final_state.get("symptom_categories"),
        "follow_up_questions": final_state.get("follow_up_questions"),
        "possible_conditions": final_state.get("possible_conditions"),
        "urgency_level": final_state.get("urgency_level"),
        "recommended_action": final_state.get("recommended_action"),
        "specialist_needed": final_state.get("specialist_needed"),
        "steps_taken": final_state.get("messages", []),
    }