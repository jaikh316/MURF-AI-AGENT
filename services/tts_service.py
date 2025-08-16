import os
import logging
import httpx
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class TTSService:
    """Service for handling Text-to-Speech operations using Murf API"""
    
    def __init__(self):
        self.api_key = os.getenv("MURF_API_KEY")
        self.api_url = os.getenv("MURF_API_URL", "https://api.murf.ai/v1/speech/generate")
        
        if not self.api_key:
            logger.error("MURF_API_KEY not found in environment variables")
            raise ValueError("MURF_API_KEY not configured")
        
        logger.info("TTSService initialized successfully")

    async def generate_speech(self, text: str, voice_id: str = "en-US-ken") -> Optional[str]:
        """
        Generate speech from text using Murf's TTS API
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use for generation
            
        Returns:
            Audio URL if successful, None otherwise
        """
        try:
            logger.info(f"Generating speech for text: {text[:50]}...")
            
            payload = {
                "text": text,
                "voiceId": voice_id,
                "format": "mp3",
                "quality": "high"
            }
            
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.api_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    audio_url = result.get("audioFile") or result.get("url") or result.get("audio_url")
                    
                    if audio_url:
                        logger.info("Speech generation successful")
                        return audio_url
                    else:
                        logger.error("Audio URL not found in response")
                        return None
                else:
                    logger.error(f"Murf API error ({response.status_code}): {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Request timeout - Murf API took too long to respond")
            return None
        except Exception as e:
            logger.error(f"Error calling Murf API: {str(e)}")
            return None

    def generate_speech_sync(self, text: str, voice_id: str = "en-US-ken") -> Optional[str]:
        """
        Synchronous version of speech generation for fallback scenarios
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use for generation
            
        Returns:
            Audio URL if successful, None otherwise
        """
        try:
            logger.info(f"Generating fallback speech for text: {text[:50]}...")
            
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "text": text,
                "voiceId": voice_id,
                "format": "mp3"
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                audio_url = data.get("audioFile") or data.get("audio_url") or data.get("audioUrl")
                if audio_url:
                    logger.info("Fallback speech generation successful")
                    return audio_url
            else:
                logger.error(f"Fallback Murf returned: {response.status_code} {response.text}")
                
        except Exception as e:
            logger.error(f"Fallback TTS error: {e}")
            
        return None

    async def generate_fallback_audio(self, text: str) -> Optional[str]:
        """
        Generate fallback audio with error handling
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Audio URL if successful, None otherwise
        """
        try:
            return self.generate_speech_sync(text)
        except Exception as e:
            logger.error(f"Error generating fallback audio: {str(e)}")
            return None