import os
from typing import Dict, Any
import anthropic

class ClaudeExtractor:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def extract_content(self, text: str) -> Dict[str, Any]:
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": f"Extract key information from this text and return as structured data: {text}"
                }]
            )
            
            return {
                "success": True,
                "content": response.content[0].text,
                "model": "claude-3-sonnet"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }