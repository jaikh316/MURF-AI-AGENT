import os
import logging
import requests
import google.generativeai as genai
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class LLMService:
    """Service for handling Large Language Model operations using Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY not configured")
        
        # Configure Gemini SDK
        genai.configure(api_key=self.api_key)
        self.model_name = "gemini-2.5-pro"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        logger.info("LLMService initialized successfully")

    async def generate_response(self, text: str) -> Optional[str]:
        """
        Generate response from text using Gemini API
        
        Args:
            text: Input text to generate response for
            
        Returns:
            Generated response text or None if failed
        """
        try:
            logger.info(f"Generating LLM response for: {text[:100]}...")
            
            payload = {
                "contents": [{"parts": [{"text": text}]}]
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.text}")
                return None

            data = response.json()
            llm_reply = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            
            if not llm_reply:
                logger.error("Gemini returned empty response")
                return None
            
            logger.info(f"LLM response generated: {llm_reply[:100]}...")
            return llm_reply
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return None

    def generate_response_with_history(self, history: List[Dict[str, str]]) -> Optional[str]:
        """
        Generate response using conversation history
        
        Args:
            history: List of conversation messages with 'role' and 'text' keys
            
        Returns:
            Generated response text or None if failed
        """
        try:
            logger.info("Generating LLM response with conversation history")
            
            # Build prompt from history
            prompt = self._build_prompt_from_history(history)
            
            model = genai.GenerativeModel(self.model_name)
            gen_response = model.generate_content(prompt)
            
            llm_reply = getattr(gen_response, "text", None)
            if not llm_reply:
                # Fallback to dictionary access
                response_dict = gen_response.to_dict()
                llm_reply = (
                    response_dict.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
            
            if not llm_reply:
                logger.error("Gemini returned empty response with history")
                return None
            
            logger.info(f"LLM response with history generated: {llm_reply[:100]}...")
            return llm_reply
            
        except Exception as e:
            logger.error(f"Error generating LLM response with history: {str(e)}")
            return None

    def _build_prompt_from_history(self, history: List[Dict[str, str]]) -> str:
        """
        Build prompt from conversation history
        
        Args:
            history: List of conversation messages
            
        Returns:
            Formatted prompt string
        """
        lines = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['text']}")
        
        # Ask assistant to reply next
        lines.append("Assistant:")
        return "\n".join(lines)