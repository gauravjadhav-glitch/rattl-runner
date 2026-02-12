import os
import json
from openai import OpenAI
from typing import Dict, Any, Optional

# Initialize client
client = None

def get_client():
    global client
    # Priority: RATT_OPENAI_KEY then OPENAI_API_KEY
    api_key = os.getenv("RATT_OPENAI_KEY") or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("[DEBUG] LLM Client: No API Key found in RATT_OPENAI_KEY or OPENAI_API_KEY")
        return None
    else:
        source = "RATT_OPENAI_KEY" if os.getenv("RATT_OPENAI_KEY") else "OPENAI_API_KEY"
        print(f"[DEBUG] LLM Client: Using API Key from {source}")
        
    # Re-initialize if key changed or client is None
    if client is None or getattr(client, "_api_key", None) != api_key:
        client = OpenAI(api_key=api_key)
        client._api_key = api_key # Store for comparison

    return client

def ask_llm(system_prompt: str, user_content: str, model: str = "gpt-4o") -> Optional[str]:
    """
    Generic function to query the LLM.
    Returns the raw string content of the response.
    """
    client = get_client()
    if not client:
        return None

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] LLM Query Failed: {e}")
        return None

def ask_llm_json(system_prompt: str, user_content: str, model: str = "gpt-4o") -> Optional[Dict[str, Any]]:
    """
    Queries the LLM and expects a JSON response.
    Handles parsing and basic error checking.
    """
    content = ask_llm(system_prompt, user_content, model)
    if not content:
        return None
        
    try:
        # Sanitize markdown code blocks if present
        json_str = content.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
             json_str = json_str.split("```")[1].split("```")[0].strip()
            
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON from LLM: {str(e)}")
        print(f"[DEBUG] Raw response: {content}")
        return None
