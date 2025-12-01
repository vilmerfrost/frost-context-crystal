from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ConversationSource(str, Enum):
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    PERPLEXITY = "perplexity"
    MOONSHOT = "moonshot"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"

class PipelineStage(str, Enum):
    INITIALIZING = "initializing"
    COMPRESSION = "compression"
    VERIFICATION = "verification"
    OPTIMIZATION = "optimization"
    COMPLETED = "completed"
    FAILED = "failed"


class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: Optional[float] = None
    model: Optional[str] = None

class Conversation(BaseModel):
    id: str
    source: ConversationSource
    extracted_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    messages: List[Message]
    metadata: Optional[Dict[str, Any]] = None

class ExtractionRequest(BaseModel):
    source: ConversationSource
    url: str
    manual_content: Optional[str] = None

class CompressionRequest(BaseModel):
    compression_ratio: float = Field(default=0.8, ge=0.1, le=0.95)
    user_continuation_prompt: Optional[str] = "Please continue from the previous context."
    preserve_code_blocks: bool = True
    preserve_technical_details: bool = True

class CompressionResult(BaseModel):
    compressed_content: str
    original_token_count: int
    compressed_token_count: int
    compression_ratio: float
    extracted_facts: List[Dict[str, Any]]
    processing_time: float

class VerificationResult(BaseModel):
    verified_content: str
    total_claims: int
    verified_claims: int
    grounding_score: float
    corrections: List[Dict[str, Any]]
    failed_verifications: List[Dict[str, Any]]

class PromptOutput(BaseModel):
    final_prompt: str
    structure_breakdown: Dict[str, str]
    estimated_tokens: int
    quality_metrics: Dict[str, float]
    cost_estimation: Dict[str, float]

class PipelineStatus(BaseModel):
    id: str
    conversation_id: str
    stage: PipelineStage
    progress: float = Field(ge=0, le=100)
    message: str
    result: Optional[PromptOutput] = None
    error: Optional[str] = None
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())

class APIKeys(BaseModel):
    deepseek_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    moonshot_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None

class QualityMetrics(BaseModel):
    compression_ratio: float
    information_density_ratio: float
    grounding_score: float
    estimated_cost_savings: float
    processing_time: float