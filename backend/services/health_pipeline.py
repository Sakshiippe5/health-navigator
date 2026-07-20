# services/health_pipeline.py
#
# RESPONSIBILITY: Orchestrates all 3 agents into one unified pipeline.
#
# WHY a service file not an agent file?
# This isn't a LangGraph agent itself — it's a coordinator
# that calls agents and combines their results.
# It belongs in services/ not agents/.
#
# Flow:
#   1. Run symptom checker
#   2. Run drug checker + appointment scheduler in parallel
#      (drug check doesn't need symptom results)
#      (scheduler needs symptom results → runs after step 1)
#   3. Combine everything into unified report

import asyncio
from typing import Dict, Any, List, Optional
from agents.symptom_checker import check_symptoms
from agents.drug_interaction import check_drug_interactions
from agents.appointment_scheduler import schedule_appointment
from datetime import datetime, timezone


def run_health_pipeline(
    symptoms: str,
    medications: List[str] = None,
    patient_age: int = None,
    medical_history: str = None,
) -> Dict[str, Any]:
    """
    Master function that runs all 3 agents and combines results.

    Args:
        symptoms: Patient's described symptoms
        medications: Current medications (optional)
        patient_age: Patient's age (optional)
        medical_history: Relevant medical history (optional)

    Returns:
        Complete unified health assessment
    """

    print("\n" + "="*50)
    print("🏥 HEALTH PIPELINE STARTING")
    print("="*50)

    pipeline_start = datetime.now(timezone.utc)
    results = {}
    errors = {}

    # ── Step 1: Symptom Checker (always runs first) ───────────────────────
    print("\n📍 STEP 1: Running Symptom Checker...")
    try:
        symptom_result = check_symptoms(
            symptoms=symptoms,
            patient_age=patient_age,
            medical_history=medical_history
        )
        results["symptom_assessment"] = symptom_result
        print(f"✅ Symptom check complete: {symptom_result.get('urgency_level')}")
    except Exception as e:
        errors["symptom_assessment"] = str(e)
        symptom_result = None
        print(f"❌ Symptom check failed: {e}")

    # ── Step 2a: Drug Interaction Check (runs if medications provided) ────
    if medications and len(medications) >= 2:
        print("\n📍 STEP 2a: Running Drug Interaction Check...")
        try:
            drug_result = check_drug_interactions(
                medications=medications,
                patient_age=patient_age,
            )
            results["drug_interactions"] = drug_result
            print(f"✅ Drug check complete: {drug_result.get('overall_risk')} risk")
        except Exception as e:
            errors["drug_interactions"] = str(e)
            drug_result = None
            print(f"❌ Drug check failed: {e}")
    else:
        drug_result = None
        results["drug_interactions"] = None
        print("\n📍 STEP 2a: Skipped (less than 2 medications provided)")

    # ── Step 2b: Appointment Scheduler (uses symptom checker output) ──────
    print("\n📍 STEP 2b: Running Appointment Scheduler...")
    try:
        # Use symptom checker output if available
        # Otherwise use sensible defaults
        if symptom_result:
            urgency = symptom_result.get("urgency_level", "MEDIUM")
            specialist = symptom_result.get("specialist_needed", "General Practitioner")
            conditions = symptom_result.get("possible_conditions", [])
        else:
            urgency = "MEDIUM"
            specialist = "General Practitioner"
            conditions = []

        scheduler_result = schedule_appointment(
            symptoms=symptoms,
            urgency_level=urgency,
            specialist_needed=specialist,
            possible_conditions=conditions,
            patient_age=patient_age
        )
        results["appointment_plan"] = scheduler_result
        print(f"✅ Scheduling complete: {scheduler_result.get('timeframe')}")
    except Exception as e:
        errors["appointment_plan"] = str(e)
        scheduler_result = None
        print(f"❌ Scheduling failed: {e}")

    # ── Step 3: Combine Results ───────────────────────────────────────────
    print("\n📍 STEP 3: Combining results...")

    pipeline_end = datetime.now(timezone.utc)
    duration = (pipeline_end - pipeline_start).total_seconds()

    # Determine overall urgency considering both
    # symptom urgency AND drug interaction risk
    overall_urgency = _calculate_overall_urgency(
        symptom_urgency=symptom_result.get("urgency_level") if symptom_result else None,
        drug_risk=drug_result.get("overall_risk") if drug_result else None
    )

    # Build unified report
    unified_report = {
        "pipeline_metadata": {
            "completed_at": pipeline_end.isoformat(),
            "duration_seconds": round(duration, 2),
            "agents_run": [k for k in results.keys() if results[k] is not None],
            "errors": errors if errors else None
        },
        "overall_urgency": overall_urgency,
        "patient_info": {
            "age": patient_age,
            "symptoms": symptoms,
            "medications": medications,
            "medical_history": medical_history
        },
        "symptom_assessment": results.get("symptom_assessment"),
        "drug_interactions": results.get("drug_interactions"),
        "appointment_plan": results.get("appointment_plan"),

        # Quick summary — most important info at the top
        "summary": _build_summary(
            symptom_result=symptom_result,
            drug_result=drug_result,
            scheduler_result=scheduler_result,
            overall_urgency=overall_urgency
        )
    }

    print(f"\n✅ Pipeline complete in {duration:.1f}s")
    print("="*50 + "\n")

    return unified_report


