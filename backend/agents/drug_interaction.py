# agents/drug_interaction.py
#
# DRUG INTERACTION DETECTOR AGENT
#
# Flow:
#   validate_drugs → check_interactions → generate_report → END
#
# Unlike symptom checker, this has NO conditional routing —
# every drug list goes through all 3 nodes.
# The complexity is INSIDE the nodes, not in the routing.

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from agents.state import DrugInteractionState
from core.config import GROQ_API_KEY
from itertools import combinations
import json
import re
from typing import Dict, Any, List

# ── Initialize LLM ────────────────────────────────────────────────────────────
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0.1
)


# ── Node 1: Validate Drugs ────────────────────────────────────────────────────

def validate_drugs(state: DrugInteractionState) -> DrugInteractionState:
    """
    NODE 1 — Validates and normalizes drug names.

    WHY validation first?
    Users might type: "metformin", "Metformin", "metformin 500mg"
    We need clean, normalized names before checking interactions.
    Also catches typos and non-drug inputs.
    """

    print(f"💊 Agent: Validating {len(state['medications'])} medications...")

    medications = state["medications"]

    prompt = f"""You are a pharmacist validating medication names.

Medications provided: {medications}

For each medication:
1. Check if it's a real medication name
2. Normalize to the standard generic name
3. Flag any that aren't recognizable medications

Respond ONLY with valid JSON:
{{
    "validated_drugs": [<list of normalized, valid drug names>],
    "invalid_drugs": [<list of unrecognized inputs>],
    "normalization_notes": "<brief note about any name changes made>"
}}

ONLY return the JSON. No other text."""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        raw = re.sub(r'```json|```', '', raw).strip()
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback — use original names
        result = {
            "validated_drugs": medications,
            "invalid_drugs": [],
            "normalization_notes": "Could not validate"
        }

    print(f"✅ Validated: {result.get('validated_drugs')}")
    if result.get('invalid_drugs'):
        print(f"⚠️ Invalid: {result.get('invalid_drugs')}")

    return {
        **state,
        "validated_drugs": result.get("validated_drugs", medications),
        "invalid_drugs": result.get("invalid_drugs", []),
        "current_step": "validated",
        "messages": state.get("messages", []) + [
            f"Validated {len(result.get('validated_drugs', []))} drugs"
        ]
    }


# ── Node 2: Check Interactions ────────────────────────────────────────────────

def check_interactions(state: DrugInteractionState) -> DrugInteractionState:
    """
    NODE 2 — Core detection logic.

    Checks EVERY pair of drugs for interactions.
    Uses itertools.combinations to generate all pairs.

    For each pair → one LLM call → structured interaction result.

    WHY check pairs individually?
    More accurate than asking about all drugs at once.
    Each pair gets focused attention from the LLM.
    """

    validated_drugs = state.get("validated_drugs", [])
    print(f"🔍 Agent: Checking interactions for {validated_drugs}...")

    # Handle edge case — need at least 2 drugs
    if len(validated_drugs) < 2:
        return {
            **state,
            "interactions": [],
            "has_dangerous": False,
            "checked_pairs": [],
            "current_step": "checked",
            "messages": state.get("messages", []) + [
                "Only one drug — no interactions to check"
            ]
        }

    # Generate ALL pairs using itertools.combinations
    # combinations(["A","B","C"], 2) → [("A","B"), ("A","C"), ("B","C")]
    drug_pairs = list(combinations(validated_drugs, 2))
    print(f"🔢 Checking {len(drug_pairs)} pairs...")

    all_interactions = []
    checked_pairs = []
    has_dangerous = False

    for drug1, drug2 in drug_pairs:
        pair_str = f"{drug1} + {drug2}"
        checked_pairs.append(pair_str)

        prompt = f"""You are a clinical pharmacist checking drug interactions.

Drug pair to check: {drug1} and {drug2}
Patient age: {state.get('patient_age', 'unknown')}
Patient conditions: {state.get('conditions', 'none provided')}

Analyze the interaction between these two specific drugs.

Respond ONLY with valid JSON:
{{
    "drug1": "{drug1}",
    "drug2": "{drug2}",
    "interaction_exists": <true or false>,
    "severity": "<NONE|MILD|MODERATE|SEVERE|CONTRAINDICATED>",
    "mechanism": "<how the interaction works, or null if none>",
    "clinical_effect": "<what happens to the patient, or null if none>",
    "recommendation": "<what doctor/patient should do>"
}}

ONLY return the JSON. No other text."""

        response = llm.invoke([HumanMessage(content=prompt)])

        try:
            raw = response.content.strip()
            raw = re.sub(r'```json|```', '', raw).strip()
            interaction = json.loads(raw)
        except json.JSONDecodeError:
            interaction = {
                "drug1": drug1,
                "drug2": drug2,
                "interaction_exists": False,
                "severity": "NONE",
                "mechanism": None,
                "clinical_effect": None,
                "recommendation": "Could not analyze — consult pharmacist"
            }

        # Track if any dangerous interactions found
        if interaction.get("severity") in ["SEVERE", "CONTRAINDICATED"]:
            has_dangerous = True
            print(f"🚨 DANGEROUS: {pair_str} — {interaction.get('severity')}")
        elif interaction.get("interaction_exists"):
            print(f"⚠️ Interaction: {pair_str} — {interaction.get('severity')}")
        else:
            print(f"✅ Safe: {pair_str}")

        all_interactions.append(interaction)

    return {
        **state,
        "interactions": all_interactions,
        "has_dangerous": has_dangerous,
        "checked_pairs": checked_pairs,
        "current_step": "checked",
        "messages": state.get("messages", []) + [
            f"Checked {len(drug_pairs)} pairs",
            f"Dangerous interactions: {has_dangerous}"
        ]
    }


