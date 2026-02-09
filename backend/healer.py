import difflib
from typing import Dict, List, Optional, Any
from intelligence import intelligence

class AIHealer:
    def __init__(self):
        self.rules = {
            "TEXT_CHANGED": self._check_text_drift,
            "ELEMENT_MOVED": self._check_position_drift,
            "ELEMENT_MISSING": self._check_missing,
            "APP_CRASH": self._check_app_health
        }

    def analyze_failure(self, run_id: str, action_data: Dict, error_msg: str, screen_snapshot: Dict) -> Dict:
        """
        Main entry point for diagnosing a test failure.
        """
        intent = action_data.get("intent", "Unknown Action")
        action_type = action_data.get("type", "unknown")
        reason = "UNKNOWN"
        healed = False
        notes = f"Failure: {error_msg}"
        suggested_fix = None

        # 1. Get Memory Context
        ui_hash = screen_snapshot.get("ui_hash", "")
        # Extract query from intent or action_data (assuming simple string for now)
        query = action_data.get("query") or str(action_data.get("intent"))
        
        expected_element = intelligence.get_element_memory(ui_hash, query)

        # 2. Check for App Crash (Simple check)
        if "crash" in error_msg.lower() or "exception" in error_msg.lower() and "adb" not in error_msg.lower():
            reason = "APP_CRASH"
            notes = "The application appears to have crashed or encountered a hard exception."
            
        # 3. Check for UI Drift
        elif "not found" in error_msg.lower() or "timeout" in error_msg.lower():
            # Attempt to find a similar element in the current hierarchy
            current_hierarchy = screen_snapshot.get("hierarchy", {})
            healing_result = self._attempt_healing(expected_element, current_hierarchy)
            
            if healing_result:
                reason = healing_result["reason"]
                healed = True
                notes = healing_result["notes"]
                suggested_fix = healing_result["suggested_fix"]
                intelligence.increment_healed()
            else:
                reason = "ELEMENT_MISSING"

        # Record in memory
        intelligence.record_failure(
            run_id=run_id,
            action_id=action_data.get("action_id", "unknown"),
            reason=reason,
            healed=healed,
            notes=notes
        )

        return {
            "reason": reason, 
            "healed": healed, 
            "notes": notes, 
            "suggested_fix": suggested_fix
        }

    def _attempt_healing(self, expected: Optional[Dict], current_hierarchy: Dict) -> Optional[Dict]:
        """Rules-based healing logic comparing memory vs current UI."""
        if not expected: return None
        
        all_elements = []  # Flatten current hierarchy for comparison
        self._flatten_hierarchy(current_hierarchy, all_elements)

        # Rule 1: TEXT_CHANGED (Fuzzy Match)
        best_match = None
        highest_ratio = 0.0
        
        for el in all_elements:
            attrs = el.get("attributes", {})
            text = attrs.get("text", "")
            if not text: continue
            
            ratio = difflib.SequenceMatcher(None, expected["text"], text).ratio()
            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match = el

        if highest_ratio > 0.8:
            new_text = best_match["attributes"]["text"]
            return {
                "reason": "TEXT_CHANGED",
                "notes": f"Label drift detected: '{expected['text']}' -> '{new_text}' (Ratio: {highest_ratio:.2f})",
                "suggested_fix": {"type": "text", "value": new_text}
            }

        # Rule 2: ELEMENT_MOVED (Same Resource ID)
        if expected.get("resource_id"):
            for el in all_elements:
                if el.get("attributes", {}).get("resource-id") == expected["resource_id"]:
                    return {
                        "reason": "ELEMENT_MOVED",
                        "notes": "Element found via Resource ID but text or position may have changed.",
                        "suggested_fix": {"type": "resource_id", "value": expected["resource_id"]}
                    }

        return None

    def _flatten_hierarchy(self, node: Dict, acc: List):
        if not node: return
        acc.append(node)
        for child in node.get("children", []):
            self._flatten_hierarchy(child, acc)

    def _check_app_health(self) -> bool: return False
    def _check_text_drift(self): pass
    def _check_position_drift(self): pass
    def _check_missing(self): pass

healer = AIHealer()
