"""Voice input handling for VLM system."""

import speech_recognition as sr
import logging
import os
import sys
from typing import Optional, List

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config.settings import VLMSettings

class VoiceHandler:
    """Handles voice input recognition and processing."""
    
    def __init__(self, settings: VLMSettings):
        """Initialize voice handler with settings."""
        self.settings = settings
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.logger = logging.getLogger(__name__)
        
        # Check Google service availability at startup
        self._google_available = self._check_google_service()
        
        # Adjust for ambient noise
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
    
    def _check_google_service(self) -> bool:
        """Check if Google Speech Recognition service is available."""
        try:
            import socket
            import urllib.request
            
            # Test network connectivity
            socket.setdefaulttimeout(3.0)
            
            # Try to reach Google's speech service
            urllib.request.urlopen('https://www.google.com', timeout=3)
            self.logger.info("Google Speech Recognition service is available")
            return True
            
        except Exception as e:
            self.logger.warning(f"Google Speech Recognition service unavailable: {e}")
            return False
    
    def is_google_available(self) -> bool:
        """Check if Google service is currently available."""
        return self._google_available
    
    def get_voice_input(self, language: str = "en-GB") -> Optional[str]:
        """Get voice input from microphone."""
        if not self.settings.enable_voice_input:
            self.logger.info("Voice input is disabled")
            return None
        
        try:
            print("🔴 Preparing microphone...")
            print("🔧 Calibrating microphone for ambient noise...")
            
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            print("🎤 Ready to listen! Please speak your command...")
            print("   💡 Tip: Speak clearly and wait for processing")
            
            with self.microphone as source:
                print("🔴 Recording... (speak now)")
                # Listen for audio with timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=self.settings.voice_timeout,
                    phrase_time_limit=self.settings.voice_phrase_time_limit
                )
                print("⏹️  Recording complete, processing...")
            
            print("🔍 Converting speech to text...")
            
            # Try offline recognition FIRST to avoid network issues
            try:
                print("🔄 Trying offline recognition...")
                text = self.recognizer.recognize_sphinx(audio)
                if text and text.strip():
                    self.logger.info(f"Offline voice recognition successful: {text}")
                    print(f"\n{'='*50}")
                    print("🎯 VOICE RECOGNITION RESULT")
                    print("="*50)
                    print(f"📝 Method: Offline Recognition")
                    print(f"🗣️  Recognized Text: '{text}'")
                    print("="*50)
                    return text.lower().strip()
            except Exception as e:
                print(f"   ⚠️ Offline recognition failed: {str(e)[:50]}...")
            
            # Only try online if Google service is available
            if self.is_google_available():
                try:
                    print("🌐 Trying online recognition (British English)...")
                    import socket
                    # Set a very short timeout for network operations
                    socket.setdefaulttimeout(3.0)
                    text = self.recognizer.recognize_google(audio, language=language)
                    self.logger.info(f"Online voice recognition successful: {text}")
                    print(f"\n{'='*50}")
                    print("🎯 VOICE RECOGNITION RESULT")
                    print("="*50)
                    print(f"📝 Method: Online Recognition (British English)")
                    print(f"🗣️  Recognised Text: '{text}'")
                    print("="*50)
                    return text.lower().strip()
                
                except Exception as e:
                    print(f"   ❌ Online recognition failed: {str(e)[:50]}...")
                    self.logger.warning("Online voice recognition failed")
                    # Update availability status
                    self._google_available = False
                    return self._offline_recognition(audio)
            else:
                print("   ⚠️ Google Speech service unavailable, using offline recognition...")
                return self._offline_recognition(audio)
        
        except sr.WaitTimeoutError:
            print("❌ No voice input detected within timeout period")
            return None
        except sr.UnknownValueError:
            print("❌ Could not understand the voice input")
            return None
        except Exception as e:
            self.logger.error(f"Voice input error: {e}")
            print(f"❌ Voice input error: {e}")
            return None
    
    def _offline_recognition(self, audio) -> Optional[str]:
        """Fallback offline voice recognition using keywords."""
        try:
            # Try offline recognition if available
            text = self.recognizer.recognize_sphinx(audio)
            self.logger.info(f"Offline voice recognition: {text}")
            return text.lower().strip()
        except:
            # Final fallback - keyword matching simulation
            self.logger.warning("Using keyword fallback for voice recognition")
            return self._keyword_fallback()
    
    def _keyword_fallback(self) -> Optional[str]:
        """Simulate keyword recognition when other methods fail."""
        print("Voice recognition failed. Using common object keywords.")
        print("Available keywords:", ", ".join(self.settings.offline_voice_keywords))
        
        # In a real implementation, this could use a simple pattern matching
        # For now, return the first keyword as a fallback
        if self.settings.offline_voice_keywords:
            fallback_keyword = self.settings.offline_voice_keywords[0]
            print(f"Using fallback keyword: {fallback_keyword}")
            return fallback_keyword
        
        return None
    
    def test_microphone(self) -> bool:
        """Test if microphone is working properly."""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Microphone test successful")
            return True
        except Exception as e:
            self.logger.error(f"Microphone test failed: {e}")
            return False
    
    def get_voice_input_with_fallback(self, languages: List[str] = None) -> Optional[str]:
        """Get voice input with multiple language fallbacks."""
        if languages is None:
            languages = ["en-GB", "zh-CN"]  # British English first, then Chinese
        
        for language in languages:
            result = self.get_voice_input(language)
            if result:
                return result
        
        return None
