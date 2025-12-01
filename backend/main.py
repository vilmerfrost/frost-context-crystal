from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from typing import Dict, Any, Optional, cast
import os
from dotenv import load_dotenv


from models.schemas import (
    Conversation, Message, ExtractionRequest, CompressionRequest,
    PipelineStatus, VerificationResult, PromptOutput, PipelineStage, ConversationSource
)
from db.sqlite import DatabaseManager
from extractors.chatgpt import ChatGPTExtractor
from extractors.claude import ClaudeExtractor
from extractors.perplexity import PerplexityExtractor
from extractors.moonshot import MoonshotExtractor
from extractors.deepseek import DeepseekExtractor
from pipeline.compressor import CompressionEngine
from pipeline.verifier import VerificationLayer
from pipeline.optimizer import PromptOptimizer


# Load environment variables
load_dotenv()


# Global state for pipeline tracking
pipeline_statuses: Dict[str, PipelineStatus] = {}
active_tasks: Dict[str, asyncio.Task] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Context Crystal Backend...")
    yield
    # Shutdown
    print("Shutting down Context Crystal Backend...")
    for task in active_tasks.values():
        task.cancel()
    await asyncio.gather(*active_tasks.values(), return_exceptions=True)


app = FastAPI(
    title="Context Crystal API",
    description="Backend for conversation compression and optimization",
    version="1.0.0",
    lifespan=lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database
db_manager = DatabaseManager()


# Initialize pipeline components
compression_engine = CompressionEngine()
verification_layer = VerificationLayer()
prompt_optimizer = PromptOptimizer()


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Context Crystal Backend API", "status": "running"}


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}


@app.post("/api/extract", response_model=Conversation)
async def extract_conversation(request: ExtractionRequest) -> Conversation:
    """Extract conversation from browser source"""
    try:
        extractor: Any = None
        if request.source == ConversationSource.CHATGPT:
            extractor = ChatGPTExtractor()
        elif request.source == ConversationSource.CLAUDE:
            extractor = ClaudeExtractor()
        elif request.source == ConversationSource.PERPLEXITY:
            extractor = PerplexityExtractor()
        elif request.source == ConversationSource.MOONSHOT:
            extractor = MoonshotExtractor()
        elif request.source == ConversationSource.DEEPSEEK:
            extractor = DeepseekExtractor()
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {request.source}")
        
        conversation = await extractor.extract_from_file(request.url) # OBS: Assuming logic is file-based for now based on previous context
        # Note: If your frontend sends a URL/File path, handle it here.
        # If extractor uses .extract() and not .extract_from_file(), change above.
        
        # Handle list return (since our extractors return List[Conversation])
        if isinstance(conversation, list):
            if not conversation:
                raise HTTPException(status_code=404, detail="No conversation found")
            conversation = conversation[0]

        conversation_id = await db_manager.save_conversation(conversation)
        conversation.id = conversation_id
        
        return conversation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.get("/api/conversations")
async def get_conversations(skip: int = 0, limit: int = 50) -> Dict[str, Any]:
    """Get paginated list of conversations"""
    try:
        conversations = await db_manager.get_conversations(skip, limit)
        return {"conversations": conversations, "total": len(conversations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> Conversation:
    """Get specific conversation by ID"""
    try:
        conversation = await db_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation: {str(e)}")


@app.post("/api/conversations/{conversation_id}/compress")
async def start_compression(conversation_id: str, request: CompressionRequest) -> Dict[str, str]:
    """Start compression pipeline for a conversation"""
    try:
        conversation = await db_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Create pipeline status
        pipeline_id = f"pipeline_{conversation_id}"
        pipeline_status = PipelineStatus(
            id=pipeline_id,
            conversation_id=conversation_id,
            stage=PipelineStage.INITIALIZING,
            progress=0,
            message="Starting compression pipeline..."
        )
        pipeline_statuses[pipeline_id] = pipeline_status
        
        # Start async pipeline task
        task = asyncio.create_task(run_compression_pipeline(pipeline_id, conversation, request))
        active_tasks[pipeline_id] = task
        
        return {
            "pipeline_id": pipeline_id,
            "status": "started",
            "message": "Compression pipeline started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start compression: {str(e)}")


@app.get("/api/pipeline/status/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str) -> PipelineStatus:
    """Get current status of a pipeline"""
    if pipeline_id not in pipeline_statuses:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return pipeline_statuses[pipeline_id]


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str) -> Dict[str, str]:
    """Delete a conversation"""
    try:
        success = await db_manager.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")


async def run_compression_pipeline(pipeline_id: str, conversation: Conversation, request: CompressionRequest) -> None:
    """Run the complete compression pipeline"""
    try:
        pipeline_status = pipeline_statuses[pipeline_id]
        
        # Stage 1: Compression
        pipeline_status.stage = PipelineStage.COMPRESSION
        pipeline_status.progress = 25
        pipeline_status.message = "Running semantic compression..."
        
        compressed_result = await compression_engine.compress(
            conversation,
            {"compression_ratio": request.compression_ratio}
        )
        
        # Stage 2: Verification
        pipeline_status.stage = PipelineStage.VERIFICATION
        pipeline_status.progress = 50
        pipeline_status.message = "Verifying compressed content..."
        
        # Handle object access safely (attribute vs dict)
        compressed_content = getattr(compressed_result, "compressed_content", "") if hasattr(compressed_result, "compressed_content") else compressed_result.get("compressed_content", "")

        verification_result = await verification_layer.verify(
            compressed_content,
            conversation.messages
        )
        
        # Stage 3: Optimization
        pipeline_status.stage = PipelineStage.OPTIMIZATION
        pipeline_status.progress = 75
        pipeline_status.message = "Optimizing prompt structure..."
        
        # Handle verification result safely
        verified_content = getattr(verification_result, "verified_content", "") if hasattr(verification_result, "verified_content") else verification_result.get("verified_content", compressed_content)

        optimized_prompt = await prompt_optimizer.optimize(
            verified_content, # Context
            verification_result # Pass full result as second arg
        )
        
        # Stage 4: Complete
        pipeline_status.stage = PipelineStage.COMPLETED
        pipeline_status.progress = 100
        pipeline_status.message = "Pipeline completed successfully"
        
        # Convert optimized_prompt to PromptOutput if it isn't already
        # For now, assume it matches schema or is adaptable
        pipeline_status.result = optimized_prompt
        
        # Save result to database
        await db_manager.save_pipeline_result(
            pipeline_id,
            conversation.id,
            compressed_result,
            verification_result,
            optimized_prompt
        )
        
    except Exception as e:
        pipeline_status.stage = PipelineStage.FAILED
        pipeline_status.message = f"Pipeline failed: {str(e)}"
        print(f"Pipeline {pipeline_id} failed: {e}")
        
    finally:
        # Clean up task
        if pipeline_id in active_tasks:
            del active_tasks[pipeline_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)