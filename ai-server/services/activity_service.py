"""
Formats and validates the structured output from the LLM into
a standard response shape consumed by the API routes.
"""


def format_activity_response(llm_output: dict) -> dict:
    """
    Validate and normalise LLM output into the canonical API response format.
    Missing fields receive safe defaults.
    """
    activity = llm_output.get("activity") or {}

    return {
        "issue": llm_output.get("issue") or "Learning difficulty detected",
        "topic": llm_output.get("topic") or "General",
        "age_group": llm_output.get("age_group") or "3-6",
        "activity": {
            "name": activity.get("name") or "Exploratory Play Activity",
            "materials": activity.get("materials") or [],
            "duration": activity.get("duration") or "15 minutes",
        },
    }
