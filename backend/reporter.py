from typing import Dict, List, Any
from intelligence import intelligence
from datetime import datetime

class AIReporter:
    def generate_run_report(self, run_id: str) -> Dict:
        """
        Generates a simple, actionable test report focused on failures.
        """
        run_data = next((r for r in intelligence.raw_data["runs"] if r["run_id"] == run_id), None)
        if not run_data:
            return {"error": "Run not found"}

        actions = [a for a in intelligence.raw_data["actions"] if a["run_id"] == run_id]
        failures = [f for f in intelligence.raw_data["failures"] if f["run_id"] == run_id]
        
        # Find failed actions
        failed_actions = [a for a in actions if a["status"] == "FAIL"]
        
        # Calculate execution time
        total_time = run_data.get("execution_time_ms", 0)
        
        # Build step-by-step execution log
        steps = []
        for i, action in enumerate(actions, 1):
            step = {
                "step_number": i,
                "action": action["intent"],
                "status": action["status"],
                "time_ms": action.get("execution_time_ms", 0)
            }
            steps.append(step)

        report = {
            "summary": {
                "test_name": run_data.get("test_name", "Test Run"),
                "status": run_data["status"],
                "run_id": run_id,
                "total_steps": len(actions),
                "passed_steps": len([a for a in actions if a["status"] == "SUCCESS"]),
                "failed_steps": len(failed_actions),
                "duration_seconds": round(total_time / 1000, 2)
            },
            "failure_details": self._get_failure_details(failed_actions, failures),
            "execution_steps": steps,
            "recommendation": self._get_recommendation(run_data, failed_actions, failures)
        }
        
        return report

    def _get_failure_details(self, failed_actions: List[Dict], failures: List[Dict]) -> List[Dict]:
        """Extract clear failure information"""
        details = []
        
        for action in failed_actions:
            failure_info = {
                "failed_step": action["intent"],
                "reason": "Unknown error"
            }
            
            # Try to find matching failure record
            matching_failure = next((f for f in failures if f["action_id"] == action["action_id"]), None)
            if matching_failure:
                # Translate technical reasons to plain language
                reason_map = {
                    "ELEMENT_MISSING": "Could not find the element on screen",
                    "TEXT_CHANGED": "Element text has changed from expected value",
                    "ELEMENT_MOVED": "Element position has changed",
                    "APP_CRASH": "Application crashed or became unresponsive",
                    "UNKNOWN": "Unexpected error occurred"
                }
                failure_info["reason"] = reason_map.get(matching_failure["reason"], matching_failure["reason"])
                failure_info["details"] = matching_failure.get("notes", "No additional details")
                failure_info["auto_fixed"] = matching_failure.get("healed", False)
            
            details.append(failure_info)
        
        return details

    def _get_recommendation(self, run_data: Dict, failed_actions: List[Dict], failures: List[Dict]) -> str:
        """Provide actionable next steps"""
        if run_data["status"] == "PASS":
            return "✅ All test steps passed successfully. No action needed."
        
        if not failed_actions:
            return "⚠️ Test failed but no specific step failure detected. Check application logs for crashes or timeouts."
        
        # Check if failures were auto-fixed
        auto_fixed = [f for f in failures if f.get("healed", False)]
        if auto_fixed:
            return f"⚠️ Test failed after {len(auto_fixed)} automatic fix attempt(s). The issue requires manual investigation. Check the failure details above."
        
        # Provide specific recommendations based on failure type
        first_failure = failures[0] if failures else None
        if first_failure:
            reason = first_failure.get("reason", "UNKNOWN")
            
            recommendations = {
                "ELEMENT_MISSING": "🔍 Recommendation: Verify the element exists on the screen. Check if the app UI has changed or if there's a timing issue (element loads slowly).",
                "TEXT_CHANGED": "🔍 Recommendation: Update your test to use the new element text, or use a more stable locator (like resource-id).",
                "ELEMENT_MOVED": "🔍 Recommendation: The UI layout has changed. Update element coordinates or use text/id-based locators instead.",
                "APP_CRASH": "🔍 Recommendation: Check application logs for crash details. This is likely a bug in the app.",
                "UNKNOWN": "🔍 Recommendation: Review the test logs and screenshots to identify the root cause."
            }
            
            return recommendations.get(reason, "🔍 Recommendation: Review failure details and test logs to diagnose the issue.")
        
        return "🔍 Recommendation: Review the execution steps to identify where the test diverged from expected behavior."

reporter = AIReporter()