# ── Node 3: Generate Report ───────────────────────────────────────────────────

def generate_report(state: DrugInteractionState) -> DrugInteractionState:
    """
    NODE 3 — Creates final human-readable report.

    Takes all interaction data and synthesizes:
    - Overall risk level
    - Clear recommendations
    - Patient-friendly summary
    """

    print(f"📋 Agent: Generating final report...")

    interactions = state.get("interactions", [])
    validated_drugs = state.get("validated_drugs", [])
    invalid_drugs = state.get("invalid_drugs", [])
    has_dangerous = state.get("has_dangerous", False)

    # Filter only real interactions
    real_interactions = [
        i for i in interactions
        if i.get("interaction_exists")
    ]

    prompt = f"""You are a clinical pharmacist writing a medication safety report.

Medications analyzed: {validated_drugs}
Unrecognized inputs: {invalid_drugs}
Interactions found: {json.dumps(real_interactions, indent=2)}
Has dangerous interactions: {has_dangerous}

Write a clear, actionable medication safety report.

Respond ONLY with valid JSON:
{{
    "overall_risk": "<SAFE|LOW|MODERATE|HIGH|CRITICAL>",
    "summary": "<2-3 sentence plain English summary for patient>",
    "recommendations": [
        "<specific action item 1>",
        "<specific action item 2>",
        "<specific action item 3>"
    ],
    "urgent_warning": "<null if no urgent concerns, or critical warning if dangerous>"
}}

ONLY return the JSON. No other text."""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        raw = re.sub(r'```json|```', '', raw).strip()
        report = json.loads(raw)
    except json.JSONDecodeError:
        report = {
            "overall_risk": "MODERATE",
            "summary": "Unable to generate complete report. Please consult your pharmacist.",
            "recommendations": ["Consult your doctor or pharmacist"],
            "urgent_warning": None
        }

    return {
        **state,
        "final_report": report.get("summary"),
        "overall_risk": report.get("overall_risk"),
        "recommendations": report.get("recommendations", []),
        "current_step": "complete",
        "messages": state.get("messages", []) + [
            f"Report complete: overall_risk={report.get('overall_risk')}"
        ]
    }


# ── Build the Graph ───────────────────────────────────────────────────────────

def build_drug_interaction_checker():
    """
    Simple linear graph — no conditional routing needed.
    Every drug list goes through all 3 nodes.

    validate → check → report → END
    """

    graph = StateGraph(DrugInteractionState)

    # Add nodes
    graph.add_node("validate_drugs", validate_drugs)
    graph.add_node("check_interactions", check_interactions)
    graph.add_node("generate_report", generate_report)

    # Linear edges — no branching needed here
    graph.set_entry_point("validate_drugs")
    graph.add_edge("validate_drugs", "check_interactions")
    graph.add_edge("check_interactions", "generate_report")
    graph.add_edge("generate_report", END)

    return graph.compile()


# ── Public Function ───────────────────────────────────────────────────────────

def check_drug_interactions(
    medications: List[str],
    patient_age: int = None,
    conditions: str = None
) -> Dict[str, Any]:
    """
    Main entry point for the drug interaction detector.
    Called by the API route.
    """

    app = build_drug_interaction_checker()

    initial_state = {
        "medications": medications,
        "patient_age": patient_age,
        "conditions": conditions,
        "messages": [],
        "current_step": "start",
        "validated_drugs": None,
        "invalid_drugs": None,
        "interactions": None,
        "has_dangerous": None,
        "checked_pairs": None,
        "final_report": None,
        "overall_risk": None,
        "recommendations": None,
        "error": None,
    }

    final_state = app.invoke(initial_state)

    # Separate interactions by severity for cleaner response
    all_interactions = final_state.get("interactions", [])
    dangerous = [i for i in all_interactions if i.get("severity") in ["SEVERE", "CONTRAINDICATED"]]
    moderate = [i for i in all_interactions if i.get("severity") == "MODERATE"]
    mild = [i for i in all_interactions if i.get("severity") == "MILD"]

    return {
        "medications_analyzed": final_state.get("validated_drugs"),
        "unrecognized_inputs": final_state.get("invalid_drugs"),
        "overall_risk": final_state.get("overall_risk"),
        "summary": final_state.get("final_report"),
        "recommendations": final_state.get("recommendations"),
        "has_dangerous_interactions": final_state.get("has_dangerous"),
        "interactions": {
            "dangerous": dangerous,
            "moderate": moderate,
            "mild": mild,
            "total_found": len([i for i in all_interactions if i.get("interaction_exists")])
        },
        "pairs_checked": final_state.get("checked_pairs"),
        "steps_taken": final_state.get("messages"),
    }