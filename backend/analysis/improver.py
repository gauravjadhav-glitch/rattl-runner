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
                    stable_locator = None
                    new_locator_dict = None
                    if el.get("resource_id"):
                        stable_locator = f"id: \"{el.get('resource_id')}\""
                        new_locator_dict = {"id": el.get("resource_id")}
                    elif el.get("content_desc"):
                        stable_locator = f"accessibilityId: \"{el.get('content_desc')}\""
                        new_locator_dict = {"accessibilityId": el.get("content_desc")}
                    
                    suggestion_msg = f"Replace locator '{el.get('preferred_locator')}' with a more stable one."
                    if stable_locator:
                        suggestion_msg = f"Use more stable locator: {stable_locator}"

                    suggestions.append({
                        "type": "FLAKY_ELEMENT",
                        "screen": screen_id,
                        "element": el.get("text") or el.get("resource_id"),
                        "old_locator": el.get("text") if el.get("preferred_locator") == "text" else el.get("resource_id"),
                        "new_locator": new_locator_dict,
                        "metric": f"{success_rate*100:.1f}% Success Rate",
                        "suggestion": suggestion_msg
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

    def apply_improvements(self, workspace_dir: str, memory_file_path: str) -> List[str]:
        import os, glob
        suggestions = self.analyze_memory(memory_file_path)
        applied_fixes = []
        
        for s in suggestions:
            if s['type'] == 'FLAKY_ELEMENT' and s.get('new_locator') and s.get('old_locator'):
                old_loc = s['old_locator']
                new_key = list(s['new_locator'].keys())[0]
                new_val = list(s['new_locator'].values())[0]
                
                # We look for files containing the old_locator
                yaml_files = glob.glob(os.path.join(workspace_dir, "**/*.yaml"), recursive=True)
                for file_path in yaml_files:
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        # Supported patterns for replacement
                        replacements = {
                            f'tapOn: "{old_loc}"': f'tapOn:\n    {new_key}: "{new_val}"',
                            f'tapOn: {old_loc}': f'tapOn:\n    {new_key}: "{new_val}"',
                            f'assertVisible: "{old_loc}"': f'assertVisible:\n    {new_key}: "{new_val}"',
                            f'assertVisible: {old_loc}': f'assertVisible:\n    {new_key}: "{new_val}"',
                        }
                        
                        modified = False
                        new_content = content
                        for old_pat, new_pat in replacements.items():
                            if old_pat in new_content:
                                new_content = new_content.replace(old_pat, new_pat)
                                modified = True
                        
                        if modified:
                            with open(file_path, 'w') as f:
                                f.write(new_content)
                            applied_fixes.append(f"Fixed '{old_loc}' -> {new_key} in {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"[DEBUG] Error fixing file {file_path}: {e}")
        
        return list(set(applied_fixes)) # Unique fixes

improver = ImproverEngine()

