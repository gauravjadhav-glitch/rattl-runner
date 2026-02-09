from typing import List, Dict, Any
from intelligence import intelligence

class AIPlanner:
    def __init__(self):
        self.system_prompt = """
You are an AI QA planner.

Your responsibility is to decide the minimum set of actions
required to validate the given test objective.

Rules:
- Reuse previously validated flows when confidence > 90%
- Skip actions that have not changed since last successful run
- Prioritize areas with recent failures
- Prefer faster execution over full coverage
- Output an execution plan, not low-level actions

If UI changes are detected, reduce reuse and increase validation.
"""

    def generate_plan(self, test_objective: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates an execution plan based on the objective and current memory/context.
        Phase 1: Deterministic Plan (Rules Engine)
        """
        
        # Mode decision logic
        recent_runs = intelligence.raw_data.get("runs", [])
        last_run = recent_runs[-1] if recent_runs else None
        
        mode = "LEARN"
        if last_run and last_run.get("status") == "PASS" and last_run.get("confidence_score", 0) > 0.9:
            mode = "FAST"
            
        # Detect UI changes (simplified)
        ui_changed = context.get("ui_hash_changed", False)
        if ui_changed:
            mode = "PARTIAL_LEARN"

        plan = []
        
        # Simple rule-based planning
        # In later phases, this will use LLM based on self.system_prompt
        
        # Strategy: Search for relevant known flows in memory
        # (For now, we use simple intent matching)
        
        if "login" in test_objective.lower():
            plan.append({"type": "ACTION", "intent": "Launch App and Login"})
        else:
            # Common prefix flow
            plan.append({"type": "REUSE_FLOW", "name": "standard_startup"})
            
        plan.append({"type": "ACTION", "intent": test_objective})
        plan.append({"type": "ASSERT", "intent": f"Validation for: {test_objective}"})

        return {
            "mode": mode,
            "plan": plan,
            "risk_level": "MEDIUM" if ui_changed else "LOW",
            "summary": f"Planner selected {mode} mode with {len(plan)} high-level intents."
        }

planner = AIPlanner()
