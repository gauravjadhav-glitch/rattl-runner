from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Literal, Dict

class TestRun(BaseModel):
    run_id: str
    test_name: str
    mode: Literal["LEARN", "FAST"]
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: Literal["PASS", "FAIL", "RUNNING"] = "RUNNING"
    execution_time_ms: int = 0
    confidence_score: float = 0.0

class ScreenMemory(BaseModel):
    screen_id: str
    screen_name: str
    screenshot_path: str
    ui_hash: str
    last_seen_run: str
    visit_count: int = 1

class ElementMemory(BaseModel):
    element_id: str
    screen_id: str
    text: Optional[str] = None
    resource_id: Optional[str] = None
    content_desc: Optional[str] = None
    bounds: Optional[Dict] = None
    preferred_locator: Literal["text", "resource_id", "content_desc", "coordinate"] = "text"
    success_rate: float = 1.0
    success_count: int = 0
    fail_count: int = 0
    last_success_run: Optional[str] = None

class ActionHistory(BaseModel):
    action_id: str
    run_id: str
    action_type: Literal["tap", "input", "swipe", "assert", "launchApp", "nav", "pressKey", "scroll", "tapOn", "inputText", "waitForAnimationToEnd", "extendedWaitUntil", "assertVisible", "assertNotVisible", "back", "stopApp", "openLink", "eraseText", "wait"]
    intent: str
    element_id: Optional[str] = None
    status: Literal["SUCCESS", "FAIL"] = "SUCCESS"
    execution_time_ms: int = 0

class FailureRecord(BaseModel):
    failure_id: str
    run_id: str
    action_id: str
    reason: Literal[
        "TEXT_CHANGED",
        "ELEMENT_MOVED",
        "ELEMENT_MISSING",
        "APP_CRASH",
        "UNKNOWN"
    ]
    healed: bool = False
    auto_fix_applied: bool = False
    notes: str = ""

class ConfidenceMetric(BaseModel):
    run_id: str
    ui_stability: float
    locator_reliability: float
    execution_consistency: float
    final_score: float
