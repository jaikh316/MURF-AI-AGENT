from pydantic import BaseModel
from typing import Optional


class TTSRequest(BaseModel):
    text: str
    voice_id: str = "en-US-ken"  # Default voice


class TTSResponse(BaseModel):
    success: bool
    audio_url: Optional[str] = None
    message: Optional[str] = None


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    transcription: str
    llm_reply: str
    murf_audio_url: Optional[str] = None


class ChatResponse(BaseModel):
    transcription: str
    llm_reply: str
    murf_audio_url: Optional[str] = None
    error: Optional[str] = None
    details: Optional[str] = None


class TranscriptionResult(BaseModel):
    success: bool
    text: Optional[str] = None
    error: Optional[str] = None
    confidence: Optional[float] = None


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    text: str