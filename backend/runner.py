import subprocess
import yaml
import time
import re
import xml.etree.ElementTree as ET
import os
import json
import requests
import base64

_hierarchy_cache = {"data": None, "time": 0}

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
    
    # Check Environment Fallbacks if no key passed
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
    px = float(px_str.replace("%", "")) / 100.0
    py = float(py_str.replace("%", "")) / 100.0
    tap_point(int(w * px), int(h * py))

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

def get_hierarchy():
    global _hierarchy_cache
    now = time.time()
    
    if _hierarchy_cache["data"] and (now - _hierarchy_cache["time"] < 1.0):
        return _hierarchy_cache["data"]

    try:
        # 1. Native ADB dump (fast)
        # Ensure we don't read partial data by checking return code
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
                        _hierarchy_cache = {"data": data, "time": now}
                        return data
                    except Exception as parse_err:
                        print(f"[DEBUG] XML Parse error: {parse_err}")
                else:
                    print(f"[DEBUG] Incomplete XML structure: start={start_xml}, end={end_xml}")
            else:
                print(f"[DEBUG] No XML tag found in dump output")
        else:
            print(f"[DEBUG] ‘uiautomator dump’ failed with return code {dump_proc.returncode}")
            
        # 2. Fallback to maestro hierarchy
        print("[DEBUG] Native dump failed or invalid, falling back to maestro")
        result = subprocess.run(["maestro", "hierarchy"], capture_output=True, text=True, timeout=30, env={**os.environ, "MAESTRO_OUTPUT_NO_COLOR": "true"})
        output = result.stdout
        start = output.find('{')
        end = output.rfind('}')
        if start != -1 and end != -1:
            data = json.loads(output[start:end+1])
            _hierarchy_cache = {"data": data, "time": now}
            return data
    except Exception as e:
        print(f"[ERROR] Hierarchy error: {e}")
    return {"children": []}


def get_hierarchy_json():
    data = get_hierarchy()
    return json.dumps(data)

def find_element(node, query):
    """
    Find an element in the UI hierarchy matching the query.
    Optimized two-pass approach:
    1. Fast path: Look for exact clickable matches first
    2. Slow path: Collect and score all matches if no exact clickable found
    """
    if not node: return None
    
    target = str(query)
    is_regex = target.startswith("regexp:")
    
    # Fast path: Try to find exact clickable match first (most common case)
    if not is_regex:
        q_lower = target.lower()
        
        def find_exact_clickable(n):
            """Recursively search for exact clickable match"""
            if not n:
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
    
    # Slow path: Collect all matches and score them
    def collect_matches(n, matches):
        if not n:
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
    
    # Sort by score (highest first) and return best match
    all_matches.sort(key=lambda x: x["score"], reverse=True)
    best = all_matches[0]
    
    # Only log if there were multiple matches (helps debug ambiguous cases)
    if len(all_matches) > 1:
        print(f"[DEBUG] Found '{target}': matched '{best['text']}' (score={best['score']}, {len(all_matches)} total matches)")
    
    return best["node"]

