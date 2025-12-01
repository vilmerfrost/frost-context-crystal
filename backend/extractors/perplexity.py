import json
from datetime import datetime
from typing import List
import aiofiles
import uuid

from models.schemas import Conversation, Message, MessageRole, ConversationSource

class PerplexityExtractor:
    """Extractor for Perplexity AI"""
    
    async def extract_from_file(self, file_path: str) -> List[Conversation]:
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
                
            conversations = []
            items = data if isinstance(data, list) else [data]
            
            for item in items:
                messages = []
                # Perplexity usually has 'text' and 'role' or similar
                # This is a placeholder logic
                history = item.get('history', [])
                for h in history:
                    messages.append(Message(
                        role=MessageRole.USER if h.get('role') == 'user' else MessageRole.ASSISTANT,
                        content=h.get('text', '') or h.get('content', ''),
                        timestamp=datetime.now().timestamp(),
                        model="perplexity-sonar"
                    ))
                    
                if messages:
                    conversations.append(Conversation(
                        id=f"pplx_{uuid.uuid4()}",
                        source=ConversationSource.PERPLEXITY,
                        extracted_at=datetime.now().timestamp(),
                        messages=messages,
                        metadata={"title": item.get('title', 'Perplexity Thread')}
                    ))
            return conversations
        except Exception as e:
            print(f"Error Perplexity: {e}")
            return []
