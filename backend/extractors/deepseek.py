import json
from datetime import datetime
from typing import List, Optional
import aiofiles
import uuid

from models.schemas import Conversation, Message, MessageRole, ConversationSource

class DeepseekExtractor:
    """Extractor for Deepseek Chat"""
    
    async def extract_from_file(self, file_path: str) -> List[Conversation]:
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
            
            conversations = []
            # Adjust parsing logic based on actual Deepseek export
            items = data if isinstance(data, list) else [data]
            
            for item in items:
                messages = []
                # Fake parsing logic - replace with real structure
                raw_msgs = item.get('messages', []) 
                for rm in raw_msgs:
                    messages.append(Message(
                        role=MessageRole.ASSISTANT if rm.get('role') == 'assistant' else MessageRole.USER,
                        content=rm.get('content', ''),
                        timestamp=datetime.now().timestamp(),
                        model="deepseek-chat"
                    ))
                
                if messages:
                    conversations.append(Conversation(
                        id=f"deepseek_{uuid.uuid4()}",
                        source=ConversationSource.DEEPSEEK,
                        extracted_at=datetime.now().timestamp(),
                        messages=messages,
                        metadata={}
                    ))
            return conversations
        except Exception as e:
            print(f"Error Deepseek: {e}")
            return []
