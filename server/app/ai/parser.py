"""Utilities for parsing raw LLM responses"""

import json, re
from app.ai.exceptions import AIResponseParsingError

class AIResponseParser:
    """Coverts raw LLM responses to python dictionaries"""
    
    @staticmethod
    def parse_json(raw_response : str) ->  dict:
        if not raw_response:
            raise AIResponseParsingError("Received empty AI response")
        
        cleaned = raw_response.strip()
        
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE)
        
        cleaned = re.sub(r"```$", "", cleaned)
        
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise AIResponseParsingError("Unable to parse AI response into JSON") from exc