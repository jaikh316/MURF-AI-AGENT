import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def log_audio_file_info(file_data: bytes, filename: str = "unknown") -> Dict[str, Any]:
    """
    Log information about uploaded audio file for debugging
    
    Args:
        file_data: Audio file bytes
        filename: Original filename
        
    Returns:
        Dict with file information
    """
    try:
        info = {
            "filename": filename,
            "size_bytes": len(file_data),
            "first_10_bytes": file_data[:10].hex() if len(file_data) >= 10 else "N/A",
            "encoding_check": "passed"
        }
        
        # Try to detect common audio formats by header
        if file_data.startswith(b'RIFF'):
            info["format"] = "WAV"
        elif file_data.startswith(b'\xff\xfb') or file_data.startswith(b'\xff\xf3') or file_data.startswith(b'\xff\xf2'):
            info["format"] = "MP3"
        elif file_data.startswith(b'OggS'):
            info["format"] = "OGG"
        elif file_data.startswith(b'fLaC'):
            info["format"] = "FLAC"
        else:
            info["format"] = "unknown"
        
        # Check for potential encoding issues
        try:
            # This will fail if the data contains non-ASCII bytes (which audio should)
            file_data.decode('ascii')
            info["encoding_check"] = "warning - data looks like text, not binary audio"
        except UnicodeDecodeError:
            info["encoding_check"] = "passed - binary data detected"
        
        logger.info(f"Audio file info: {info}")
        return info
        
    except Exception as e:
        logger.error(f"Error analyzing audio file: {e}")
        return {"error": str(e)}


def safe_log_text(text: str, max_length: int = 100) -> str:
    """
    Safely log text with length limit and encoding handling
    
    Args:
        text: Text to log
        max_length: Maximum length to display
        
    Returns:
        Safe text for logging
    """
    try:
        if not text:
            return "empty"
        
        # Truncate if too long
        if len(text) > max_length:
            return f"{text[:max_length]}... (truncated from {len(text)} chars)"
        
        return text
        
    except Exception as e:
        return f"<error logging text: {e}>"