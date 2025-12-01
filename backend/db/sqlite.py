import sqlite3
import aiosqlite
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from models.schemas import Conversation, Message, ConversationSource, MessageRole

class DatabaseManager:
    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with required tables"""
        init_script = """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            extracted_at REAL NOT NULL,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp REAL,
            model TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS pipeline_results (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            compressed_content TEXT NOT NULL,
            verification_result TEXT NOT NULL,
            optimized_prompt TEXT NOT NULL,
            metrics TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS api_keys (
            service TEXT PRIMARY KEY,
            api_key TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_conversations_source ON conversations(source);
        CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(extracted_at);
        CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(init_script)
            conn.commit()

    async def save_conversation(self, conversation: Conversation) -> str:
        """Save conversation to database and return ID"""
        async with aiosqlite.connect(self.db_path) as db:
            # Insert conversation
            await db.execute(
                "INSERT INTO conversations (id, source, extracted_at, metadata) VALUES (?, ?, ?, ?)",
                (
                    conversation.id,
                    conversation.source.value,
                    conversation.extracted_at,
                    json.dumps(conversation.metadata) if conversation.metadata else None
                )
            )

            # Insert messages
            message_data = [
                (
                    conversation.id,
                    message.role.value,
                    message.content,
                    message.timestamp,
                    message.model
                )
                for message in conversation.messages
            ]

            await db.executemany(
                "INSERT INTO messages (conversation_id, role, content, timestamp, model) VALUES (?, ?, ?, ?, ?)",
                message_data
            )

            await db.commit()
            return conversation.id

    async def get_conversations(self, skip: int = 0, limit: int = 50) -> List[Conversation]:
        """Get paginated list of conversations"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM conversations ORDER BY extracted_at DESC LIMIT ? OFFSET ?",
                (limit, skip)
            )
            rows = await cursor.fetchall()
            
            conversations = []
            for row in rows:
                conversation = await self._build_conversation_from_row(db, row)
                if conversation:
                    conversations.append(conversation)
            
            return conversations

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get specific conversation by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return await self._build_conversation_from_row(db, row)

    async def _build_conversation_from_row(self, db: aiosqlite.Connection, row) -> Optional[Conversation]:
        """Build Conversation object from database row"""
        try:
            # Get messages for this conversation
            cursor = await db.execute(
                "SELECT role, content, timestamp, model FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
                (row['id'],)
            )
            message_rows = await cursor.fetchall()
            
            messages = []
            for msg_row in message_rows:
                messages.append(Message(
                    role=MessageRole(msg_row['role']),
                    content=msg_row['content'],
                    timestamp=msg_row['timestamp'],
                    model=msg_row['model']
                ))
            
            metadata = json.loads(row['metadata']) if row['metadata'] else None
            
            return Conversation(
                id=row['id'],
                source=ConversationSource(row['source']),
                extracted_at=row['extracted_at'],
                messages=messages,
                metadata=metadata
            )
        except Exception as e:
            print(f"Error building conversation from row: {e}")
            return None

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and its messages"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def save_pipeline_result(self, pipeline_id: str, conversation_id: str,
                                 compressed_result: Any, verification_result: Any,
                                 optimized_prompt: Any) -> bool:
        """Save pipeline results to database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                metrics = {
                    "compression_ratio": getattr(compressed_result, 'compression_ratio', 0),
                    "grounding_score": getattr(verification_result, 'grounding_score', 0),
                    "original_tokens": getattr(compressed_result, 'original_token_count', 0),
                    "compressed_tokens": getattr(compressed_result, 'compressed_token_count', 0)
                }
                
                await db.execute(
                    """INSERT INTO pipeline_results 
                    (id, conversation_id, compressed_content, verification_result, optimized_prompt, metrics)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        pipeline_id,
                        conversation_id,
                        json.dumps(compressed_result.dict() if hasattr(compressed_result, "dict") else compressed_result),
                        json.dumps(verification_result.dict() if hasattr(verification_result, "dict") else verification_result),
                        json.dumps(optimized_prompt.dict() if hasattr(optimized_prompt, "dict") else optimized_prompt),
                        json.dumps(metrics)
                    )
                )
                await db.commit()
                return True
        except Exception as e:
            print(f"Error saving pipeline result: {e}")
            return False
