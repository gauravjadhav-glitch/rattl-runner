from intelligence import intelligence
from models import TestRun, ScreenMemory, ElementMemory, ActionHistory, FailureRecord, ConfidenceMetric
from healer import healer
import subprocess
import time
import hashlib
import os
import json
import base64
import requests
import re
import xml.etree.ElementTree as ET
import yaml
from typing import List, Dict, Optional, Any
from agents.failure_analyzer import failure_analyzer
from agents.hybrid_resolver import hybrid_resolver
from agents.planner_agent import planner_agent
from agents.goal_agent import goal_agent
from analysis.crash_analyzer import crash_analyzer
from analysis.improver import improver

# Global variables for current run tracking
current_run_id = None

_hierarchy_cache = {"data": None, "time": 0, "hash": None}
_last_interaction_time = 0
_native_dump_failures = 0

def mark_interaction():
    global _last_interaction_time
    _last_interaction_time = time.time()

def call_google_vision(screenshot_path, query, api_key):
    """Google Gemini Vision Implementation"""
    try:
        print(f"[DEBUG] Asking Google Gemini to find '{query}'...")
        with open(screenshot_path, "rb") as img_file:
            b64_image = base64.b64encode(img_file.read()).decode("utf-8")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        prompt = (
            f"You are a UI automation agent. Locate the center coordinates (x, y) of the UI element labeled '{query}'. "
            "Output STRICT JSON: {\"found\": true, \"x\": 123, \"y\": 456}. If not found: {\"found\": false}."
        )
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": b64_image}}
                ]
            }]
        }
        
        resp = requests.post(url, headers=headers, json=payload)
        data = resp.json()
        
        if "error" in data:
            print(f"[DEBUG] Google Vision Error: {data['error']}")
            return None
            
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            if result.get("found"):
                return (result["x"], result["y"])
    except Exception as e:
        print(f"[DEBUG] Google Vision Exception: {e}")
    return None

def call_ai_vision(screenshot_path, query, api_key):
    """Fallback: Use AI to find element coordinates by vision (OpenAI or Google)"""
    
    # 1. Determine Provider
    use_google = False
    active_key = api_key
    
    if not active_key:
        if os.getenv("GOOGLE_API_KEY"):
            active_key = os.getenv("GOOGLE_API_KEY")
            use_google = True
        elif os.getenv("OPENAI_API_KEY"):
            active_key = os.getenv("OPENAI_API_KEY")
    
    # Detect based on key format
    if active_key and active_key.startswith("AIza"):
        use_google = True
        
    if not active_key:
        print("[DEBUG] AI Vision skipped (No API Key found)")
        return None

    # 2. Call Provider
    if use_google:
        return call_google_vision(screenshot_path, query, active_key)

    # 3. OpenAI Implementation (Legacy)
    try:
        print(f"[DEBUG] Asking OpenAI to find '{query}'...")
        with open(screenshot_path, "rb") as img_file:
            b64_image = base64.b64encode(img_file.read()).decode("utf-8")
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {active_key}"
        }
        
        prompt = (
            f"You are a UI automation agent. The user wants to click on the element labeled '{query}'. "
            "Analyze the screenshot. Locate the visual element (text, icon, or button) that matches match. "
            "Return the center coordinates (x, y) of the element. "
            "Output MUST be strict JSON only: {\"found\": true, \"x\": 100, \"y\": 200}. "
            "If not found, {\"found\": false}."
        )
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
                    ]
                }
            ],
            "max_tokens": 100
        }
        
        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        data = resp.json()
        
        if "error" in data:
            print(f"[DEBUG] OpenAI Vision Error: {data['error']}")
            return None
            
        content = data["choices"][0]["message"]["content"]
        # Extract JSON
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            if result.get("found"):
                return (result["x"], result["y"])
    except Exception as e:
        print(f"[DEBUG] OpenAI Vision Exception: {e}")
        
    return None

def run_adb(command):
    cmd = ["adb"] + command.split()
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def tap_point(x, y):
    mark_interaction()
    run_adb(f"shell input tap {x} {y}")

def get_screen_size():
    res = run_adb("shell wm size").stdout
    # Prioritize Override size (user custom resolution)
    match = re.search(r"Override size:\s*(\d+)x(\d+)", res)
    if match:
        return int(match.group(1)), int(match.group(2))
    
    # Fallback to Physical size
    match = re.search(r"Physical size:\s*(\d+)x(\d+)", res)
    if match:
        return int(match.group(1)), int(match.group(2))
        
    # Last resort fallback
    match = re.search(r"(\d+)x(\d+)", res)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 1080, 2400

def tap_point_percent(px_str, py_str):
    w, h = get_screen_size()
    
    # Handle X
    if "%" in str(px_str):
        x_val = float(str(px_str).replace("%", "")) / 100.0 * w
    else:
        x_val = float(px_str)
        
    # Handle Y
    if "%" in str(py_str):
        y_val = float(str(py_str).replace("%", "")) / 100.0 * h
    else:
        y_val = float(py_str)
        
    tap_point(int(x_val), int(y_val))

