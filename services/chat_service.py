# import logging
# from typing import Dict, List, Any
# from fastapi import UploadFile
# from schemas import ChatMessage
# from services.stt_service import STTService
# from services.tts_service import TTSService
# from services.llm_service import LLMService

# logger = logging.getLogger(__name__)


# class ChatService:
#     """Service for managing chat sessions and coordinating STT, LLM, and TTS services"""
    
#     def __init__(self):
#         # In-memory chat store: session_id -> list of ChatMessage
#         self.chat_store: Dict[str, List[Dict[str, str]]] = {}
        
#         # Initialize services
#         self.stt_service = STTService()
#         self.tts_service = TTSService()
#         self.llm_service = LLMService()
        
#         logger.info("ChatService initialized successfully")

#     async def process_chat_interaction(self, session_id: str, audio_file: UploadFile) -> Dict[str, Any]:
#         """
#         Process a complete chat interaction: STT -> LLM -> TTS
        
#         Args:
#             session_id: Unique identifier for the chat session
#             audio_file: Uploaded audio file
            
#         Returns:
#             Dictionary containing transcription, LLM reply, audio URL, and any errors
#         """
#         try:
#             # Step 1: Read audio data
#             audio_data = await self._read_audio_data(audio_file)
#             if not audio_data["success"]:
#                 return self._create_fallback_response(
#                     "", 
#                     "I'm having trouble receiving your audio right now.",
#                     "read_failed", 
#                     audio_data["error"]
#                 )

#             # Step 2: Transcribe audio
#             transcript_result = await self.stt_service.transcribe_audio(audio_data["data"])
#             if not transcript_result["success"]:
#                 return self._create_fallback_response(
#                     "", 
#                     "I'm having trouble hearing you right now.",
#                     "stt_failed", 
#                     transcript_result["error"]
#                 )

#             user_text = transcript_result["text"]
#             logger.info(f"User said: {user_text}")

#             # Step 3: Manage conversation history
#             history = self._get_or_create_session_history(session_id)
#             history.append({"role": "user", "text": user_text})

#             # Step 4: Generate LLM response
#             llm_reply = self.llm_service.generate_response_with_history(history)
#             if not llm_reply:
#                 fallback_text = "I'm having trouble thinking right now."
#                 history.append({"role": "assistant", "text": fallback_text})
#                 return self._create_fallback_response(
#                     user_text, 
#                     fallback_text,
#                     "llm_failed", 
#                     "LLM service returned empty response"
#                 )

#             # Step 5: Add assistant response to history
#             history.append({"role": "assistant", "text": llm_reply})

#             # Step 6: Generate TTS audio
#             murf_audio_url = await self.tts_service.generate_speech(llm_reply, "en-US-ken")
#             if not murf_audio_url:
#                 logger.warning("TTS failed, but continuing with text response")

#             return {
#                 "transcription": user_text,
#                 "llm_reply": llm_reply,
#                 "murf_audio_url": murf_audio_url
#             }

#         except Exception as e:
#             logger.error(f"Error in chat interaction: {str(e)}")
#             return self._create_fallback_response(
#                 "", 
#                 "I'm having trouble connecting right now.",
#                 "unexpected_failure", 
#                 str(e)
#             )

#     async def _read_audio_data(self, audio_file: UploadFile) -> Dict[str, Any]:
#         """
#         Read audio data from uploaded file
        
#         Args:
#             audio_file: Uploaded audio file
            
#         Returns:
#             Dictionary with success status and audio data or error
#         """
#         try:
#             audio_data = await audio_file.read()
#             return {"success": True, "data": audio_data, "error": None}
#         except Exception as e:
#             logger.error(f"Error reading audio file: {str(e)}")
#             return {"success": False, "data": None, "error": str(e)}

#     def _get_or_create_session_history(self, session_id: str) -> List[Dict[str, str]]:
#         """
#         Get existing session history or create new one
        
#         Args:
#             session_id: Unique session identifier
            
#         Returns:
#             List of conversation messages
#         """
#         if session_id not in self.chat_store:
#             self.chat_store[session_id] = []
#             logger.info(f"Created new chat session: {session_id}")
        
#         return self.chat_store[session_id]

#     async def _create_fallback_response(
#         self, 
#         transcription: str, 
#         fallback_text: str, 
#         error_type: str, 
#         error_details: str
#     ) -> Dict[str, Any]:
#         """
#         Create a fallback response with TTS audio
        
#         Args:
#             transcription: User's transcribed text
#             fallback_text: Fallback message to display
#             error_type: Type of error that occurred
#             error_details: Detailed error message
            
#         Returns:
#             Dictionary with fallback response data
#         """
#         fallback_audio_url = await self.tts_service.generate_fallback_audio(fallback_text)
        
#         return {
#             "transcription": transcription,
#             "llm_reply": fallback_text,
#             "murf_audio_url": fallback_audio_url,
#             "error": error_type,
#             "details": error_details
#         }

#     def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
#         """
#         Get conversation history for a session
        
#         Args:
#             session_id: Unique session identifier
            
#         Returns:
#             List of conversation messages
#         """
#         return self.chat_store.get(session_id, [])

#     def clear_session_history(self, session_id: str) -> bool:
#         """
#         Clear conversation history for a session
        
#         Args:
#             session_id: Unique session identifier
            
#         Returns:
#             True if session existed and was cleared, False otherwise
#         """
#         if session_id in self.chat_store:
#             del self.chat_store[session_id]
#             logger.info(f"Cleared chat session: {session_id}")
#             return True
#         return False

