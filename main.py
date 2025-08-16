
import os
import logging
from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from services.stt_service import STTService
from services.tts_service import TTSService
from services.llm_service import LLMService
from services.chat_service import ChatService
from schemas import TTSRequest, TTSResponse, QueryResponse, ChatResponse
from fastapi import WebSocket, WebSocketDisconnect

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="MURF Voice Agent API", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates (for HTML)
templates = Jinja2Templates(directory="templates")

# Initialize services
stt_service = STTService()
tts_service = TTSService()
llm_service = LLMService()
chat_service = ChatService()


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon_io/favicon.ico")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate-speech", response_model=TTSResponse)
async def generate_speech(request: TTSRequest):
    """
    Generate speech from text using Murf's TTS API
    
    Args:
        request: TTSRequest containing text and optional voice_id
        
    Returns:
        TTSResponse with audio URL or error message
    """
    try:
        logger.info(f"Generating speech for text: {request.text[:50]}...")
        audio_url = await tts_service.generate_speech(request.text, request.voice_id)
        
        if audio_url:
            return TTSResponse(
                success=True,
                audio_url=audio_url,
                message="Speech generated successfully!"
            )
        else:
            return TTSResponse(
                success=False,
                message="Failed to generate speech"
            )
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        return TTSResponse(
            success=False,
            message=f"Error: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "MURF Voice Agent"}


@app.get("/voices")
async def get_voices():
    """
    Get available voices from Murf API
    Note: Implement this if Murf provides a voices endpoint
    """
    return {
        "voices": [
            {"id": "en-US-ken", "name": "Ken (US English)", "language": "en-US"},
            {"id": "en-US-sarah", "name": "Sarah (US English)", "language": "en-US"},
            {"id": "en-GB-oliver", "name": "Oliver (UK English)", "language": "en-GB"}
        ]
    }


@app.post("/transcribe/file")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe uploaded audio file using AssemblyAI"""
    try:
        logger.info(f"Transcribing file: {file.filename}")
        audio_data = await file.read()
        
        transcript_result = await stt_service.transcribe_audio(audio_data)
        
        if transcript_result["success"]:
            return {
                "transcript": transcript_result["text"],
                "status": "completed",
                "confidence": transcript_result.get("confidence")
            }
        else:
            return JSONResponse(
                status_code=400,
                content={"error": transcript_result["error"]}
            )
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/llm/query", response_model=QueryResponse)
async def llm_query(file: UploadFile = File(...)):
    """
    Accepts an audio file, transcribes it with AssemblyAI,
    sends the transcript to Gemini to produce a reply,
    sends Gemini reply to Murf to generate audio,
    returns the Murf audio url to client.
    """
    try:
        logger.info("Processing LLM query from audio")
        
        # 1. Read uploaded audio bytes
        audio_data = await file.read()

        # 2. Transcribe with AssemblyAI
        transcript_result = await stt_service.transcribe_audio(audio_data)
        if not transcript_result["success"]:
            return JSONResponse(status_code=400, content={"error": "Transcription failed"})

        user_text = transcript_result["text"]
        logger.info(f"Transcribed text: {user_text}")

        # 3. Generate LLM reply
        llm_reply = await llm_service.generate_response(user_text)
        if not llm_reply:
            return JSONResponse(status_code=500, content={"error": "LLM returned empty response"})

        logger.info(f"LLM reply: {llm_reply[:100]}...")

        # 4. Generate audio response
        murf_audio_url = await tts_service.generate_speech(llm_reply, "en-US-ken")
        if not murf_audio_url:
            return JSONResponse(status_code=500, content={"error": "Failed to generate audio response"})

        return QueryResponse(
            transcription=user_text,
            llm_reply=llm_reply,
            murf_audio_url=murf_audio_url
        )

    except Exception as e:
        logger.error(f"Error in LLM query: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/agent/chat/{session_id}", response_model=ChatResponse)
async def agent_chat(session_id: str, file: UploadFile = File(...)):
    """
    Accepts audio file for a given session_id.
    Steps:
      - Transcribe audio (AssemblyAI)
      - Append user transcript to session history
      - Create prompt from history and call Gemini
      - Append assistant reply to session history
      - Send assistant reply to Murf TTS
      - Return transcription, assistant reply, and murf_audio_url
    """
    try:
        logger.info(f"Processing chat for session: {session_id}")
        
        # Process the chat interaction
        result = await chat_service.process_chat_interaction(session_id, file)
        
        return ChatResponse(
            transcription=result["transcription"],
            llm_reply=result["llm_reply"],
            murf_audio_url=result.get("murf_audio_url"),
            error=result.get("error"),
            details=result.get("details")
        )

    except Exception as e:
        logger.error(f"Error in agent chat: {str(e)}")
        fallback_text = "I'm having trouble connecting right now."
        
        # Generate fallback audio synchronously to avoid coroutine issues
        try:
            fallback_audio_url = await tts_service.generate_fallback_audio(fallback_text)
        except Exception as tts_error:
            logger.error(f"Fallback TTS also failed: {tts_error}")
            fallback_audio_url = None
        
        return ChatResponse(
            transcription="",
            llm_reply=fallback_text,
            murf_audio_url=fallback_audio_url,
            error="unexpected_failure",
            details=str(e)
        )
        
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("New WebSocket connection established")

    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received via WebSocket: {data}")

            # Echo the same message back
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")

# Main entrypoint for Uvicorn
if __name__ == "__main__":
    import uvicorn
    # Use only a single worker for in-memory state to work correctly

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)