def parse_bounds(bounds_str):
    # "[0,0][1080,210]"
    try:
        match = re.search(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            return {
                "left": x1,
                "top": y1,
                "right": x2,
                "bottom": y2,
                "width": x2 - x1,
                "height": y2 - y1
            }
    except:
        pass
    return None

def parse_xml_node(node):
    attrs = node.attrib
    
    # Flatten attributes for Maestro-compatible format
    res = {
        "text": attrs.get("text", ""),
        "resourceId": attrs.get("resource-id", ""),
        "className": attrs.get("class", ""),
        "packageName": attrs.get("package", ""),
        "contentDescription": attrs.get("content-desc", ""),
        "checkable": attrs.get("checkable", "") == "true",
        "checked": attrs.get("checked", "") == "true",
        "clickable": attrs.get("clickable", "") == "true",
        "enabled": attrs.get("enabled", "") == "true",
        "focusable": attrs.get("focusable", "") == "true",
        "focused": attrs.get("focused", "") == "true",
        "scrollable": attrs.get("scrollable", "") == "true",
        "long-clickable": attrs.get("long-clickable", "") == "true",
        "password": attrs.get("password", "") == "true",
        "selected": attrs.get("selected", "") == "true",
        "bounds": parse_bounds(attrs.get("bounds", "")),
        "attributes": dict(attrs)
    }
    
    res["children"] = [parse_xml_node(child) for child in node]
    return res

def get_screen_hash(hierarchy_data):
    """Creates a fingerprint of the current screen structure."""
    if not hierarchy_data: return None
    structure = []
    
    if isinstance(hierarchy_data, dict):
        def traverse_dict(n):
            attrs = n.get("attributes", {})
            structure.append(f"{attrs.get('class')}:{attrs.get('text')}:{attrs.get('resource-id')}")
            for c in n.get("children", []): traverse_dict(c)
        traverse_dict(hierarchy_data)
    
    full_str = "|".join(structure)
    return hashlib.md5(full_str.encode()).hexdigest()

def get_hierarchy(force_refresh=False, smart_cache=False):
    global _hierarchy_cache, _native_dump_failures
    now = time.time()
    
    # Smart Cache: If enabled, utilize cache as long as it's newer than the last interaction
    # This allows bulk assertions to run instantly without re-dumping
    if smart_cache and _hierarchy_cache["data"]:
        # Check if cache was captured AFTER the last interaction
        if _hierarchy_cache["time"] > _last_interaction_time:
            return _hierarchy_cache["data"]

    # Standard Cache: 3 seconds (unless forced), BUT must be newer than last interaction
    is_fresh = _hierarchy_cache["time"] > _last_interaction_time
    if not force_refresh and _hierarchy_cache["data"] and (now - _hierarchy_cache["time"] < 3.0) and is_fresh:
        return _hierarchy_cache["data"]

    data = None
    
    # Check circuit breaker
    if _native_dump_failures < 3:
        try:
            # 1. Native ADB dump (fast)
            # Self-healing: kill any stuck uiautomator process first
            run_adb("shell pkill -9 uiautomator")
            
            # Try native dump with timeout
            # Cleanup first
            run_adb("shell rm -f /data/local/tmp/uidump.xml")
            
            dump_proc = run_adb("shell uiautomator dump /data/local/tmp/uidump.xml")
            
            # If it failed, try once more after a tiny sleep
            if dump_proc.returncode != 0:
                print(f"[DEBUG] Native dump failed (code {dump_proc.returncode}, stderr: {dump_proc.stderr}), retrying...")
                time.sleep(0.5)
                # Kill uiautomator more aggressively
                run_adb("shell am force-stop com.github.uiautomator")
                run_adb("shell am force-stop com.github.uiautomator.test")
                dump_proc = run_adb("shell uiautomator dump /data/local/tmp/uidump.xml")

            if dump_proc.returncode == 0:
                xml_res = run_adb("shell cat /data/local/tmp/uidump.xml")
                xml_data = xml_res.stdout
                
                if xml_data and "<?xml" in xml_data:
                    start_xml = xml_data.find("<?xml")
                    end_xml = xml_data.rfind("</hierarchy>")
                    if start_xml != -1 and end_xml != -1:
                        clean_xml = xml_data[start_xml:end_xml + len("</hierarchy>")]
                        try:
                            root = ET.fromstring(clean_xml)
                            data = parse_xml_node(root)
                            # Success! Reset failure count
                            _native_dump_failures = 0
                        except: pass
            
            if not data:
                _native_dump_failures += 1
                if _native_dump_failures >= 3:
                     print("[DEBUG] Native dump unstable. Disabling for this session.")

        except Exception as e:
             _native_dump_failures += 1
             print(f"[ERROR] Native dump error: {e}")

    if not data:
        # 2. Fallback to maestro hierarchy
        print("[DEBUG] Native dump failed/invalid/disabled, falling back to maestro")
        result = subprocess.run(["maestro", "hierarchy"], capture_output=True, text=True, timeout=30, env={**os.environ, "MAESTRO_OUTPUT_NO_COLOR": "true"})
        output = result.stdout
        start = output.find('{')
        end = output.rfind('}')
        if start != -1 and end != -1:
            data = json.loads(output[start:end+1])

    if data:
        h = get_screen_hash(data)
        # AI Learning integration
        intelligence.learn_screen(h, None, current_run_id or "unknown", data)
        _hierarchy_cache = {"data": data, "time": now, "hash": h}
        return data
            
    return {"children": []}

def get_current_screen_hash():
    """Helper to get the hash of the last captured hierarchy."""
    if _hierarchy_cache["time"] > _last_interaction_time:
        return _hierarchy_cache.get("hash")
    return None


def get_hierarchy_json():
    data = get_hierarchy()
    return json.dumps(data)

def find_element(node, query, index=None):
    """
    Find an element in the UI hierarchy matching the query.
    
    If index is provided, returns the N-th match (0-indexed) found in the hierarchy.
    Otherwise, returns the highest-scoring match.
    """
    if not node: return None
    
    target = str(query)
    is_regex = target.startswith("regexp:")
    
    def is_visible(n):
        # Check bounds
        b = n.get("bounds")
        # If no bounds, assume it's a container (like root) and allow children search
        if not b: return True 
        if b["width"] <= 0 or b["height"] <= 0: return False
        return True
    
    # Fast path: Try to find exact clickable match first (most common case)
    # Skip fast path if index is specified, as we need to find ALL matches to correctly index them
    if not is_regex and index is None:
        q_lower = target.lower()
        
        def find_exact_clickable(n):
            """Recursively search for exact clickable match"""
            if not n:
                return None
            
            # Visibility check
            if not is_visible(n):
                return None
            
            attrs = n.get("attributes", {})
            text = str(attrs.get("text", "")).lower()
            hint = str(attrs.get("hint", "")).lower()
            
            # Check for exact match on clickable element (text or hint)
            if (text == q_lower or hint == q_lower) and attrs.get("clickable") == "true":
                elem_class = attrs.get("class", "")
                # Prefer buttons over other clickable elements
                if "Button" in elem_class:
                    return n
                # Store as potential match but keep searching for button
                if not hasattr(find_exact_clickable, 'backup'):
                    find_exact_clickable.backup = n
            
            # Search children
            for child in n.get("children", []):
                result = find_exact_clickable(child)
                if result:
                    return result
            
            return None
        
        # Try fast path
        exact_match = find_exact_clickable(node)
        if exact_match:
            return exact_match
        
        # Check if we found a backup (exact clickable but not a button)
        if hasattr(find_exact_clickable, 'backup'):
            backup = find_exact_clickable.backup
            delattr(find_exact_clickable, 'backup')
            return backup
    
    # Slow path: Collect all matches and score/index them
    def collect_matches(n, matches):
        if not n:
            return
        
        # Check visibility
        if not is_visible(n):
            return
            
        attributes = n.get("attributes", {})
        text = str(attributes.get("text", ""))
        hint = str(attributes.get("hint", ""))
        resource_id = str(attributes.get("resource-id", ""))
        content_desc = str(attributes.get("content-desc", ""))
        
        match_type = None
        
        # Regex Match
        if is_regex:
            pattern = target[7:]
            try:
                if text and re.search(pattern, text):
                    match_type = 'regex'
                elif hint and re.search(pattern, hint):
                    match_type = 'regex'
                elif resource_id and re.search(pattern, resource_id):
                    match_type = 'regex'
                elif content_desc and re.search(pattern, content_desc):
                    match_type = 'regex'
            except:
                pass
        # Standard Match
        else:
            q_lower = target.lower()
            t_lower = text.lower()
            h_lower = hint.lower()
            r_lower = resource_id.lower()
            d_lower = content_desc.lower()
            
            # Exact match
            if (q_lower == t_lower and t_lower) or \
               (q_lower == h_lower and h_lower) or \
               (q_lower == r_lower and r_lower) or \
               (q_lower == d_lower and d_lower):
                match_type = 'exact'
            # Substring match
            elif (q_lower in t_lower and t_lower) or \
                 (q_lower in h_lower and h_lower) or \
                 (q_lower in r_lower and r_lower) or \
                 (q_lower in d_lower and d_lower):
                match_type = 'substring'
        
        if match_type:
            # Calculate score
            score = 0
            if match_type == 'exact':
                score += 1000
            elif match_type == 'regex':
                score += 500
            
            if attributes.get("clickable") == "true":
                score += 100
            
            elem_class = attributes.get("class", "")
            if "Button" in elem_class:
                score += 50
            elif "EditText" in elem_class or "Input" in elem_class:
                score += 40
            elif "ImageButton" in elem_class or "ImageView" in elem_class:
                score += 30
            
            matches.append({
                "node": n,
                "score": score,
                "text": text[:50],  # Truncate for logging
                "class": elem_class
            })
        
        # Recursively search children
        for child in n.get("children", []):
            collect_matches(child, matches)
    
    # Collect all matches
    all_matches = []
    collect_matches(node, all_matches)
    
    if not all_matches:
        return None

    # Handle indexing (index-th match in hierarchy order)
    if index is not None:
        try:
            # Maestro index can be string or int. 
            idx = int(index)
            if 0 <= idx < len(all_matches):
                return all_matches[idx]["node"]
            else:
                return None # Out of bounds
        except (ValueError, TypeError):
            pass # Fallback to scoring if index invalid

    # Sort by score (highest first) and return best match
    all_matches.sort(key=lambda x: x["score"], reverse=True)
    best = all_matches[0]
    
    # Only log if there were multiple matches (helps debug ambiguous cases)
    if len(all_matches) > 1:
        print(f"[DEBUG] Found '{target}': matched '{best['text']}' (score={best['score']}, {len(all_matches)} total matches)")
    
    return best["node"]

def find_fuzzy_successor(root, query, cached_data):
    """
    HEALING LOGIC: If a query fails but we have cached coordinates,
    look for the most similar element at or near those coordinates.
    """
    if not cached_data: return None
    
    target_bounds = cached_data.get("bounds")
    if not target_bounds: return None
    
    cx = (target_bounds["left"] + target_bounds["right"]) // 2
    cy = (target_bounds["top"] + target_bounds["bottom"]) // 2
    
    best_candidate = None
    min_dist = 200 # Max 200px drift allowed for auto-healing
    
    def search(n):
        nonlocal best_candidate, min_dist
        if not n: return
        
        attrs = n.get("attributes", {})
        bounds = attrs.get("bounds")
        
        if bounds:
            ncx = (bounds["left"] + bounds["right"]) // 2
            ncy = (bounds["top"] + bounds["bottom"]) // 2
            dist = ((cx - ncx)**2 + (cy - ncy)**2)**0.5
            
            if dist < min_dist:
                # Check for semantic similarity
                score = 0
                if attrs.get("class") == cached_data.get("class"): score += 1
                if attrs.get("clickable") == "true": score += 1
                
                # If it's close and looks like a button/input, it's a candidate
                if score >= 1:
                    min_dist = dist
                    best_candidate = n
        
        for child in n.get("children", []):
            search(child)
            
    search(root)
    return best_candidate

def analyze_failure(root, query, screen_hash):
    """
    REASONING ENGINE: Why did it fail? 
    Compares current state vs knowledge base.
    """
    cached = intelligence.get_element_memory(screen_hash, query)
    if not cached:
         return "Element never seen before on this screen. Is the locator correct?"
    
    # Check if a similar element exists elsewhere
    other_match = find_element(root, query)
    if other_match:
        return f"Element '{query}' moved! It used to be at {cached['bounds']}, but now it's at {other_match['attributes']['bounds']}."

    return f"Element '{query}' has disappeared from screen '{screen_hash}'. The UI structure may have changed significantly."

def get_center(bounds):
    """
    Calculate center of bounds. Handles both:
    1. String: "[0,0][1080,210]"
    2. Dict: {'left': 0, 'top': 0, 'right': 1080, 'bottom': 210, 'width': 1080, 'height': 210}
    """
    if not bounds: return None
    
    if isinstance(bounds, dict):
        x1, y1 = bounds.get("left", 0), bounds.get("top", 0)
        x2, y2 = bounds.get("right", 0), bounds.get("bottom", 0)
        return (x1 + x2) // 2, (y1 + y2) // 2

    # String format
    try:
        match = re.search(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", str(bounds))
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            return (x1 + x2) // 2, (y1 + y2) // 2
    except:
        pass
    return None

def perform_tap_id_only(resource_id):
    """
    Perform a tap on an element identified by its resource-id.
    This helper is used for fast-path permission dialog handling.
    """
    print(f"[DEBUG] Attempting tap on ID: {resource_id}")
    root = get_hierarchy()
    el = find_element(root, resource_id)
    if el:
        attrs = el.get("attributes", {})
        bounds = attrs.get("bounds", "")
        # Get center returns tuple (cx, cy) or None
        center = get_center(bounds)
        if center:
            cx, cy = center
            run_adb(f"shell input tap {cx} {cy}")
            return True
        else:
            print(f"[DEBUG] ID '{resource_id}' found but no valid bounds: {bounds}")
    else:
        print(f"[DEBUG] ID '{resource_id}' not found in current hierarchy")
    return False

def perform_tap_text_only(text, root=None):
    """
    Perform a tap on an element identified by its text.
    """
    print(f"[DEBUG] Attempting tap on Text: {text}")
    if not root:
        root = get_hierarchy()
    el = find_element(root, text)
    if el:
        attrs = el.get("attributes", {})
        bounds = attrs.get("bounds", "")
        center = get_center(bounds)
        if center:
            cx, cy = center
            run_adb(f"shell input tap {cx} {cy}")
            return True
    return False

def input_text(text):
    mark_interaction()
    # Ensure it is a string if it came from a dict parameter
    if isinstance(text, dict):
        # Extract text if parameter was a dict like {text: "...", index: ...}
        text = text.get("text", str(text))
    else:
        text = str(text)
        
    # Escape spaces for ADB input
    escaped = text.replace(" ", "%s")
    run_adb(f"shell input text {escaped}")

def take_screenshot(name="failure"):
    path = f"/data/local/tmp/{name}.png"
    run_adb(f"shell screencap -p {path}")
    # Pull to local workspace for viewing? For now just capturing implies debugging intent
    # Real implementation would pull this to frontend
    return path

class StepData:
    def __init__(self, step):
        self.raw = step
        if isinstance(step, str):
            self.type = step
            self.params = None
        else:
            self.type = list(step.keys())[0]
            self.params = step[self.type]

def resolve_query(params):
    if params is None: return None
    if isinstance(params, str): return params
    if not isinstance(params, dict): return str(params)
    if "point" in params: return None
    
    # Prioritize common Maestro-style keys
    for key in ["id", "resourceId", "text", "contentDescription", "accessibilityId", "label", "hint"]:
        if key in params:
            val = str(params[key])
            # Auto-detect regex for IDs/resourceIds if they contain regex special chars
            if key in ["id", "resourceId"] and not val.startswith("regexp:"):
                if any(c in val for c in [".*", "+", "^", "$", "|"]):
                    return f"regexp:{val}"
            return val
            
    # Fallback to any value that isn't a known metadata key
    clean = {k:v for k,v in params.items() if k not in ["timeout", "optional", "index", "point", "longPress"]}
    if clean: return str(next(iter(clean.values())))
    return None

def retry_operation(operation_func, max_retries=3, retry_delay=1.0, operation_name="operation"):
    """
    Retry an operation up to max_retries times with a delay between attempts.
    
    Args:
        operation_func: Function to execute (should raise exception on failure)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Delay in seconds between retries (default: 1.0)
        operation_name: Name of the operation for logging
    
    Returns:
        Result of the operation_func if successful
    
    Raises:
        Exception: If all retries fail, raises the last exception
    """
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[DEBUG] {operation_name} - Attempt {attempt}/{max_retries}")
            result = operation_func()
            if attempt > 1:
                print(f"[DEBUG] {operation_name} succeeded on attempt {attempt}")
            return result
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                print(f"[DEBUG] {operation_name} failed (attempt {attempt}/{max_retries}): {str(e)}")
                print(f"[DEBUG] Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
            else:
                print(f"[DEBUG] {operation_name} failed after {max_retries} attempts")
    
    # All retries exhausted
    raise last_exception

def wait_for_element_or_fail(query, timeout=10, step_context=None, index=None):
    # Requirement: Wait up to 10s. If not found, retry for another 10s.
    # We enforce a minimum of 10s per attempt unless a specific long timeout was requested.
    phase_timeout = max(timeout, 10)
    
    # 1. Try to recall from knowledge first (Instant check)
    # Skip recall if index is used (recall currently optimized for "best" match)
    if index is None:
        last_hash = get_current_screen_hash()
        cached = intelligence.get_element_memory(last_hash, query)
        if cached:
            print(f"[DEBUG] Learner: Recalled '{query}' from previous run knowledge.")
            if step_context:
                 intelligence.save_step_memory(step_context[0], step_context[1], cached["bounds"])
            return {"bounds": cached["bounds"], "attributes": {"bounds": cached["bounds"], "recalled": True}}

    # Two attempts: Initial (10s) + Retry (10s)
    for attempt in range(1, 3):
        start = time.time()
        msg = f"{query}[{index}]" if index is not None else query
        print(f"[DEBUG] Waiting for element: {msg} (Attempt {attempt}/2, timeout {phase_timeout}s)")
        
        first_check = True

        while time.time() - start < phase_timeout:
            # OPTIMIZATION: On first check, try smart cache (fastest)
            # If that fails, force a refresh immediately (to avoid waiting 3s for cache expiry)
            is_smart = first_check and attempt == 1
            root = get_hierarchy(smart_cache=is_smart, force_refresh=(not is_smart and first_check))
            
            if not root:
                 print("[DEBUG] Hierarchy is None")
                 time.sleep(0.3)
                 continue
                 
            # Detect screen hash
            current_hash = get_current_screen_hash()
            
            # Check cache again if screen changed (and no index)
            if index is None:
                cached = intelligence.get_element_memory(current_hash, query)
                if cached:
                    print(f"[DEBUG] Learner: Identified screen '{current_hash}'. Recalling '{query}'.")
                    if step_context:
                         intelligence.save_step_memory(step_context[0], step_context[1], cached["bounds"])
                    return {"bounds": cached["bounds"], "attributes": {"bounds": cached["bounds"], "recalled": True}}

            el = find_element(root, query, index=index)
            if el:
                # Visibility check: Ensure bounds are valid and interactive
                bounds = el.get("bounds") # Use the parsed bounds object, not the raw string
                # Basic visibility check
                if bounds and bounds.get("width", 0) > 0 and bounds.get("height", 0) > 0:
                     print(f"[DEBUG] Found '{msg}' in {time.time() - start:.2f}s")
                     if index is None: # Only remember interactions for unique/best elements
                         intelligence.remember_interaction(current_hash, query, el, success=True)
                     if step_context:
                          intelligence.save_step_memory(step_context[0], step_context[1], bounds)
                     return el
                else:
                     print(f"[DEBUG] Found '{msg}' but it is not visible/interactive. Continuing search...")
            
            # If we failed the smart check, don't sleep - loop immediately to force refresh
            if is_smart and first_check:
                first_check = False
                continue

            first_check = False
            
            # SELF-HEALING: Try fuzzy matching (only if no index)
            if index is None:
                cached = intelligence.get_element_memory(current_hash, query)
                if cached:
                    healed_el = find_fuzzy_successor(root, query, cached)
                    if healed_el:
                        print(f"[DEBUG] 🛠 SELF-HEALED: Exact match for '{query}' failed, but found a similar element.")
                        intelligence.increment_healed()
                        intelligence.remember_interaction(current_hash, query, healed_el, success=True)
                        if step_context:
                             intelligence.save_step_memory(step_context[0], step_context[1], healed_el["attributes"]["bounds"])
                        return healed_el
                
                # 3. HYBRID RESOLVER (Semantic AI Matching)
                # Trigger this earlier if we've done at least one full hierarchy scan
                if (attempt == 1 and time.time() - start > 5.0) or (attempt == 2):
                    openai_key = os.getenv("RATT_OPENAI_KEY") or os.getenv("OPENAI_API_KEY")
                    if openai_key:
                        semantic_el = hybrid_resolver.resolve_with_json(query, root)
                        if semantic_el:
                            print(f"[DEBUG] 🧠 HYBRID RESOLVER: Found semantic match for '{query}'.")
                            intelligence.remember_interaction(current_hash, query, semantic_el, success=True)
                            if step_context:
                                 intelligence.save_step_memory(step_context[0], step_context[1], semantic_el["attributes"]["bounds"])
                            return semantic_el

            time.sleep(0.3)
        
        if attempt == 1:
            print(f"[DEBUG] Element '{msg}' not found in first {phase_timeout}s. RETRYING...")
            time.sleep(0.5)

    # Timeout -> Fail
    current_hash = get_current_screen_hash()
    reason = analyze_failure(get_hierarchy(), query, current_hash)
    if index is None:
        intelligence.remember_interaction(current_hash, query, {}, success=False)
    print(f"[DEBUG] FAIL: {reason}")
    take_screenshot("failure_timeout")
    raise Exception(f"Element not found: {query} (index: {index}) after {phase_timeout*2}s. Analysis: {reason}")

def run_test_step(step, run_id=None, step_index=None, history=None):
    """Wrapper for intelligence and failure handling around step execution."""
    start_time = time.time()
    s = StepData(step)
    intent = str(step)
    action_type = s.type
    
    if history is None:
        history = []

    # Determine Intelligence Mode
    mode = "LEARN"
    test_name = None
    if run_id:
        for r in intelligence.raw_data["runs"]:
             if r["run_id"] == run_id: 
                 mode = r.get("mode", "LEARN")
                 test_name = r.get("test_name")
                 break
    
    step_context = (test_name, step_index) if test_name and step_index is not None else None

    # FAST MODE: Predict and Optimize
    if mode == "FAST" and step_context and s.type == "tapOn":
        # Check if we have a memory for this step
        mem = intelligence.get_step_memory(*step_context)
        if mem:
            print(f"[FAST] Recalled step memory: {mem['bounds']}")
            cx, cy = get_center(mem['bounds'])
            if cx:
                # OPTIMIZATION: Rewrite step to use point directly!
                # This bypasses hierarchy dump and search entirely.
                if isinstance(s.params, str): # "Search"
                    s.params = {"point": f"{cx},{cy}", "original": s.params}
                elif isinstance(s.params, dict) and "point" not in s.params:
                    s.params["point"] = f"{cx},{cy}"
                print(f"[FAST] Optimized to tap point {cx},{cy}")

    
    # Track current state before action
    # OPTIMIZATION: In FAST mode, skip initial hierarchy dump unless we fail
    root = None
    current_hash = "FAST_MODE_SKIP"
    
    should_capture_state = True
    if mode == "FAST": should_capture_state = False

    if should_capture_state:
        root = get_hierarchy()
        current_hash = get_screen_hash(root)
    
    attempts = 0
    max_attempts = 2  # 1 regular + 1 retry if healed

    while attempts < max_attempts:
        try:
            result = _dispatch_step_logic(s, step_context)
            
            # Record Success
            duration = int((time.time() - start_time) * 1000)
            if run_id:
                intelligence.record_action(run_id, action_type, intent, "SUCCESS", duration)
                
            yield f"RETURN:{result}"
            return

        except Exception as e:
            attempts += 1
            duration = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            # Record Failure & Analyze
            analysis = None
            if run_id:
                intelligence.record_action(run_id, action_type, intent, "FAIL", duration)
                analysis = healer.analyze_failure(
                    run_id, 
                    {"intent": intent, "type": action_type}, 
                    error_msg, 
                    {"ui_hash": current_hash or "unknown", "hierarchy": root or {}}
                )

                # NEW: AI Deep Analysis
                yield "[AI-BOT] Deep Analysis triggered..."
                # 1. Check for Crash first (FAST)
                is_crash = crash_analyzer.is_crash(error_msg)
                
                # 2. Capture state for LLM 
                # (We already have root/current_hash, lets get history)
                # history is passed from argument
                xml_str = json.dumps(root) if root else ""
                
                # 3. Ask the Bot
                ai_analysis = failure_analyzer.analyze(
                   step=s.raw,
                   error=error_msg,
                   xml_hierarchy=xml_str,
                   history=history
                )
                
                if ai_analysis:
                   yield f"[AI-BOT] Analysis: {ai_analysis.get('failure_type')} - {ai_analysis.get('root_cause')}"
                   
                   # Merge AI diagnosis into existing analysis object for reporting
                   analysis["ai_diagnosis"] = ai_analysis
                   
                   # Check if LLM suggested a fix that Healer missed
                   if ai_analysis.get("suggested_fix") and not analysis.get("healed"):
                        bfix = ai_analysis["suggested_fix"]
                        yield f"[AI-BOT] Suggested Fix: {bfix}"
                        
                        # Apply fix to params dynamically
                        if bfix.get("action") == "replace_locator":
                             val = bfix["value"]
                             if bfix.get("locator_type") == "text":
                                  if isinstance(s.params, dict): s.params['text'] = val
                                  else: s.params = val
                             elif "id" in bfix.get("locator_type", ""):
                                  if isinstance(s.params, dict): s.params['id'] = val
                                  else: s.params = f"id:{val}"
                             
                             # Set flag to retry with new params
                             analysis["healed"] = True
                             analysis["suggested_fix"] = {"type": bfix.get("locator_type"), "value": val}
            
            # HEALING LOGIC: Can we retry?
            if attempts < max_attempts and analysis and analysis.get("healed"):
                fix = analysis.get("suggested_fix")
                if fix:
                    yield f"[HEALER] Attempting auto-fix: {fix['value']}"
                    # Update step data for retry
                    if fix['type'] == 'text':
                        if isinstance(s.params, dict): s.params['text'] = fix['value']
                        else: s.params = fix['value']
                    elif fix['type'] == 'resource_id':
                        if isinstance(s.params, dict): s.params['id'] = fix['value']
                        else: s.params = f"id:{fix['value']}"
                    
                    # Refresh hierarchy before retry to be sure
                    root = get_hierarchy()
                    current_hash = get_screen_hash(root)
                    continue

            raise e

def _dispatch_step_logic(s, step_context=None):
    """The core Maestro command dispatcher."""
    if s.type == "launchApp":
        if isinstance(s.params, str):
            app_id = s.params
            clear_state = False
        else:
            app_id = s.params.get("appId")
            clear_state = s.params.get("clearState", False)
        
        # Force stop the app first
        run_adb(f"shell am force-stop {app_id}")
        
        # Clear app data if clearState is true (optimized - no extra wait)
        if clear_state:
            print(f"[DEBUG] Clearing app data for {app_id}")
            result = run_adb(f"shell pm clear {app_id}")
            # pm clear is synchronous, no need to wait
        
        # Launch the app with optimized startup
        run_adb(f"shell monkey -p {app_id} -c android.intent.category.LAUNCHER 1")
        
        # Reduced wait time - app launches quickly
        time.sleep(1.5)
        
        return f"Launch {app_id}" + (" (cleared state)" if clear_state else "")


    elif s.type == "tapOn":
        is_optional = False
        timeout = 5 if is_optional else 10 # Reduced default timeout
        
        # Handle coordinate tap immediately (FAST PATH)
        if isinstance(s.params, dict) and "point" in s.params:
            pt = str(s.params["point"])
            if "," in pt:
                px_str, py_str = pt.split(",")
            else:
                # Handle possible YAML parsing artifact where {point: 90%, 9%} 
                # might result in 'point' being '90%' and others as keys
                px_str = pt
                py_str = None
                for k in s.params:
                    if k != "point":
                        py_str = str(k)
                        break
                if not py_str:
                     raise Exception(f"Invalid point format: {pt}")
            
            tap_point_percent(px_str, py_str)
            return f"Tap Point: {px_str},{py_str}"
            
        query = resolve_query(s.params)
        index = s.params.get("index") if isinstance(s.params, dict) else None
        
        def perform_tap():
            # Regular Search - wait_for_element_or_fail already handles retries/wait/visibility
            el = wait_for_element_or_fail(query, timeout=timeout, step_context=step_context, index=index)
            
            # Extract bounds
            attrs = el.get("attributes", {})
            bounds = attrs.get("bounds")
            
            # Use center coordinates
            cx, cy = get_center(bounds)
            if cx:
                run_adb(f"shell input tap {cx} {cy}")
                return f"Tap '{query}'" + (f" [{index}]" if index is not None else "")
            
            raise Exception(f"Element found but no valid center for bounds: {query}")

        try:
            return retry_operation(perform_tap, max_retries=5, retry_delay=1.0, operation_name=f"Tap '{query}'")
        except Exception as e:
            if is_optional: return f"Skip optional tap: '{query}'"
            
            # Special handling for "Allow" (Permission Dialogs)
            # FAST PATH: Check common IDs immediately if query is broadly "allow"
            if "allow" in query.lower():
                print("[DEBUG] Permission dialog suspected. Checking common IDs...")
                permission_ids = [
                    "com.android.permissioncontroller:id/permission_allow_button",
                    "com.android.permissioncontroller:id/permission_allow_foreground_only_button",
                    "com.android.packageinstaller:id/permission_allow_button",
                    "com.android.permissioncontroller:id/permission_allow_one_time_button",
                    "android:id/button1"
                ]
                
                # Try IDs first (faster than hierarchy text scan)
                for pid in permission_ids:
                    try:
                        # Quick check if ID exists in current hierarchy (optimization)
                        if perform_tap_id_only(pid):
                             return f"Tap Permission Allow (via ID fast-path)"
                    except:
                        continue
                        
                # Then try text variations
                extra_queries = ["ALLOW", "While using the app", "Only this time"]
                root = get_hierarchy()
                for eq in extra_queries:
                     if perform_tap_text_only(eq, root):
                         return f"Tap '{eq}' (via variation fallback)"

            # Fallback: AI Vision
            api_key = os.getenv("RATT_OPENAI_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if api_key:
                print(f"[DEBUG] Element '{query}' not found via hierarchy. Trying AI Vision...")
                try:
                    snap_path = take_screenshot("vision_check")
                    coords = call_ai_vision(snap_path, query, api_key)
                    if coords:
                        run_adb(f"shell input tap {coords[0]} {coords[1]}")
                        return f"Tap '{query}' (via AI Vision)"
                except Exception as vision_err:
                    print(f"[DEBUG] AI Vision failed: {vision_err}")
            
            raise Exception(f"Element '{query}' not found. {str(e)}")

    elif s.type == "assertVisible":
        query = resolve_query(s.params)
        index = s.params.get("index") if isinstance(s.params, dict) else None
        timeout = s.params.get("timeout", 50) if isinstance(s.params, dict) else 50
        
        def perform_assert():
            wait_for_element_or_fail(query, timeout=timeout, step_context=step_context, index=index)
            return f"Assert Valid: '{query}'" + (f" [{index}]" if index is not None else "")
        
        # Retry assertion up to 3 times
        return retry_operation(perform_assert, max_retries=3, retry_delay=0.5, operation_name=f"Assert '{query}'")

    elif s.type == "assertNotVisible":
        query = resolve_query(s.params)
        # Quick check, no wait needed usually, or short wait to ensure animation finished?
        root = get_hierarchy()
        el = find_element(root, query)
        if el:
            take_screenshot("failure_visible")
            raise Exception(f"Element should NOT be visible: {query}")
        return f"Assert Not Visible: '{query}'"

    elif s.type == "back":
        mark_interaction()
        run_adb("shell input keyevent 4")
        return "Pressed Back"

    elif s.type == "stopApp" or s.type == "killApp":
        app_id = s.params
        if isinstance(s.params, dict):
             app_id = s.params.get("appId")
        run_adb(f"shell am force-stop {app_id}")
        return f"stopped App {app_id}"

    elif s.type == "openLink":
        link = s.params
        if isinstance(s.params, dict):
             link = s.params.get("link")
        run_adb(f"shell am start -a android.intent.action.VIEW -d {link}")
        return f"Open Link {link}"
        
    elif s.type == "eraseText":
        chars = 50
        if isinstance(s.params, int):
             chars = s.params
        elif isinstance(s.params, dict) and "characters" in s.params:
             chars = s.params["characters"]
        
        # Send Backspace N times
        cmd = "test" # dummy
        # Use a loop or multiple events
        # 'input keyevent 67 67 ...'
        events = " ".join(["67"] * chars)
        # If too long, split
        run_adb(f"shell input keyevent {events}")
        return f"Erased {chars} chars"

    elif s.type == "doubleTapOn":
        # Similar to tapOn but twice
        query = resolve_query(s.params)
        el = wait_for_element_or_fail(query, timeout=5)
        attrs = el.get("attributes", {})
        cx, cy = get_center(attrs["bounds"])
        if cx:
            run_adb(f"shell input tap {cx} {cy}")
            time.sleep(0.1)
            run_adb(f"shell input tap {cx} {cy}")
            return f"Double Tap '{query}'"
        raise Exception(f"No bounds for {query}")

    elif s.type == "longPressOn":
         # input swipe x y x y duration
         query = resolve_query(s.params)
         el = wait_for_element_or_fail(query, timeout=5)
         attrs = el.get("attributes", {})
         cx, cy = get_center(attrs["bounds"])
         if cx:
             run_adb(f"shell input swipe {cx} {cy} {cx} {cy} 1000")
             return f"Long Press '{query}'"
         raise Exception(f"No bounds for {query}")

    elif s.type == "inputText":
        input_text(s.params)
        time.sleep(0.1)  # Small delay to ensure text is processed
        return f"Input: {s.params}"

    elif s.type == "pressKey":
        key = s.params
        key_map = {"Enter": "66", "Back": "4", "Home": "3"}
        code = key_map.get(key, key)
        mark_interaction()
        run_adb(f"shell input keyevent {code}")
        return f"Key: {key}"

    elif s.type == "hideKeyboard":
        # Key event 111 is ESCAPE, often closes keyboard. 
        # Alternatively 4 (BACK) but that might navigate if no keyboard.
        # Let's try 111 first, or we can use 'input method hide' if available?
        # Safe bet: keyevent 111
        run_adb("shell input keyevent 111")
        time.sleep(0.5)
        return "Hide Keyboard"

    elif s.type == "scroll":
        mark_interaction()
        direction = "DOWN"
        query = None
        if isinstance(s.params, dict):
            direction = s.params.get("direction", "DOWN")
            query = resolve_query(s.params.get("element"))
        
        w, h = get_screen_size()
        
        # If element is provided, scroll within its center
        if query:
            root = get_hierarchy()
            el = find_element(root, query)
            if el:
                bounds = el.get("bounds")
                cx = (bounds["left"] + bounds["right"]) // 2
                cy = (bounds["top"] + bounds["bottom"]) // 2
                # Use a larger distance to ensure content moves (60% of element)
                dist_h = int(bounds["width"] * 0.3)
                dist_v = int(bounds["height"] * 0.3)
                
                if direction == "DOWN":
                    run_adb(f"shell input swipe {cx} {cy + dist_v} {cx} {cy - dist_v} 1000")
                elif direction == "UP":
                    run_adb(f"shell input swipe {cx} {cy - dist_v} {cx} {cy + dist_v} 1000")
                elif direction == "RIGHT":
                    run_adb(f"shell input swipe {cx + dist_h} {cy} {cx - dist_h} {cy} 1000")
                elif direction == "LEFT":
                    run_adb(f"shell input swipe {cx - dist_h} {cy} {cx + dist_h} {cy} 1000")
                return f"Scroll {direction} on '{query}'"

        # Global scroll
        cx, cy = w // 2, h // 2
        if direction == "DOWN":
            run_adb(f"shell input swipe {cx} {int(h * 0.8)} {cx} {int(h * 0.2)} 1000")
        elif direction == "UP":
            run_adb(f"shell input swipe {cx} {int(h * 0.2)} {cx} {int(h * 0.8)} 1000")
        elif direction == "RIGHT":
            run_adb(f"shell input swipe {int(w * 0.8)} {cy} {int(w * 0.2)} {cy} 1000")
        elif direction == "LEFT":
            run_adb(f"shell input swipe {int(w * 0.2)} {cy} {int(w * 0.8)} {cy} 1000")
            
        return f"Scroll {direction}"

    elif s.type == "scrollUntilVisible":
        if isinstance(s.params, dict):
             target_query = s.params.get("element")
             # Handle nested map if element is complex or just string
             if isinstance(target_query, dict):
                 # e.g. element: { text: "Foo" } -> resolve
                 query = resolve_query(target_query)
             else:
                 query = target_query
                 
             direction = s.params.get("direction", "DOWN")
        else:
             query = s.params
             direction = "DOWN"
        
        print(f"[DEBUG] Scroll {direction} until '{query}' visible")
        
        max_scrolls = 15
        found = False
        
        for i in range(max_scrolls):
            # Check visibility
            root = get_hierarchy()
            if find_element(root, query):
                found = True
                break
            
            # Not found, scroll
            w, h = get_screen_size()
            cx = w // 2
            
            # Scroll behavior
            if direction == "DOWN":
                # Scroll DOWN content = Swipe UP
                run_adb(f"shell input swipe {cx} {int(h * 0.8)} {cx} {int(h * 0.2)} 1000")
            elif direction == "UP":
                # Scroll UP content = Swipe DOWN
                run_adb(f"shell input swipe {cx} {int(h * 0.2)} {cx} {int(h * 0.8)} 1000")
            elif direction == "RIGHT":
                # Scroll RIGHT content = Swipe LEFT
                run_adb(f"shell input swipe {int(w * 0.8)} {cy} {int(w * 0.2)} {cy} 1000")
            elif direction == "LEFT":
                # Scroll LEFT content = Swipe RIGHT
                run_adb(f"shell input swipe {int(w * 0.2)} {cy} {int(w * 0.8)} {cy} 1000")
            
            time.sleep(1.0) # Wait for scroll to settle
            
        if not found:
             raise Exception(f"Element '{query}' not found after scrolling {direction} {max_scrolls} times")
             
        return f"Scrolled {direction} to find '{query}'"

    elif s.type == "swipe":
        mark_interaction()
        direction = "LEFT"
        duration = 500
        query = None
        
        if isinstance(s.params, dict):
            direction = s.params.get("direction", "LEFT")
            duration = s.params.get("duration", 500)
            query = resolve_query(s.params.get("element"))
        
        w, h = get_screen_size()
        
        # If element is provided, swipe within element bounds
        if query:
            root = get_hierarchy()
            el = find_element(root, query)
            if not el:
                raise Exception(f"Swipe failed: Element '{query}' not found")
            
            bounds = el.get("bounds")
            cx, cy = (bounds["left"] + bounds["right"]) // 2, (bounds["top"] + bounds["bottom"]) // 2
            width, height = bounds["width"], bounds["height"]
            
            if direction == "LEFT":
                run_adb(f"shell input swipe {int(cx + width*0.3)} {cy} {int(cx - width*0.3)} {cy} {duration}")
            elif direction == "RIGHT":
                run_adb(f"shell input swipe {int(cx - width*0.3)} {cy} {int(cx + width*0.3)} {cy} {duration}")
            elif direction == "DOWN":
                run_adb(f"shell input swipe {cx} {int(cy - height*0.3)} {cx} {int(cy + height*0.3)} {duration}")
            elif direction == "UP":
                run_adb(f"shell input swipe {cx} {int(cy + height*0.3)} {cx} {int(cy - height*0.3)} {duration}")
        else:
            # Global swipe (centered)
            cx, cy = w // 2, h // 2
            if direction == "LEFT":
                run_adb(f"shell input swipe {int(w*0.7)} {cy} {int(w*0.3)} {cy} {duration}")
            elif direction == "RIGHT":
                run_adb(f"shell input swipe {int(w*0.3)} {cy} {int(w*0.7)} {cy} {duration}")
            elif direction == "DOWN":
                run_adb(f"shell input swipe {cx} {int(h*0.3)} {cx} {int(h*0.7)} {duration}")
            elif direction == "UP":
                run_adb(f"shell input swipe {cx} {int(h*0.7)} {cx} {int(h*0.3)} {duration}")
        
        return f"Swipe {direction}"

    elif s.type == "wait":
        # Wait for specified milliseconds
        duration_ms = s.params if isinstance(s.params, (int, float)) else 1000
        duration_sec = duration_ms / 1000
        time.sleep(duration_sec)
        return f"Wait {duration_ms}ms"

    elif s.type == "waitForAnimationToEnd":
        # Rough approximation: wait for UI to settle
        time.sleep(10.0)
        return "Wait animation to end (10s)"


    elif s.type == "extendedWaitUntil":
        # Check if awaiting visibility or not visibility
        timeout_ms = s.params.get("timeout", 5000)
        timeout_s = timeout_ms / 1000
        
        # Determine query from berbagai possible keys (visible, assertVisible, etc.)
        target = s.params.get("visible") or s.params.get("assertVisible")
        if target:
            query = resolve_query(target)
            index = target.get("index") if isinstance(target, dict) else None
            wait_for_element_or_fail(query, timeout=timeout_s, step_context=step_context, index=index)
            return f"Wait until visible: {query}"
            
        target_not = s.params.get("notVisible") or s.params.get("assertNotVisible")
        if target_not:
            query = resolve_query(target_not)
            index = target_not.get("index") if isinstance(target_not, dict) else None
            start = time.time()
            while time.time() - start < timeout_s:
                root = get_hierarchy()
                if not find_element(root, query, index=index):
                    return f"Wait until not visible: {query}"
                time.sleep(0.5)
            raise Exception(f"Element still visible after {timeout_s}s: {query}")
             
        time.sleep(timeout_s)
        return f"Wait {timeout_ms}ms"
        
    return f"Skipped {s.type}"

def execute_flow(flow, global_app_id, run_id=None):
    history = []
    for i, step in enumerate(flow):
        # Inject appId if needed
        if isinstance(step, dict) and "launchApp" in step:
            if isinstance(step["launchApp"], dict) and "appId" not in step["launchApp"] and global_app_id:
                step["launchApp"]["appId"] = global_app_id

        try:
            # Send 'running' status before starting the step
            yield f"data: [{i+1}/{len(flow)}] step (running)\n\n"
            
            # Consume generator from run_test_step
            log = "Step Completed"
            for msg in run_test_step(step, run_id=run_id, step_index=i, history=history):
                if msg.startswith("RETURN:"):
                    log = msg.replace("RETURN:", "", 1)
                elif msg.startswith("[AI-BOT]"):
                    yield f"data: {msg}\n\n"
                elif msg.startswith("[HEALER]"):
                    yield f"data: {msg}\n\n"
                else:
                    # Debug logs or others
                    print(msg) 
            
            # Record step to history
            history.append({"step": step, "log": log, "status": "PASS"})
            yield f"data: [{i+1}/{len(flow)}] {log} (completed)\n\n"
        except Exception as e:
            history.append({"step": step, "error": str(e), "status": "FAIL"})
            yield f"data: [{i+1}/{len(flow)}] {str(e)} (failed)\n\n"
            raise e

def run_yaml_custom(yaml_content, api_key=None, filename=""):
    # Set key for this run
    if api_key:
        os.environ["RATT_OPENAI_KEY"] = api_key
        
    try:
        docs = list(yaml.safe_load_all(yaml_content))
        header = docs[0] if len(docs) > 0 else {}
        flow = docs[1] if len(docs) > 1 else (docs[0] if isinstance(docs[0], list) else [])
        
        yield f"data: [STARTING] Test Run\n\n"
        
        global_app_id = header.get("appId") if isinstance(header, dict) else None
        
        # AI RUN TRACKING: Start Run
        # Use filename (without .yaml) if no name in header
        if filename and filename.endswith('.yaml'):
            default_name = filename[:-5]  # Remove .yaml extension
        else:
            default_name = filename if filename else "Unnamed Test"
        
        run_name = header.get("name", default_name)
        
        # Determine mode based on history
        mode = "LEARN"
        for r in sorted(intelligence.raw_data["runs"], key=lambda x: str(x.get("started_at", "")), reverse=True):
             if r.get("test_name") == run_name and r.get("status") == "PASS":
                 mode = "FAST"
                 break
                 
        run_id = intelligence.start_run(run_name, mode=mode)
        global current_run_id
        current_run_id = run_id
        start_time = time.time()
        
        # AI PLANNER: Analyze test flow before execution
        try:
            from agents.planner_agent import planner_agent
            
            # Get memory stats for this test
            memory_stats = {
                "previous_runs": len([r for r in intelligence.raw_data["runs"] if r.get("test_name") == run_name]),
                "mode": mode
            }
            
            plan = planner_agent.plan_execution(flow, memory_stats)
            if plan:
                yield f"data: [AI-PLANNER] 🎯 Execution Plan Generated:\n\n"
                yield f"data: [AI-PLANNER] - Risk Level: {plan.get('risk_level', 'UNKNOWN')} (Score: {plan.get('risk_score', 0)})\n\n"
                yield f"data: [AI-PLANNER] - Mode: {plan.get('execution_mode', 'NORMAL')}\n\n"
                yield f"data: [AI-PLANNER] - Reasoning: {plan.get('reasoning', 'N/A')}\n\n"
                if plan.get('potential_flaky_steps'):
                    yield f"data: [AI-PLANNER] - ⚠️  Potentially Flaky Steps: {plan.get('potential_flaky_steps')}\n\n"
        except Exception as e:
            print(f"[DEBUG] Planner Agent failed: {e}")
        
        try:
            for msg in execute_flow(flow, global_app_id, run_id=run_id):
                yield msg
            
            # AI RUN TRACKING: End Run (Pass)
            duration = int((time.time() - start_time) * 1000)
            intelligence.end_run(run_id, "PASS", duration)
            
            # AI IMPROVER: Check for suggestions
            try:
                suggestions = improver.analyze_memory(intelligence.storage_path)
                if suggestions:
                    yield f"data: [AI-IMPROVER] 💡 Found {len(suggestions)} Improvement Suggestions:\n\n"
                    for s in suggestions:
                        yield f"data: [AI-IMPROVER] - {s['type']}: {s['suggestion']} ({s.get('metric', '')})\n\n"
            except Exception as e:
                print(f"[DEBUG] Improver failed: {e}")

            yield f"data: [DONE] EXIT_CODE: 0\n\n"
            yield f"data: [REPORT] Run ID: {run_id}\n\n"
        except Exception as e:
            # AI RUN TRACKING: End Run (Fail)
            duration = int((time.time() - start_time) * 1000)
            intelligence.end_run(run_id, "FAIL", duration)
            yield f"data: [ERROR] {str(e)}\n\n"
            yield f"data: [DONE] EXIT_CODE: 1\n\n"
            yield f"data: [REPORT] Run ID: {run_id}\n\n"
        
    except Exception as e:
        yield f"data: [ERROR] {str(e)}\n\n"

def run_folder_custom(folder_path):
    import os
    try:
        if not os.path.isdir(folder_path):
             yield f"data: [ERROR] Not a folder: {folder_path}\n\n"
             return

        files = sorted([f for f in os.listdir(folder_path) if f.endswith('.yaml') or f.endswith('.yml')])
        
        if not files:
            yield f"data: [ERROR] No YAML files found in {folder_path}\n\n"
            return

        yield f"data: [INFO] Found {len(files)} tests in folder\n\n"
        
        failures = 0

        for idx, filename in enumerate(files):
            yield f"data: [INFO] === Running {filename} ({idx+1}/{len(files)}) ===\n\n"
            full_path = os.path.join(folder_path, filename)
            
            with open(full_path, 'r') as f:
                content = f.read()
            
            try:
                docs = list(yaml.safe_load_all(content))
                header = docs[0] if len(docs) > 0 else {}
                flow = docs[1] if len(docs) > 1 else (docs[0] if isinstance(docs[0], list) else [])
                global_app_id = header.get("appId") if isinstance(header, dict) else None
                
                for msg in execute_flow(flow, global_app_id):
                    yield msg
                
                yield f"data: [SUCCESS] {filename} passed\n\n"
            except Exception as e:
                failures += 1
                yield f"data: [ERROR] {filename} failed: {str(e)}\n\n"
                # Continue to next test or stop? Usually continue in bulk run is better.
                # But user flow might depend on previous.
                # I'll continue for now.
        
        if failures == 0:
            yield f"data: [DONE] EXIT_CODE: 0\n\n"
        else:
            yield f"data: [DONE] EXIT_CODE: 1\n\n"

    except Exception as e:
        yield f"data: [ERROR] {str(e)}\n\n"
def run_goal_autonomous(goal: str, app_id: Optional[str] = None, api_key: Optional[str] = None):
    """
    Autonomous loop: 
    1. Observe Screen
    2. Plan Step
    3. Execute
    4. Repeat until Goal Reached or Max Steps (15)
    """
    if api_key:
        os.environ["RATT_OPENAI_KEY"] = api_key

    history = []
    max_steps = 15
    run_id = intelligence.start_run(f"Goal: {goal[:20]}...", mode="LEARN")
    global current_run_id
    current_run_id = run_id
    
    yield f"data: [STARTING] Autonomous Goal Run: '{goal}'\n\n"
    
    if app_id:
        yield f"data: [INFO] Launching app '{app_id}'...\n\n"
        # Use run_test_step to launch properly
        launch_step = {"launchApp": {"appId": app_id, "clearState": True}}
        for msg in run_test_step(launch_step, run_id=run_id):
            if not msg.startswith("RETURN:"):
                yield f"data: {msg}\n\n"
    
    for i in range(max_steps):
        yield f"data: [GOAL-AGENT] Step {i+1}: Observing screen...\n\n"
        hierarchy = get_hierarchy(force_refresh=True)
        
        plan_res = goal_agent.plan_steps(goal, hierarchy, history)
        explanation = plan_res.get("explanation", "Thinking...")
        yield f"data: [GOAL-AGENT] 🧠 {explanation}\n\n"
        
        if plan_res.get("is_goal_reached"):
            yield f"data: [SUCCESS] Goal Reached! 🎉\n\n"
            intelligence.end_run(run_id, "PASS", 0)
            yield f"data: [DONE] EXIT_CODE: 0\n\n"
            return

        steps = plan_res.get("plan", [])
        if not steps:
            yield f"data: [ERROR] Goal Agent stuck: No steps generated.\n\n"
            intelligence.end_run(run_id, "FAIL", 0)
            yield f"data: [DONE] EXIT_CODE: 1\n\n"
            return

        # Execute planned steps
        for step in steps:
            # Prepare step context for intelligence
            yield f"data: [EXEC] Action: {json.dumps(step)}\n\n"
            
            try:
                res_msg = "Completed"
                for msg in run_test_step(step, run_id=run_id, step_index=i, history=history):
                    if msg.startswith("RETURN:"):
                        res_msg = msg.replace("RETURN:", "", 1)
                    else:
                        yield f"data: {msg}\n\n"
                
                history.append({"action": step, "result": res_msg})
                
                # RE-OBSERVE: After each action, the screen might change.
                # If we have more steps planned, we should ideally verify if they still make sense
                # or just break and let the outer loop re-plan from the new state.
                break # Favor re-planning after every single action for max robustness.

            except Exception as e:
                yield f"data: [ERROR] Step failed: {str(e)}\n\n"
                intelligence.end_run(run_id, "FAIL", 0)
                yield f"data: [DONE] EXIT_CODE: 1\n\n"
                return

    yield f"data: [ERROR]Reached max steps ({max_steps}) without hitting goal.\n\n"
    intelligence.end_run(run_id, "FAIL", 0)
    yield f"data: [DONE] EXIT_CODE: 1\n\n"
