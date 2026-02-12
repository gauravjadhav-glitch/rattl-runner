from typing import Dict, Any, List
from services.llm_service import ask_llm_json

class FailureAnalyzer:
    """
    AI-powered agent that analyzes test failures to determine root cause
    and suggest potential fixes.
    """
    
    SYSTEM_PROMPT = """
You are an expert Mobile QA Automation Engineer AI.
Your task is to analyze a test failure and determine the root cause.

You will be provided with:
1. The FAILED STEP (what was attempted).
2. The ERROR MESSAGE (what went wrong).
3. The XML HIERARCHY (current screen state).
4. The HISTORY (previous steps executed).

Your goal is to classify the failure into one of these categories:
- LOCATOR_CHANGED: The element exists but attributes changed (e.g. text drift).
- ELEMENT_MISSING: The element is completely gone from the screen.
- SCREEN_MISMATCH: The app is on a completely wrong screen.
- APP_CRASH: The app has crashed (popup visible or process died).
- LOADING_ISSUE: Infinite spinner or network timeout.
- POPUP_BLOCKING: A modal/dialog is blocking the target.

And provide a suggested fix if possible.

OUTPUT FORMAT:
Return a strictly valid JSON object:
{
    "failure_type": "LOCATOR_CHANGED",
    "root_cause": "The button text changed from 'Save' to 'Submit'.",
    "confidence": 0.95,
    "suggested_fix": {
        "action": "replace_locator",
        "locator_type": "text",
        "value": "Submit"
    } 
}
If no fix is possible, set suggested_fix to null.
"""

    def analyze(self, step: Dict, error: str, xml_hierarchy: str, history: List[Dict]) -> Dict:
        """
        Analyzes a failure using the LLM.
        """
        user_content = f"""
FAILED STEP:
{step}

ERROR MESSAGE:
{error}

PREVIOUS 5 STEPS:
{history[-5:] if history else []}

CURRENT XML HIERARCHY (Snippet):
{xml_hierarchy[:10000]}
"""
        return ask_llm_json(self.SYSTEM_PROMPT, user_content)

# Singleton instance
failure_analyzer = FailureAnalyzer()