def get_center(bounds_str):
    # "[0,0][1080,210]"
    try:
        match = re.search(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            return (x1 + x2) // 2, (y1 + y2) // 2
    except:
        pass
    return None

def input_text(text):
    # Escape spaces
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
    if isinstance(params, str): return params
    if "point" in params: return None
    # simplify: first text key or id
    clean = {k:v for k,v in params.items() if k not in ["timeout", "optional"]}
    if clean: return next(iter(clean.values()))
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

def wait_for_element_or_fail(query, timeout=10):
    start = time.time()
    print(f"[DEBUG] Waiting for element: {query} (timeout {timeout}s)")
    while time.time() - start < timeout:
        root = get_hierarchy()
        if not root:
             print("[DEBUG] Hierarchy is None")
             time.sleep(0.5)
             continue
             
        el = find_element(root, query)
        if el: 
            print(f"[DEBUG] Element found: {query}")
            return el
        
        print(f"[DEBUG] Element '{query}' not found... retrying")
        time.sleep(0.5)
    
    # Timeout -> Fail
    print(f"[DEBUG] FAIL: Element not found: {query}")
    take_screenshot("failure_timeout")
    raise Exception(f"Element not found: {query} (timeout {timeout}s)")

def run_test_step(step):
    s = StepData(step)
    
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
            px_str, py_str = str(s.params["point"]).split(",")
            tap_point_percent(px_str, py_str)
            return f"Tap Point: {px_str},{py_str}"
            
        query = resolve_query(s.params)
        
        def perform_tap():
            el = wait_for_element_or_fail(query, timeout=timeout)
            if el and "bounds" in el.get("attributes", {}):
                attrs = el.get("attributes", {})
                is_enabled = attrs.get("enabled", "true")
                if isinstance(is_enabled, str):
                    is_enabled = is_enabled.lower() == "true"
                if not is_enabled:
                    raise Exception(f"Element '{query}' found but is DISABLED (not clickable)")
                cx, cy = get_center(attrs["bounds"])
                if cx:
                    run_adb(f"shell input tap {cx} {cy}")
                    return f"Tap '{query}'"
            raise Exception(f"Element found but no bounds: {query}")
        
        try:
            return retry_operation(perform_tap, max_retries=2, retry_delay=0.3, operation_name=f"Tap '{query}'")
        except Exception as e:
            if is_optional: return f"Skip optional tap: '{query}'"
            api_key = os.getenv("RATT_OPENAI_KEY") or os.getenv("OPENAI_API_KEY")
            if api_key:
                snap_path = take_screenshot("vision_check")
                coords = call_ai_vision(snap_path, query, api_key)
                if coords:
                    run_adb(f"shell input tap {coords[0]} {coords[1]}")
                    return f"Tap '{query}' (via AI Vision)"
            raise Exception(f"Element '{query}' not found. {str(e)}")

    elif s.type == "assertVisible":
        query = resolve_query(s.params)
        
        def perform_assert():
            wait_for_element_or_fail(query, timeout=50)
            return f"Assert Valid: '{query}'"
        
        # Retry assertion up to 3 times
        return retry_operation(perform_assert, max_retries=3, retry_delay=0.5, operation_name=f"Assert '{query}'")

    elif s.type == "assertNotVisible":
        query = resolve_query(s.params)
        # Quick check, no wait needed usually, or short wait to ensure animation finished?
        # Maestro default: if found -> fail.
        root = get_hierarchy()
        el = find_element(root, query)
        if el:
            take_screenshot("failure_visible")
            raise Exception(f"Element should NOT be visible: {query}")
        return f"Assert Not Visible: '{query}'"

    elif s.type == "inputText":
        input_text(s.params)
        time.sleep(0.1)  # Small delay to ensure text is processed
        return f"Input: {s.params}"

    elif s.type == "pressKey":
        key = s.params
        key_map = {"Enter": "66", "Back": "4", "Home": "3"}
        code = key_map.get(key, key)
        run_adb(f"shell input keyevent {code}")
        return f"Key: {key}"

    elif s.type == "scroll":
        direction = "DOWN"
        if isinstance(s.params, dict):
            direction = s.params.get("direction", "DOWN")
        
        w, h = get_screen_size()
        cx = w // 2
        
        # Scroll DOWN means content moves up, so we swipe UP (Bottom -> Top)
        if direction == "DOWN":
            start_y = int(h * 0.7)
            end_y = int(h * 0.3)
            run_adb(f"shell input swipe {cx} {start_y} {cx} {end_y} 1000")
        # Scroll UP means content moves down, so we swipe DOWN (Top -> Bottom)
        elif direction == "UP":
            start_y = int(h * 0.3)
            end_y = int(h * 0.7)
            run_adb(f"shell input swipe {cx} {start_y} {cx} {end_y} 1000")
            
        return f"Scroll {direction}"

    elif s.type == "swipe":
        direction = None
        if isinstance(s.params, dict):
            direction = s.params.get("direction")
        
        if direction:
             w, h = get_screen_size()
             cx = w // 2
             cy = h // 2
             
             if direction == "LEFT":
                 run_adb(f"shell input swipe {int(w*0.8)} {cy} {int(w*0.2)} {cy} 500")
             elif direction == "RIGHT":
                 run_adb(f"shell input swipe {int(w*0.2)} {cy} {int(w*0.8)} {cy} 500")
             elif direction == "DOWN":
                 run_adb(f"shell input swipe {cx} {int(h*0.2)} {cx} {int(h*0.8)} 500")
             elif direction == "UP":
                 run_adb(f"shell input swipe {cx} {int(h*0.8)} {cx} {int(h*0.2)} 500")
             return f"Swipe {direction}"
        
        return "Swipe (Custom coordinates not implemented)"

    elif s.type == "wait":
        # Wait for specified milliseconds
        duration_ms = s.params if isinstance(s.params, (int, float)) else 1000
        duration_sec = duration_ms / 1000
        time.sleep(duration_sec)
        return f"Wait {duration_ms}ms"

    elif s.type == "waitForAnimationToEnd":
        time.sleep(0.5)
        return "Wait animation"
        
    elif s.type == "extendedWaitUntil":
        # Check if awaiting visibility or not visibility
        timeout = s.params.get("timeout", 5000) / 1000
        if "visible" in s.params:
            query = resolve_query(s.params["visible"])
            wait_for_element_or_fail(query, timeout)
            return f"Wait until visible: {query}"
        elif "notVisible" in s.params:
             query = resolve_query(s.params["notVisible"])
             start = time.time()
             while time.time() - start < timeout:
                 root = get_hierarchy()
                 if not find_element(root, query):
                     return f"Wait until not visible: {query}"
                 time.sleep(2.0)
             raise Exception(f"Element still visible: {query}")
             
        time.sleep(timeout)
        return f"Sleep {timeout}s"
        
    return f"Skipped {s.type}"

def execute_flow(flow, global_app_id):
    for i, step in enumerate(flow):
        # Inject appId
        if "launchApp" in step:
                if isinstance(step["launchApp"], dict) and "appId" not in step["launchApp"] and global_app_id:
                    step["launchApp"]["appId"] = global_app_id

        
        try:
            # Send 'running' status before starting the step
            yield f"data: [{i+1}/{len(flow)}] step (running)\n\n"
            log = run_test_step(step)
            yield f"data: [{i+1}/{len(flow)}] {log} (completed)\n\n"
        except Exception as e:
            yield f"data: [{i+1}/{len(flow)}] {str(e)} (failed)\n\n"
            raise e

def run_yaml_custom(yaml_content, api_key=None):
    # Set key for this run
    if api_key:
        os.environ["RATT_OPENAI_KEY"] = api_key
        
    try:
        docs = list(yaml.safe_load_all(yaml_content))
        header = docs[0] if len(docs) > 0 else {}
        flow = docs[1] if len(docs) > 1 else (docs[0] if isinstance(docs[0], list) else [])
        
        yield f"data: [STARTING] Test Run\n\n"
        
        global_app_id = header.get("appId") if isinstance(header, dict) else None
        
        try:
            for msg in execute_flow(flow, global_app_id):
                yield msg
            yield f"data: [DONE] EXIT_CODE: 0\n\n"
        except:
            yield f"data: [ERROR] Test stopped due to failure.\n\n"
            yield f"data: [DONE] EXIT_CODE: 1\n\n"
        
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
