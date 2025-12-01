import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import aiofiles

from models.schemas import Conversation, Message, MessageRole, ConversationSource

class ChatGPTExtractor:
    """Extractor for ChatGPT JSON export format"""
    
    async def extract_from_file(self, file_path: str) -> List[Conversation]:
        """Extract conversations from a ChatGPT JSON file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
                
            conversations = []
            
            # Check if data is a list (multiple conversations) or dict (single conversation wrapper)
            items = data if isinstance(data, list) else [data]
            
            for item in items:
                if conversation := self._process_conversation(item):
                    conversations.append(conversation)
                    
            return conversations
            
        except Exception as e:
            print(f"Error extracting from ChatGPT file: {e}")
            return []

    def _process_conversation(self, data: Dict[str, Any]) -> Optional[Conversation]:
        """Process a single conversation object"""
        try:
            # Basic validation
            if 'mapping' not in data or 'title' not in data:
                return None
                
            messages = []
            mapping = data.get('mapping', {})
            
            # Sort messages by create_time if available, otherwise try to follow thread
            # For simplicity in this version, we'll collect all valid messages
            # In a real implementation, we'd follow the 'parent' pointers to reconstruct the tree
            
            for msg_id, node in mapping.items():
                if not node or 'message' not in node or not node['message']:
                    continue
                    
                msg_data = node['message']
                
                # Skip system messages or empty content
                if msg_data.get('author', {}).get('role') == 'system':
                    continue
                    
                if not msg_data.get('content', {}).get('parts'):
                    continue
                
                # Extract content
                parts = msg_data['content']['parts']
                text_content = ""
                
                for part in parts:
                    if isinstance(part, str):
                        text_content += part
                    elif isinstance(part, dict) and 'text' in part:
                        # Handle multimodal/image parts if text is present
                        text_content += part['text']
                
                if not text_content.strip():
                    continue
                
                # Determine role
                role_str = msg_data.get('author', {}).get('role', 'user')
                role = MessageRole.ASSISTANT if role_str == 'assistant' else MessageRole.USER
                
                # Get timestamp
                create_time = msg_data.get('create_time')
                timestamp = float(create_time) if create_time else datetime.now().timestamp()
                
                # Get model (for assistant messages)
                model = None
                if role == MessageRole.ASSISTANT:
                    metadata = msg_data.get('metadata', {})
                    model = metadata.get('model_slug') or 'gpt-unknown'
                
                messages.append(Message(
                    role=role,
                    content=text_content,
                    timestamp=timestamp,
                    model=model
                ))
            
            # Sort by timestamp to ensure chronological order
            messages.sort(key=lambda x: float(x.timestamp or 0.0))
            
            # Create metadata
            metadata = {
                "title": data.get('title', 'Untitled Chat'),
                "create_time": data.get('create_time'),
                "update_time": data.get('update_time'),
                "original_id": data.get('id')
            }
            
            # Use the ID from the file or generate one if missing (though ChatGPT exports usually have IDs)
            conv_id = data.get('id') or f"chatgpt_{int(datetime.now().timestamp())}"
            
            # Get extract timestamp (using create_time of conversation or current time)
            extracted_at = data.get('create_time') or datetime.now().timestamp()
            
            return Conversation(
                id=conv_id,
                source=ConversationSource.CHATGPT,
                extracted_at=float(extracted_at),
                messages=messages,
                metadata=metadata
            )
            
        except Exception as e:
            print(f"Error processing conversation: {e}")
            return None
