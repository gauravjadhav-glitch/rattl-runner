from typing import Dict, Optional, List
import re

class CrashAnalyzer:
    """
    Analyzes application crashes by mapping stack traces/logcat to known modules.
    Currently uses simple regex/keywords but can be upgraded to LLM.
    """
    
    MODULE_MAP = {
        "com.google.android.gms": "Google Play Services",
        "okhttp3": "Network Layer",
        "retrofit2": "API Client",
        "androidx.appcompat": "UI Framework (AppCompat)",
        "androidx.fragment": "UI Navigation (Fragments)",
        "java.lang.NullPointerException": "Logic Error (Null Pointer)",
        "android.database.sqlite": "Database Error",
        "com.android.vending": "Google Play Store",
        "org.chromium": "WebView Component",
        "com.facebook": "Facebook SDK",
        "com.google.firebase": "Firebase",
    }

    def detect_module(self, stacktrace: str) -> str:
        """Determines which module crashed based on the stacktrace."""
        if not stacktrace: return "Unknown"
            
        for pattern, name in self.MODULE_MAP.items():
            if pattern in stacktrace:
                return name
                
        match = re.search(r"at (com\.[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)", stacktrace)
        if match: return f"Pkg: {match.group(1)}"
            
        return "Unknown"

    def analyze_with_ai(self, stacktrace: str) -> Optional[Dict]:
        """Use LLM to explain the crash and suggest a fix."""
        from services.llm_service import ask_llm_json
        
        system_prompt = "You are a Mobile Crash Expert. Analyze the stacktrace and explain why it happened and how to fix it."
        user_content = f"Stacktrace:\n{stacktrace}"
        
        try:
            return ask_llm_json(system_prompt, user_content)
        except:
            return None

    def is_crash(self, logs: str) -> bool:
        """Checks if the provided logs contain indicators of a crash."""
        crash_keywords = ["FATAL EXCEPTION", "ANR in", "Process: ", "SIGSEGV", "AndroidRuntime"]
        return any(keyword in logs for keyword in crash_keywords)

crash_analyzer = CrashAnalyzer()
