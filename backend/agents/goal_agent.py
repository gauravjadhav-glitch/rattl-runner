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
1. Use ONLY information provided in the screen hierarchy.
2. If the target is NOT on the current screen, identify the most likely navigational element to get closer (e.g., 'Settings', 'Menu', 'Search').
3. Produce a sequence of max 5 steps at a time.
4. If the goal is reached, include a final 'assertVisible' step.

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
        # Extract candidates for the LLM to keep context window small
        candidates = self._extract_candidates(hierarchy_data)
        
        user_content = f"Goal: {goal}\nCandidates: {json.dumps(candidates)}\nHistory: {json.dumps(history or [])}"
        
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
