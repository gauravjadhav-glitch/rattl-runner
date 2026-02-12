import xml.etree.ElementTree as ET
import json
import os
from typing import List, Dict, Optional
from services.llm_service import ask_llm_json

class HybridResolver:
    def __init__(self):
        self.system_prompt = """
You are an AI UI Resolver. Your job is to match a user's intent to the best available element on a mobile screen.
You will be given a 'Target' (what the user wants) and a list of 'Candidates' (elements found in the UI XML).

Analyze the candidates based on:
1. Text similarity (e.g., "Save" matches "Save Changes")
2. Functional similarity (e.g., "Back" matches an arrow icon or "Cancel")
3. Context (e.g., if looking for "Login", buttons near username fields are likely)

Return the index of the best match and a confidence score (0-1).
If no match is found, return index -1.

OUTPUT FORMAT (JSON):
{
    "best_match_index": 2,
    "confidence": 0.95,
    "reasoning": "Target 'Save' semantically matches 'Save Changes' button."
}
"""

    def parse_xml_to_candidates(self, xml_path: str) -> List[Dict]:
        """Convert standard Android XML dump to a list of searchable candidates."""
        if not os.path.exists(xml_path):
            return []
            
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            candidates = []
            
            # Counter for unique ID within this dump
            element_id_counter = 0
            
            for node in root.iter("node"):
                text = node.attrib.get("text", "").strip()
                res_id = node.attrib.get("resource-id", "").strip()
                desc = node.attrib.get("content-desc", "").strip()
                bounds = node.attrib.get("bounds", "")
                
                # Only consider elements that have some metadata or are likely interactive
                if text or res_id or desc:
                    candidates.append({
                        "id": element_id_counter,
                        "text": text,
                        "resource_id": res_id,
                        "content_desc": desc,
                        "bounds": bounds,
                        "class": node.attrib.get("class", "")
                    })
                    element_id_counter += 1
            return candidates
        except Exception as e:
            print(f"[HybridResolver] XML Parse Error: {e}")
            return []

    def semantic_resolve(self, target: str, candidates: List[Dict]) -> Optional[Dict]:
        """Use LLM to find the best match based on meaning, not just exact strings."""
        if not candidates:
            return None

        # Filter candidates to send a concise list to the LLM (save tokens)
        simplified_candidates = []
        for c in candidates:
            simplified_candidates.append({
                "id": c["id"],
                "text": c["text"],
                "res": c["resource_id"].split("/")[-1] if c["resource_id"] else "", 
                "desc": c["content_desc"]
            })

        user_content = f"Target: {target}\nCandidates: {json.dumps(simplified_candidates)}"
        
        try:
            result = ask_llm_json(self.system_prompt, user_content)
            idx = result.get("best_match_index")
            confidence = result.get("confidence", 0)
            
            if idx != -1 and confidence > 0.6:
                # Find the original candidate
                for cand in candidates:
                    if cand["id"] == idx:
                        print(f"[HybridResolver] Semantic match found: '{target}' -> '{cand.get('text') or cand.get('resource_id')}' (Conf: {confidence})")
                        return cand
            return None
        except Exception as e:
            print(f"[HybridResolver] Semantic resolving failed: {e}")
            return None

    def resolve_with_json(self, query: str, data: Dict) -> Optional[Dict]:
        """Resolve query using the JSON hierarchy dictionary."""
        candidates = self.parse_json_to_candidates(data)
        
        if not candidates:
            return None

        # 1. Try Exact/Simple matching first (Fastest)
        query_lower = query.lower()
        for cand in candidates:
            if (cand["text"] and query_lower == cand["text"].lower()) or \
               (cand["resource_id"] and query_lower in cand["resource_id"].lower()) or \
               (cand["content_desc"] and query_lower == cand["content_desc"].lower()):
                print(f"[HybridResolver] Exact match found for '{query}'")
                return cand["node"]

        # 2. Try Semantic AI Matching (The Brain)
        print(f"[HybridResolver] No exact match for '{query}'. Trying semantic resolving...")
        semantic_match = self.semantic_resolve(query, candidates)
        if semantic_match:
            return semantic_match["node"]

        return None

    def parse_json_to_candidates(self, data: Dict) -> List[Dict]:
        """Convert the JSON hierarchy dictionary to a list of searchable candidates."""
        candidates = []
        element_id_counter = 0

        def traverse(node):
            nonlocal element_id_counter
            attrs = node.get("attributes", {})
            text = str(attrs.get("text", "")).strip()
            res_id = str(attrs.get("resource-id", "")).strip()
            desc = str(attrs.get("content-desc", "")).strip()
            bounds = attrs.get("bounds", "")

            if text or res_id or desc:
                candidates.append({
                    "id": element_id_counter,
                    "text": text,
                    "resource_id": res_id,
                    "content_desc": desc,
                    "bounds": bounds,
                    "class": attrs.get("class", ""),
                    "node": node
                })
                element_id_counter += 1

            for child in node.get("children", []):
                traverse(child)

        traverse(data)
        return candidates

    def resolve_with_root(self, query: str, root) -> Optional[Dict]:
        """Resolve query using a pre-parsed ElementTree root."""
        candidates = self.parse_root_to_candidates(root)
        
        if not candidates:
            return None

        # 1. Try Exact/Simple matching first (Fastest)
        query_lower = query.lower()
        for cand in candidates:
            if (cand["text"] and query_lower == cand["text"].lower()) or \
               (cand["resource_id"] and query_lower in cand["resource_id"].lower()) or \
               (cand["content_desc"] and query_lower == cand["content_desc"].lower()):
                print(f"[HybridResolver] Exact match found for '{query}'")
                return cand["node"]

        # 2. Try Semantic AI Matching (The Brain)
        print(f"[HybridResolver] No exact match for '{query}'. Trying semantic resolving...")
        semantic_match = self.semantic_resolve(query, candidates)
        if semantic_match:
            return semantic_match["node"]

        return None

    def parse_root_to_candidates(self, root) -> List[Dict]:
        """Convert ElementTree root to a list of searchable candidates."""
        candidates = []
        element_id_counter = 0
        
        for node in root.iter("node"):
            text = node.attrib.get("text", "").strip()
            res_id = node.attrib.get("resource-id", "").strip()
            desc = node.attrib.get("content-desc", "").strip()
            bounds = node.attrib.get("bounds", "")
            
            if text or res_id or desc:
                candidates.append({
                    "id": element_id_counter,
                    "text": text,
                    "resource_id": res_id,
                    "content_desc": desc,
                    "bounds": bounds,
                    "class": node.attrib.get("class", ""),
                    "node": node # Keep reference to original node
                })
                element_id_counter += 1
        return candidates

    def resolve(self, query: str, xml_path: str) -> Optional[Dict]:
        """The main entry point for the Hybrid Resolver using XML path."""
        if not os.path.exists(xml_path):
            return None
        try:
            tree = ET.parse(xml_path)
            return self.resolve_with_root(query, tree.getroot())
        except Exception as e:
            print(f"[HybridResolver] Error: {e}")
            return None

hybrid_resolver = HybridResolver()
