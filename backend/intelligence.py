import json
import os
import hashlib
import time
from typing import Dict, List, Optional, Any, Literal
from models import TestRun, ScreenMemory, ElementMemory, ActionHistory, FailureRecord, ConfidenceMetric
from datetime import datetime

class TestMemory:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.raw_data = {
            "screens": {},
            "globals": {},
            "healed_count": 0,
            "runs": [],
            "elements": {}, # screen_id -> {element_id -> ElementMemory}
            "step_memory": {}, # formatted_test_name|step_index -> {bounds, element_id}
            "actions": [],
            "failures": []
        }
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    # Merge existing data into default structure
                    for k in data:
                        self.raw_data[k] = data[k]
            except Exception as e:
                print(f"[DEBUG] Error loading memory: {e}")

    def save(self):
        with open(self.storage_path, "w") as f:
            # We convert Pydantic models to dict if they were stored as such
            # But here raw_data is mostly dicts for simplicity in internal storage
            json.dump(self.raw_data, f, indent=2, default=str)

    def start_run(self, test_name: str, mode: Literal["LEARN", "FAST"]) -> str:
        run_id = hashlib.md5(f"{test_name}|{time.time()}".encode()).hexdigest()[:8]
        new_run = TestRun(
            run_id=run_id,
            test_name=test_name,
            mode=mode,
            started_at=datetime.now()
        )
        run_dict = new_run.dict()
        run_dict["started_at"] = run_dict["started_at"].isoformat()
        self.raw_data["runs"].append(run_dict)
        self.save()
        return run_id

    def end_run(self, run_id: str, status: Literal["PASS", "FAIL"], execution_time_ms: int):
        for run in self.raw_data["runs"]:
            if run["run_id"] == run_id:
                run["status"] = status
                run["completed_at"] = datetime.now().isoformat()
                run["execution_time_ms"] = execution_time_ms
                # Simple confidence calculation for now
                run["confidence_score"] = self.calculate_confidence(run_id)
                break
        self.save()

    def learn_screen(self, screen_hash: str, screenshot_path: str, run_id: str, hierarchy: Dict):
        if screen_hash not in self.raw_data["screens"]:
            self.raw_data["screens"][screen_hash] = {
                "screen_id": screen_hash,
                "first_seen": time.time(),
                "visit_count": 0,
                "screenshot_path": screenshot_path,
                "ui_hash": screen_hash,
                "last_seen_run": run_id
            }
        
        self.raw_data["screens"][screen_hash]["visit_count"] += 1
        self.raw_data["screens"][screen_hash]["last_seen"] = time.time()
        self.raw_data["screens"][screen_hash]["last_seen_run"] = run_id
        
        # Learn all persistent elements from this hierarchy
        self._learn_elements(screen_hash, hierarchy, run_id)
        self.save()

    def _learn_elements(self, screen_id: str, node: Dict, run_id: str):
        """Recursively learn elements from a hierarchy."""
        if not node: return

        attrs = node.get("attributes", {})
        text = attrs.get("text")
        rid = attrs.get("resource-id")
        
        if text or rid:
            # Create a stable element ID
            el_id = hashlib.md5(f"{screen_id}|{text}|{rid}|{attrs.get('class')}".encode()).hexdigest()[:8]
            
            # Initialize or update element memory
            if screen_id not in self.raw_data["elements"]:
                self.raw_data["elements"][screen_id] = {}
                
            if el_id not in self.raw_data["elements"][screen_id]:
                self.raw_data["elements"][screen_id][el_id] = {
                    "element_id": el_id,
                    "screen_id": screen_id,
                    "text": text,
                    "resource_id": rid,
                    "content_desc": attrs.get("content-desc"),
                    "bounds": attrs.get("bounds"),
                    "success_rate": 1.0,
                    "success_count": 0,
                    "fail_count": 0,
                    "preferred_locator": "resource_id" if rid else "text"
                }
            
        for child in node.get("children", []):
            self._learn_elements(screen_id, child, run_id)

    def record_action(self, run_id: str, action_type: str, intent: str, status: str, duration_ms: int, element_id: str = None):
        action_id = hashlib.md5(f"{run_id}|{intent}|{time.time()}".encode()).hexdigest()[:8]
        action = ActionHistory(
            action_id=action_id,
            run_id=run_id,
            action_type=action_type,
            intent=intent,
            element_id=element_id,
            status=status,
            execution_time_ms=duration_ms
        )
        self.raw_data["actions"].append(action.dict())
        self.save()
        return action_id

    def record_failure(self, run_id: str, action_id: str, reason: str, healed: bool = False, notes: str = ""):
        failure_id = hashlib.md5(f"{run_id}|{action_id}|{time.time()}".encode()).hexdigest()[:8]
        failure = FailureRecord(
            failure_id=failure_id,
            run_id=run_id,
            action_id=action_id,
            reason=reason,
            healed=healed,
            auto_fix_applied=healed,
            notes=notes
        )
        self.raw_data["failures"].append(failure.dict())
        self.save()
    def remember_interaction(self, screen_id: str, query: str, element_node: Dict, success: bool = True):
        """Update element memory with the result of an interaction."""
        el = self.get_element_memory(screen_id, query)
        if not el:
            # If not learned during screen learn (unlikely but possible), learn it now
            attrs = element_node.get("attributes", {})
            text = attrs.get("text")
            rid = attrs.get("resource-id")
            el_id = hashlib.md5(f"{screen_id}|{text}|{rid}|{attrs.get('class')}".encode()).hexdigest()[:8]
            
            if screen_id not in self.raw_data["elements"]:
                self.raw_data["elements"][screen_id] = {}
                
            el = {
                "element_id": el_id,
                "screen_id": screen_id,
                "text": text,
                "resource_id": rid,
                "content_desc": attrs.get("content-desc"),
                "bounds": attrs.get("bounds"),
                "success_rate": 1.0,
                "success_count": 0,
                "fail_count": 0,
                "preferred_locator": "resource_id" if rid else "text"
            }
            self.raw_data["elements"][screen_id][el_id] = el
        
        # Update stats
        if success:
            el["success_count"] = el.get("success_count", 0) + 1
        else:
            el["fail_count"] = el.get("fail_count", 0) + 1
        
        total = el["success_count"] + el["fail_count"]
        el["success_rate"] = el["success_count"] / total if total > 0 else 1.0
        
        self.save()

    def increment_healed(self):
        self.raw_data["healed_count"] = self.raw_data.get("healed_count", 0) + 1
        self.save()
    
    def delete_run(self, run_id: str) -> bool:
        """Delete a test run and all associated data"""
        # Remove run
        self.raw_data["runs"] = [r for r in self.raw_data["runs"] if r["run_id"] != run_id]
        # Remove associated actions
        self.raw_data["actions"] = [a for a in self.raw_data["actions"] if a["run_id"] != run_id]
        # Remove associated failures
        self.raw_data["failures"] = [f for f in self.raw_data["failures"] if f["run_id"] != run_id]
        self.save()
        return True

    def calculate_confidence(self, run_id: str) -> float:
        """
        Calculates confidence based on multiple metrics:
        1. UI Stability (How many screens are known vs new)
        2. Locator Reliability (Success rate of elements used)
        3. Execution Consistency (Pass rate of actions)
        """
        run_actions = [a for a in self.raw_data["actions"] if a["run_id"] == run_id]
        if not run_actions: return 0.0
        
        # 1. Execution Consistency
        success_rate = len([a for a in run_actions if a["status"] == "SUCCESS"]) / len(run_actions)
        
        # 2. UI Stability
        known_screens = len(self.raw_data["screens"])
        total_visits = sum(s.get("visit_count", 0) for s in self.raw_data["screens"].values())
        stability = min(1.0, total_visits / 100) if total_visits > 0 else 0.5
        
        # 3. Weighted score
        final_score = (success_rate * 0.6) + (stability * 0.4)
        return round(final_score, 2)

    def get_screen_memory(self, screen_hash: str) -> Optional[Dict]:
        return self.raw_data["screens"].get(screen_hash)

    def get_element_memory(self, screen_id: str, query: str) -> Optional[Dict]:
        """Find an element in memory by text or resource_id."""
        screen_elements = self.raw_data["elements"].get(screen_id, {})
        for el_id, el in screen_elements.items():
            if el.get("text") == query or el.get("resource_id") == query:
                return el
        return None

    def save_step_memory(self, test_name: str, step_index: int, bounds: str):
        """Remember where a step successfully interacted."""
        key = f"{test_name}|{step_index}"
        self.raw_data["step_memory"][key] = {
            "bounds": bounds,
            "last_updated": time.time()
        }
        self.save()

    def get_step_memory(self, test_name: str, step_index: int) -> Optional[Dict]:
        """Recall where a step interacted previously."""
        key = f"{test_name}|{step_index}"
        return self.raw_data.get("step_memory", {}).get(key)

# Global intelligence instance
intelligence = TestMemory(os.path.join(os.path.dirname(__file__), "intelligent_memory.json"))
