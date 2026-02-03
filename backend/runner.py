import subprocess
import yaml
import time
import re
import xml.etree.ElementTree as ET
import os
import json

_hierarchy_cache = {"data": None, "time": 0}

def run_adb(command):
    cmd = ["adb"] + command.split()
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def tap_point(x, y):
    run_adb(f"shell input tap {x} {y}")

def get_screen_size():
    res = run_adb("shell wm size").stdout
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
    if not node: return None
    
    # Normalize query
    q_str = str(query).lower()
    
    # Check attributes
    attributes = node.get("attributes", {})
    text = str(attributes.get("text", "")).lower()
    resource_id = str(attributes.get("resource-id", "")).lower()
    content_desc = str(attributes.get("content-desc", "")).lower()
    hint_text = str(attributes.get("hintText", "")).lower()
    hint = str(attributes.get("hint", "")).lower()

    # Fuzzy match logic:
    # 1. Exact match (highest priority - handled implicitly if contained)
    # 2. Substring match
    if (q_str in text and text) or \
       (q_str in resource_id and resource_id) or \
       (q_str in content_desc and content_desc) or \
       (q_str in hint_text and hint_text) or \
       (q_str in hint and hint):
        return node
        
    children = node.get("children", [])
    for child in children:
        found = find_element(child, query)
        if found: return found
        
    return None

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

def wait_for_element_or_fail(query, timeout=50):
    start = time.time()
    print(f"[DEBUG] Waiting for element: {query} (timeout {timeout}s)")
    while time.time() - start < timeout:
        root = get_hierarchy()
        if not root:
             print("[DEBUG] Hierarchy is None")
             time.sleep(2.0)
             continue
             
        el = find_element(root, query)
        if el: 
            print(f"[DEBUG] Element found: {query}")
            return el
        
        print(f"[DEBUG] Element '{query}' not found... retrying")
        time.sleep(2.0)
    
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
        if isinstance(s.params, dict) and "point" in s.params:
            coords = s.params["point"].split(",")
            tap_point_percent(coords[0], coords[1])
            return f"Tap {s.params['point']}"
        
        # Check if this is an optional tap (for permission dialogs, etc)
        is_optional = isinstance(s.params, dict) and s.params.get("optional", False)
        timeout = 5 if is_optional else 50
            
        query = resolve_query(s.params)
        
        try:
            el = wait_for_element_or_fail(query, timeout=timeout)
            
            if el and "bounds" in el.get("attributes", {}):
                cx, cy = get_center(el["attributes"]["bounds"])
                if cx:
                    run_adb(f"shell input tap {cx} {cy}")
                    return f"Tap '{query}'"
            raise Exception(f"Element found but no bounds: {query}")
        except Exception as e:
            if is_optional:
                print(f"[DEBUG] Optional tap skipped: {query} not found")
                return f"Skip optional tap: '{query}'"
            raise

    elif s.type == "assertVisible":
        query = resolve_query(s.params)
        wait_for_element_or_fail(query, timeout=50)
        return f"Assert Valid: '{query}'"

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

    elif s.type == "waitForAnimationToEnd":
        time.sleep(2)
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

def run_yaml_custom(yaml_content):
    try:
        docs = list(yaml.safe_load_all(yaml_content))
        header = docs[0] if len(docs) > 0 else {}
        flow = docs[1] if len(docs) > 1 else (docs[0] if isinstance(docs[0], list) else [])
        
        yield f"data: [STARTING] Strict Mode\n\n"
        
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
