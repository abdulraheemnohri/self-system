#!/usr/bin/env python3
"""
Voice Input/Output Module for the Complete Self System

Provides:
- Speech-to-Text (STT) using SpeechRecognition
- Text-to-Speech (TTS) using pyttsx3
- Microphone input handling
- Audio playback
"""

import os
import time
from typing import Optional, Dict, Any


class VoiceManager:
    """
    Voice manager for speech recognition and text-to-speech.
    
    Supports:
    - Speech-to-Text via Google Speech Recognition
    - Text-to-Speech via pyttsx3
    - Microphone input
    - Audio configuration
    """
    
    def __init__(self, enabled: bool = False, stt_engine: str = "google", 
                 tts_engine: str = "pyttsx3", language: str = "en-US"):
        """
        Initialize the VoiceManager.
        
        Args:
            enabled: Whether voice features are enabled
            stt_engine: Speech-to-Text engine (google, sphinx, etc.)
            tts_engine: Text-to-Speech engine (pyttsx3, espeak, etc.)
            language: Language for speech recognition and synthesis
        """
        self.enabled = enabled
        self.stt_engine = stt_engine
        self.tts_engine = tts_engine
        self.language = language
        
        # Speech Recognition
        self.stt_available = False
        self.recognizer = None
        self.microphone = None
        self._init_stt()
        
        # Text-to-Speech
        self.tts_available = False
        self.engine = None
        self._init_tts()
    
    def _init_stt(self) -> None:
        """Initialize Speech Recognition."""
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self.stt_available = True
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
        except ImportError:
            self.stt_available = False
        except Exception as e:
            print(f"[Voice] STT initialization error: {e}")
            self.stt_available = False
    
    def _init_tts(self) -> None:
        """Initialize Text-to-Speech."""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.tts_available = True
            
            # Set properties
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 0.9)
            
            # Try to set voice by language
            try:
                voices = self.engine.getProperty('voices')
                for voice in voices:
                    if self.language.lower() in voice.id.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            except Exception:
                pass
                
        except ImportError:
            self.tts_available = False
        except Exception as e:
            print(f"[Voice] TTS initialization error: {e}")
            self.tts_available = False
    
    def is_enabled(self) -> bool:
        """Check if voice features are enabled."""
        return self.enabled
    
    def enable(self) -> None:
        """Enable voice features."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable voice features."""
        self.enabled = False
    
    def speak(self, text: str, rate: Optional[int] = None, 
              volume: Optional[float] = None) -> Dict[str, Any]:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            Dictionary with success status
        """
        if not self.enabled or not self.tts_available:
            return {
                "success": False,
                "error": "Voice output disabled or TTS unavailable",
                "message": "Install pyttsx3 to enable text-to-speech"
            }
        
        try:
            if rate is not None:
                self.engine.setProperty('rate', rate)
            if volume is not None:
                self.engine.setProperty('volume', volume)
            
            self.engine.say(str(text))
            self.engine.runAndWait()
            
            return {"success": True, "message": f"Spoke: {text[:50]}..."}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def listen(self, timeout: float = 5.0, phrase_time_limit: float = 15.0,
               language: Optional[str] = None) -> Dict[str, Any]:
        """
        Listen to microphone input and convert to text.
        
        Args:
            timeout: Seconds to wait for speech
            phrase_time_limit: Maximum seconds for a phrase
            language: Language for recognition (overrides default)
            
        Returns:
            Dictionary with recognized text or error
        """
        if not self.enabled or not self.stt_available:
            return {
                "success": False,
                "error": "Voice input disabled or STT unavailable",
                "text": "",
                "message": "Install SpeechRecognition and pyaudio to enable speech-to-text"
            }
        
        lang = language or self.language
        
        try:
            with self.microphone as source:
                print("[Voice] Listening... (Press Ctrl+C to stop)")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            print("[Voice] Processing...")
            
            # Use the specified engine
            if self.stt_engine == "google":
                text = self.recognizer.recognize_google(audio, language=lang)
            elif self.stt_engine == "sphinx":
                text = self.recognizer.recognize_sphinx(audio, language=lang)
            elif self.stt_engine == "wit":
                # Requires Wit.ai API key
                text = self.recognizer.recognize_wit(audio, key=None, language=lang)
            elif self.stt_engine == "ibm":
                # Requires IBM Watson credentials
                text = self.recognizer.recognize_ibm(audio, username=None, password=None, language=lang)
            else:
                text = self.recognizer.recognize_google(audio, language=lang)
            
            return {"success": True, "text": text, "language": lang}
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle common errors
            if "timeout" in error_msg.lower():
                return {"success": False, "error": "No speech detected (timeout)", "text": ""}
            elif "audio" in error_msg.lower():
                return {"success": False, "error": "Microphone access error", "text": ""}
            elif "api" in error_msg.lower():
                return {"success": False, "error": "API error (check internet connection)", "text": ""}
            else:
                return {"success": False, "error": error_msg, "text": ""}
    
    def listen_continuous(self, callback: callable, timeout: float = 1.0,
                         phrase_time_limit: float = 5.0,
                         language: Optional[str] = None) -> None:
        """
        Listen continuously and call callback with recognized text.
        
        Args:
            callback: Function to call with recognized text
            timeout: Seconds to wait between phrases
            phrase_time_limit: Maximum seconds for a phrase
            language: Language for recognition
        """
        if not self.enabled or not self.stt_available:
            print("[Voice] Continuous listening disabled or STT unavailable")
            return
        
        lang = language or self.language
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("[Voice] Continuous listening started... (Press Ctrl+C to stop)")
                
                while True:
                    try:
                        audio = self.recognizer.listen(
                            source,
                            timeout=timeout,
                            phrase_time_limit=phrase_time_limit
                        )
                        
                        if self.stt_engine == "google":
                            text = self.recognizer.recognize_google(audio, language=lang)
                        else:
                            text = self.recognizer.recognize_google(audio, language=lang)
                        
                        callback(text)
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "timeout" not in error_msg.lower():
                            print(f"[Voice] Error: {error_msg}")
                            break
                            
        except KeyboardInterrupt:
            print("[Voice] Continuous listening stopped")
        except Exception as e:
            print(f"[Voice] Continuous listening error: {e}")
    
    def save_to_file(self, text: str, filename: str = "speech.wav") -> Dict[str, Any]:
        """
        Save text as speech to a WAV file.
        
        Args:
            text: Text to convert to speech
            filename: Output filename
            
        Returns:
            Dictionary with success status
        """
        if not self.enabled or not self.tts_available:
            return {
                "success": False,
                "error": "Voice disabled or TTS unavailable"
            }
        
        try:
            self.engine.save_to_file(str(text), filename)
            self.engine.runAndWait()
            
            return {"success": True, "path": filename, "message": "Speech saved to file"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_available_voices(self) -> Dict[str, Any]:
        """
        Get list of available voices for TTS.
        
        Returns:
            Dictionary with list of voices or error
        """
        if not self.tts_available:
            return {
                "success": False,
                "error": "TTS unavailable",
                "voices": []
            }
        
        try:
            voices = self.engine.getProperty('voices')
            voice_list = []
            
            for voice in voices:
                voice_list.append({
                    "id": voice.id,
                    "name": voice.name,
                    "languages": voice.languages,
                    "gender": getattr(voice, 'gender', 'unknown')
                })
            
            return {"success": True, "voices": voice_list, "count": len(voice_list)}
        except Exception as e:
            return {"success": False, "error": str(e), "voices": []}
    
    def set_voice(self, voice_id: str) -> Dict[str, Any]:
        """
        Set the voice for TTS.
        
        Args:
            voice_id: ID of the voice to use
            
        Returns:
            Dictionary with success status
        """
        if not self.tts_available:
            return {"success": False, "error": "TTS unavailable"}
        
        try:
            self.engine.setProperty('voice', voice_id)
            return {"success": True, "message": f"Voice set to: {voice_id}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_rate(self, rate: int) -> Dict[str, Any]:
        """
        Set the speech rate.
        
        Args:
            rate: Words per minute
            
        Returns:
            Dictionary with success status
        """
        if not self.tts_available:
            return {"success": False, "error": "TTS unavailable"}
        
        try:
            self.engine.setProperty('rate', rate)
            return {"success": True, "message": f"Speech rate set to: {rate} WPM"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_volume(self, volume: float) -> Dict[str, Any]:
        """
        Set the speech volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            Dictionary with success status
        """
        if not self.tts_available:
            return {"success": False, "error": "TTS unavailable"}
        
        try:
            self.engine.setProperty('volume', volume)
            return {"success": True, "message": f"Volume set to: {volume}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stop(self) -> None:
        """Stop any ongoing speech."""
        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.stop()


def create_voice_manager(enabled: bool = False, stt_engine: str = "google",
                        tts_engine: str = "pyttsx3", language: str = "en-US") -> VoiceManager:
    """
    Factory function to create a VoiceManager instance.
    
    Args:
        enabled: Whether voice features are enabled
        stt_engine: Speech-to-Text engine
        tts_engine: Text-to-Speech engine
        language: Language for speech
        
    Returns:
        VoiceManager instance
    """
    return VoiceManager(
        enabled=enabled,
        stt_engine=stt_engine,
        tts_engine=tts_engine,
        language=language
    )