#     def get_active_sessions(self) -> List[str]:
#         """
#         Get list of active session IDs
        
#         Returns:
#             List of active session IDs
#         """
#         return list(self.chat_store.keys())


import logging
from typing import Dict, List, Any
from fastapi import UploadFile
from schemas import ChatMessage
from services.stt_service import STTService
from services.tts_service import TTSService
from services.llm_service import LLMService
from debug_utils import log_audio_file_info, safe_log_text

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat sessions and coordinating STT, LLM, and TTS services"""
    
    def __init__(self):
        # In-memory chat store: session_id -> list of ChatMessage
        self.chat_store: Dict[str, List[Dict[str, str]]] = {}
        
        # Initialize services
        self.stt_service = STTService()
        self.tts_service = TTSService()
        self.llm_service = LLMService()
        
        logger.info("ChatService initialized successfully")

    async def process_chat_interaction(self, session_id: str, audio_file: UploadFile) -> Dict[str, Any]:
        """
        Process a complete chat interaction: STT -> LLM -> TTS
        
        Args:
            session_id: Unique identifier for the chat session
            audio_file: Uploaded audio file
            
        Returns:
            Dictionary containing transcription, LLM reply, audio URL, and any errors
        """
        try:
            # Step 1: Read audio data
            audio_data = await self._read_audio_data(audio_file)
            if not audio_data["success"]:
                return await self._create_fallback_response(
                    "", 
                    "I'm having trouble receiving your audio right now.",
                    "read_failed", 
                    audio_data["error"]
                )

            # Step 2: Transcribe audio
            transcript_result = await self.stt_service.transcribe_audio(audio_data["data"])
            if not transcript_result["success"]:
                return await self._create_fallback_response(
                    "", 
                    "I'm having trouble hearing you right now.",
                    "stt_failed", 
                    transcript_result["error"]
                )

            user_text = transcript_result["text"]
            logger.info(f"User said: {user_text}")

            # Step 3: Manage conversation history
            history = self._get_or_create_session_history(session_id)
            history.append({"role": "user", "text": user_text})

            # Step 4: Generate LLM response
            llm_reply = self.llm_service.generate_response_with_history(history)
            if not llm_reply:
                fallback_text = "I'm having trouble thinking right now."
                history.append({"role": "assistant", "text": fallback_text})
                return await self._create_fallback_response(
                    user_text, 
                    fallback_text,
                    "llm_failed", 
                    "LLM service returned empty response"
                )

            # Step 5: Add assistant response to history
            history.append({"role": "assistant", "text": llm_reply})

            # Step 6: Generate TTS audio
            murf_audio_url = await self.tts_service.generate_speech(llm_reply, "en-US-ken")
            if not murf_audio_url:
                logger.warning("TTS failed, but continuing with text response")

            return {
                "transcription": user_text,
                "llm_reply": llm_reply,
                "murf_audio_url": murf_audio_url
            }

        except Exception as e:
            logger.error(f"Error in chat interaction: {str(e)}")
            return await self._create_fallback_response(
                "", 
                "I'm having trouble connecting right now.",
                "unexpected_failure", 
                str(e)
            )

    async def _read_audio_data(self, audio_file: UploadFile) -> Dict[str, Any]:
        """
        Read audio data from uploaded file
        
        Args:
            audio_file: Uploaded audio file
            
        Returns:
            Dictionary with success status and audio data or error
        """
        try:
            audio_data = await audio_file.read()
            
            # Debug: Log audio file information
            file_info = log_audio_file_info(audio_data, audio_file.filename or "unknown")
            logger.info(f"Reading audio file: {safe_log_text(str(file_info))}")
            
            return {"success": True, "data": audio_data, "error": None}
        except Exception as e:
            logger.error(f"Error reading audio file: {str(e)}")
            return {"success": False, "data": None, "error": str(e)}

    def _get_or_create_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get existing session history or create new one
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            List of conversation messages
        """
        if session_id not in self.chat_store:
            self.chat_store[session_id] = []
            logger.info(f"Created new chat session: {session_id}")
        
        return self.chat_store[session_id]

    async def _create_fallback_response(
        self, 
        transcription: str, 
        fallback_text: str, 
        error_type: str, 
        error_details: str
    ) -> Dict[str, Any]:
        """
        Create a fallback response with TTS audio
        
        Args:
            transcription: User's transcribed text
            fallback_text: Fallback message to display
            error_type: Type of error that occurred
            error_details: Detailed error message
            
        Returns:
            Dictionary with fallback response data
        """
        fallback_audio_url = await self.tts_service.generate_fallback_audio(fallback_text)
        
        return {
            "transcription": transcription,
            "llm_reply": fallback_text,
            "murf_audio_url": fallback_audio_url,
            "error": error_type,
            "details": error_details
        }

    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            List of conversation messages
        """
        return self.chat_store.get(session_id, [])

    def clear_session_history(self, session_id: str) -> bool:
        """
        Clear conversation history for a session
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session existed and was cleared, False otherwise
        """
        if session_id in self.chat_store:
            del self.chat_store[session_id]
            logger.info(f"Cleared chat session: {session_id}")
            return True
        return False

    def get_active_sessions(self) -> List[str]:
        """
        Get list of active session IDs
        
        Returns:
            List of active session IDs
        """
        return list(self.chat_store.keys())