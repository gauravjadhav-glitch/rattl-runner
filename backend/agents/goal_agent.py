from services.llm_service import ask_llm_json
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
import json

class GoalAgent:
    def __init__(self):
        self.system_prompt = """
You are a Goal-Oriented Mobile Testing Agent. 
Your job is to decompose a high-level user goal into a sequence of Maestro-style automation steps.

Rules:
0. CRITICAL: Do NOT set "is_goal_reached": true unless you explicitly SEE the final outcome (e.g. 'Logged In', 'Order Placed'). If actions are still needed (like clicking Continue), set false.
1. Use ONLY information provided in the screen hierarchy.
2. If the target is NOT on the current screen, identify the most likely navigational element to get closer.
3. Think step-by-step: First ANALYZE the screen state. Then PLAN the entire remaining flow if possible.
4. Produce the FULL sequence (up to 15 steps) to reach the goal in one go if confidence is high.
5. If the goal is reached, include a final 'assertVisible' step.
6. HANDLE DIALOGS: If a permission dialog or popup is visible (e.g., 'Allow', 'Continue', 'Close'), prioritize interacting with it before other navigation.
7. APP STATE: If the app is already open (based on screen content), DO NOT try to launch it again or tap the Home screen icon.
8. INPUTS: ALWAYS generate a 'tapOn' step for an input field BEFORE the 'inputText' step to ensure focus.

Input provided:
- Goal: {goal}
- Current Screen Hierarchy (CANDIDATES ONLY): {candidates}
- Previous Actions: {history}

Return a structured JSON report:
{{
    "plan": [
        {{"tapOn": "Continue"}},
        {{"inputText": "Pepperoni", "id": "search_box"}}
    ],
    "explanation": "Briefly explain why this step was chosen.",
    "is_goal_reached": true/false
}}
"""

    def plan_steps(self, goal: str, hierarchy_data: Dict, history: List = None) -> Dict:
        # Load user-defined rules dynamically
        custom_rules = ""
        try:
            import yaml
            import os
            rules_path = os.path.join(os.path.dirname(__file__), "..", "agent_rules.yaml")
            if os.path.exists(rules_path):
                with open(rules_path, "r") as f:
                    data = yaml.safe_load(f)
                    if data and "rules" in data:
                        custom_rules = "\nAPP-SPECIFIC TRAINING MEMORY:\n" + "\n".join([f"- {r}" for r in data["rules"]])
        except Exception:
            pass

        # Extract candidates for the LLM to keep context window small
        candidates = self._extract_candidates(hierarchy_data)
        
        user_content = f"Goal: {goal}\n{custom_rules}\nCandidates: {json.dumps(candidates)}\nHistory: {json.dumps(history or [])}"
        
        try:
            result = ask_llm_json(self.system_prompt.format(goal=goal, candidates=json.dumps(candidates), history=json.dumps(history or [])), user_content)
            if not result:
                return {
                    "plan": [],
                    "explanation": "Agent failed to think. (LLM returned None)",
                    "is_goal_reached": False
                }
            return result
        except Exception as e:
            print(f"[GoalAgent] Planning failed: {e}")
            return {
                "plan": [],
                "explanation": f"Failed to plan goal: {str(e)}",
                "is_goal_reached": False
            }

    def _extract_candidates(self, node: Dict) -> List[Dict]:
        candidates = []
        def traverse(n):
            attrs = n.get("attributes", {})
            text = attrs.get("text")
            res_id = attrs.get("resource-id")
            desc = attrs.get("content-desc")
            if text or res_id or desc:
                # Keep elements that have at least one identifying attribute
                candidates.append({
                        "text": text,
                        "id": res_id,
                        "desc": desc,
                        "class": attrs.get("class"),
                        "bounds": attrs.get("bounds")
                    })
            for child in n.get("children", []):
                traverse(child)
        traverse(node)
        return candidates[:60] # Slightly higher limit for better context

goal_agent = GoalAgent()
