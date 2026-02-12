from typing import Dict, List, Optional
import json
import time

class ImproverEngine:
    """
    AI-powered agent that reviews test execution memory to suggest test improvements.
    - Identifies FLAKY steps (success rate < 95%)
    - Identifies SLOW steps (execution time > average)
    - Suggests better selectors or shorter flows.
    """

    def analyze_memory(self, memory_file_path: str) -> List[Dict]:
        """
        Scans the intelligent memory for patterns of failure or inefficiency.
        """
        try:
            with open(memory_file_path, 'r') as f:
                memory = json.load(f)
        except Exception as e:
            return []

        suggestions = []
        
        # 1. Check for Flaky Elements
        screens = memory.get("elements", {})
        for screen_id, elements in screens.items():
            for el_id, el in elements.items():
                success_rate = el.get("success_rate", 1.0)
                if success_rate < 0.90: # If less than 90% success
                    suggestions.append({
                        "type": "FLAKY_ELEMENT",
                        "screen": screen_id,
                        "element": el.get("text") or el.get("resource_id"),
                        "metric": f"{success_rate*100:.1f}% Success Rate",
                        "suggestion": f"Replace locator '{el.get('preferred_locator')}' with a more stable one."
                    })

        # 2. Check for Slow Actions (from run history)
        runs = memory.get("runs", [])
        for run in runs[-5:]: # Look at last 5 runs
           if run.get("execution_time_ms", 0) > 60000: # 1 minute
               suggestions.append({
                   "type": "SLOW_TEST",
                   "test": run.get("test_name"),
                   "metric": f"{run.get('execution_time_ms')/1000}s",
                   "suggestion": "Test takes >1min. Consider breaking into smaller flows."
               })

        return suggestions

improver = ImproverEngine()
