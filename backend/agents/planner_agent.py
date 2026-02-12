from services.llm_service import ask_llm_json
import yaml
import json
import os

class PlannerAgent:
    def __init__(self):
        self.system_prompt = """
You are an AI Test Planner for a mobile automation system. 
Your job is to analyze a test flow (YAML) and historical context to determine the best execution strategy.

Analyze the flow for:
1. Complexity (number of steps, types of actions)
2. Risk (potential for flakiness, complex UI transitions, permission dialogs)
3. Optimization (can certain steps be sped up?)

Return a structured JSON report:
{
    "risk_score": 0-100,
    "execution_mode": "FAST" | "DEEP_SCAN",
    "potential_flaky_steps": [index1, index2],
    "estimated_duration_sec": 30,
    "reasoning": "Brief explanation of the strategy."
}
"""

    def plan_execution(self, yaml_content, history=None) -> dict:
        try:
            # Handle string vs already parsed data
            if isinstance(yaml_content, str):
                if "---" in yaml_content:
                    parts = yaml_content.split("---")
                    yaml_data = yaml.safe_load(parts[1]) if len(parts) > 1 else yaml.safe_load(parts[0])
                else:
                    yaml_data = yaml.safe_load(yaml_content)
            else:
                yaml_data = yaml_content
            
            user_content = f"Test Flow:\n{yaml.dump(yaml_data)}\n\nHistorical Context:\n{json.dumps(history or {})}"
            
            result = ask_llm_json(self.system_prompt, user_content)
            return result
        except Exception as e:
            print(f"[PlannerAgent] Planning failed: {e}")
            return {
                "risk_score": 50,
                "execution_mode": "DEEP_SCAN",
                "potential_flaky_steps": [],
                "estimated_duration_sec": 60,
                "reasoning": f"Planning failed due to error: {str(e)}. Defaulting to safe mode."
            }

planner_agent = PlannerAgent()
