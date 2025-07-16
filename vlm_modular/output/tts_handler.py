"""Text-to-speech handler for VLM system."""

import subprocess
import logging
import platform
import os
import sys
from typing import Optional

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config.settings import VLMSettings

class TTSHandler:
    """Handles text-to-speech output for the VLM system."""
    
    def __init__(self, settings: VLMSettings):
        """Initialize TTS handler with settings."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.system = platform.system()
        
        # Check TTS availability
        self.tts_available = self._check_tts_availability()
    
    def _check_tts_availability(self) -> bool:
        """Check if TTS is available on the system."""
        if not self.settings.enable_tts:
            return False
        
        try:
            if self.system == "Darwin":  # macOS
                # Check if 'say' command is available
                result = subprocess.run(['which', 'say'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                return result.returncode == 0
            elif self.system == "Linux":
                # Check for espeak or festival
                for tts_cmd in ['espeak', 'festival', 'spd-say']:
                    result = subprocess.run(['which', tts_cmd], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=5)
                    if result.returncode == 0:
                        return True
                return False
            elif self.system == "Windows":
                # Windows has built-in TTS
                return True
            else:
                self.logger.warning(f"TTS not supported on {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"Error checking TTS availability: {e}")
            return False
    
    def speak(self, text: str, voice: Optional[str] = None) -> bool:
        """Convert text to speech."""
        if not self.tts_available:
            self.logger.info("TTS not available or disabled")
            return False
        
        if not text or not text.strip():
            self.logger.warning("Empty text provided to TTS")
            return False
        
        try:
            # Clean text for TTS
            clean_text = self._clean_text_for_tts(text)
            
            if self.system == "Darwin":  # macOS
                return self._speak_macos(clean_text, voice)
            elif self.system == "Linux":
                return self._speak_linux(clean_text, voice)
            elif self.system == "Windows":
                return self._speak_windows(clean_text, voice)
            else:
                self.logger.error(f"TTS not implemented for {self.system}")
                return False
                
        except Exception as e:
            self.logger.error(f"TTS error: {e}")
            return False
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for better TTS pronunciation."""
        # Remove special characters that might confuse TTS
        import re
        
        # Replace common technical terms with pronounceable versions
        replacements = {
            'VLM': 'vision language model',
            'API': 'A P I',
            'bbox': 'bounding box',
            'coords': 'coordinates',
            'conf': 'confidence',
            'avg': 'average',
            'max': 'maximum',
            'min': 'minimum'
        }
        
        clean_text = text
        for term, replacement in replacements.items():
            clean_text = re.sub(rf'\b{term}\b', replacement, clean_text, flags=re.IGNORECASE)
        
        # Remove excessive punctuation
        clean_text = re.sub(r'[.]{2,}', '.', clean_text)
        clean_text = re.sub(r'[!]{2,}', '!', clean_text)
        clean_text = re.sub(r'[?]{2,}', '?', clean_text)
        
        # Limit length to prevent very long TTS
        if len(clean_text) > 500:
            sentences = clean_text.split('.')
            clean_text = '. '.join(sentences[:3]) + '.'
        
        return clean_text.strip()
    
    def _speak_macos(self, text: str, voice: Optional[str] = None) -> bool:
        """Use macOS 'say' command for TTS."""
        try:
            cmd = ['say']
            
            # Add voice if specified
            if voice:
                cmd.extend(['-v', voice])
            
            cmd.append(text)
            
            # Execute with timeout
            result = subprocess.run(
                cmd,
                timeout=self.settings.tts_timeout,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("macOS TTS successful")
                return True
            else:
                self.logger.error(f"macOS TTS failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.warning("macOS TTS timeout")
            return False
        except Exception as e:
            self.logger.error(f"macOS TTS error: {e}")
            return False
    
    def _speak_linux(self, text: str, voice: Optional[str] = None) -> bool:
        """Use Linux TTS systems."""
        # Try different TTS systems in order of preference
        tts_systems = [
            (['espeak', text], 'espeak'),
            (['spd-say', text], 'speech-dispatcher'),
            (['festival', '--tts'], 'festival')
        ]
        
        for cmd, system_name in tts_systems:
            try:
                if system_name == 'festival':
                    # Festival reads from stdin
                    result = subprocess.run(
                        cmd,
                        input=text,
                        timeout=self.settings.tts_timeout,
                        capture_output=True,
                        text=True
                    )
                else:
                    result = subprocess.run(
                        cmd,
                        timeout=self.settings.tts_timeout,
                        capture_output=True,
                        text=True
                    )
                
                if result.returncode == 0:
                    self.logger.info(f"Linux TTS successful ({system_name})")
                    return True
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
            except Exception as e:
                self.logger.warning(f"Linux TTS error with {system_name}: {e}")
                continue
        
        self.logger.error("All Linux TTS systems failed")
        return False
    
    def _speak_windows(self, text: str, voice: Optional[str] = None) -> bool:
        """Use Windows TTS via PowerShell."""
        try:
            # Use PowerShell SAPI for TTS
            ps_script = f"""
            Add-Type -AssemblyName System.Speech
            $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
            $speak.Speak('{text.replace("'", "''")}')
            """
            
            cmd = ['powershell', '-Command', ps_script]
            
            result = subprocess.run(
                cmd,
                timeout=self.settings.tts_timeout,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("Windows TTS successful")
                return True
            else:
                self.logger.error(f"Windows TTS failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.warning("Windows TTS timeout")
            return False
        except Exception as e:
            self.logger.error(f"Windows TTS error: {e}")
            return False
    
    def get_available_voices(self) -> list:
        """Get list of available TTS voices."""
        voices = []
        
        try:
            if self.system == "Darwin":  # macOS
                result = subprocess.run(['say', '-v', '?'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            voice_name = line.split()[0]
                            voices.append(voice_name)
            
            elif self.system == "Linux":
                # espeak voices
                try:
                    result = subprocess.run(['espeak', '--voices'], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=10)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n')[1:]:  # Skip header
                            if line.strip():
                                parts = line.split()
                                if len(parts) > 1:
                                    voices.append(parts[1])
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"Error getting voices: {e}")
        
        return voices
    
    def test_tts(self) -> bool:
        """Test TTS functionality."""
        test_text = "TTS test successful"
        return self.speak(test_text)
    
    def speak_detection_result(self, objects_found: int, object_name: str) -> bool:
        """Speak detection result in a standardized way."""
        if objects_found == 0:
            text = f"No {object_name} found in the image"
        elif objects_found == 1:
            text = f"Found one {object_name} in the image"
        else:
            text = f"Found {objects_found} {object_name}s in the image"
        
        return self.speak(text)
    
    def is_available(self) -> bool:
        """Check if TTS is available and enabled."""
        return self.tts_available and self.settings.enable_tts
