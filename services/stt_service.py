import os
import logging
import assemblyai as aai
from typing import Dict, Any
from schemas import TranscriptionResult

logger = logging.getLogger(__name__)


class STTService:
    """Service for handling Speech-to-Text operations using AssemblyAI"""
    
    def __init__(self):
        self.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not self.api_key:
            logger.error("ASSEMBLYAI_API_KEY not found in environment variables")
            raise ValueError("ASSEMBLYAI_API_KEY not configured")
        
        aai.settings.api_key = self.api_key
        self.transcriber = aai.Transcriber()
        logger.info("STTService initialized successfully")

    async def transcribe_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Transcribe audio data to text using AssemblyAI
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Dict containing success status, transcribed text, and optional error
        """
        try:
            logger.info("Starting audio transcription")
            
            # Handle potential encoding issues with audio data
            if isinstance(audio_data, str):
                try:
                    audio_data = audio_data.encode('utf-8')
                except Exception as encoding_error:
                    logger.error(f"Error encoding audio data: {encoding_error}")
                    return {
                        "success": False,
                        "error": f"Audio encoding error: {encoding_error}",
                        "text": None
                    }
            
            # Transcribe using AssemblyAI
            transcript = self.transcriber.transcribe(audio_data)
            
            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"Transcription failed: {transcript.error}")
                return {
                    "success": False,
                    "error": f"Transcription failed: {transcript.error}",
                    "text": None
                }
            
            transcribed_text = getattr(transcript, "text", "")
            if not transcribed_text:
                logger.warning("Transcription returned empty text")
                return {
                    "success": False,
                    "error": "Transcription returned empty text",
                    "text": None
                }
            
            logger.info(f"Transcription successful: {transcribed_text[:100]}...")
            return {
                "success": True,
                "text": transcribed_text,
                "confidence": getattr(transcript, "confidence", None),
                "error": None
            }
            
        except UnicodeDecodeError as decode_error:
            logger.error(f"Unicode decode error during transcription: {decode_error}")
            return {
                "success": False,
                "error": f"Audio format/encoding issue: {decode_error}",
                "text": None
            }
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": None

            }