def _calculate_overall_urgency(
    symptom_urgency: str = None,
    drug_risk: str = None
) -> str:
    """
    Combines symptom urgency and drug risk into one overall urgency.

    Rule: Take the HIGHER of the two.
    A safe symptom + dangerous drugs = HIGH overall.
    """

    # Urgency ranking (higher index = more urgent)
    urgency_rank = {
        "LOW": 1, "SAFE": 1,
        "MEDIUM": 2, "MODERATE": 2,
        "HIGH": 3,
        "EMERGENCY": 4, "CRITICAL": 4
    }

    symptom_rank = urgency_rank.get(
        (symptom_urgency or "MEDIUM").upper(), 2
    )
    drug_rank = urgency_rank.get(
        (drug_risk or "LOW").upper(), 1
    )

    # Take the maximum
    max_rank = max(symptom_rank, drug_rank)

    # Map back to string
    rank_to_urgency = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "EMERGENCY"}
    return rank_to_urgency.get(max_rank, "MEDIUM")


def _build_summary(
    symptom_result: Dict = None,
    drug_result: Dict = None,
    scheduler_result: Dict = None,
    overall_urgency: str = "MEDIUM"
) -> Dict[str, Any]:
    """
    Builds a clean top-level summary from all agent results.
    This is what the frontend will display prominently.
    """

    summary = {
        "overall_urgency": overall_urgency,
        "immediate_action": None,
        "key_findings": [],
        "next_steps": []
    }

    # Key findings from symptom checker
    if symptom_result:
        if symptom_result.get("possible_conditions"):
            summary["key_findings"].append(
                f"Possible conditions: {', '.join(symptom_result['possible_conditions'])}"
            )
        if symptom_result.get("recommended_action"):
            summary["immediate_action"] = symptom_result["recommended_action"]

    # Key findings from drug checker
    if drug_result and drug_result.get("has_dangerous_interactions"):
        dangerous = drug_result.get("interactions", {}).get("dangerous", [])
        for interaction in dangerous:
            summary["key_findings"].append(
                f"⚠️ DANGEROUS: {interaction.get('drug1')} + "
                f"{interaction.get('drug2')} — {interaction.get('severity')}"
            )

    # Next steps from scheduler
    if scheduler_result:
        timeframe = scheduler_result.get("timeframe")
        specialist = scheduler_result.get("specialist_needed")
        if timeframe and specialist:
            summary["next_steps"].append(
                f"See {specialist} — {timeframe}"
            )

        scheduling_steps = scheduler_result.get("scheduling", {}).get("steps", [])
        summary["next_steps"].extend(scheduling_steps[:2])  # top 2 steps

    return summary