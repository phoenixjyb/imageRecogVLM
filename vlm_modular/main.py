"""Main application file for the modular VLM Object Recognition System."""

import os
import sys
import logging
from typing import Optional

# Add the current directory to the Python path for proper imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Now import with absolute imports
from config.settings import VLMSettings
from config.api_keys import APIKeys
from input.voice_handler import VoiceHandler
from input.text_processor import TextProcessor
from vlm.factory import VLMFactory
from image.processor import ImageProcessor
from image.annotator import ImageAnnotator
from image.coordinate_parser import CoordinateParser
from output.response_generator import ResponseGenerator
from output.tts_handler import TTSHandler

class VLMObjectRecognition:
    """Main application class for VLM Object Recognition System."""
    
    def __init__(self):
        """Initialize the VLM Object Recognition System."""
        # Load configuration
        self.settings = VLMSettings.load_from_env()
        self.api_keys = APIKeys()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.voice_handler = VoiceHandler(self.settings)
        self.text_processor = TextProcessor(self.settings)
        self.vlm_factory = VLMFactory(self.api_keys, self.settings)
        self.image_processor = ImageProcessor(self.settings)
        self.image_annotator = ImageAnnotator(self.settings)
        self.coordinate_parser = CoordinateParser()
        self.response_generator = ResponseGenerator(self.settings)
        self.tts_handler = TTSHandler(self.settings)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("VLM Object Recognition System initialized")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        level = logging.DEBUG if self.settings.enable_debug_logging else logging.INFO
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('vlm_system.log')
            ]
        )
    
    def run_object_detection(self, image_path: str, query: Optional[str] = None, 
                           provider: Optional[str] = None) -> dict:
        """Run object detection on an image."""
        try:
            # Get query from user if not provided
            if not query:
                query = self._get_user_query()
            
            if not query:
                return {'success': False, 'error': 'No query provided'}
            
            # Process the query
            processed_query = self.text_processor.process_user_query(query)
            object_name = self.text_processor.extract_object_name(processed_query)
            
            # Load and prepare image
            image_result = self.image_processor.load_and_prepare_image(image_path)
            if not image_result:
                return {'success': False, 'error': 'Failed to load image'}
            
            # Unpack the result safely
            try:
                image, base64_data = image_result
            except (ValueError, TypeError) as e:
                self.logger.error(f"Failed to unpack image result: {e}")
                return {'success': False, 'error': 'Invalid image processing result'}
            
            # Get VLM provider
            if not provider:
                provider = self.settings.default_vlm_provider
            
            vlm_client = self.vlm_factory.create_client(provider)
            
            # Create optimized prompt using the extracted object name
            prompt = self.text_processor.create_vlm_prompt(object_name, provider)
            
            # Query VLM
            self.logger.info(f"Querying {provider} with prompt: {prompt[:100]}...")
            vlm_response = vlm_client.query_image(base64_data, prompt)
            
            if not vlm_response.get('success', False):
                error_msg = vlm_response.get('error', 'VLM query failed')
                return {'success': False, 'error': error_msg}
            
            # Parse coordinates
            self.logger.info("Parsing VLM response...")
            objects = vlm_client.parse_response(vlm_response)
            self.logger.info(f"VLM client parsed {len(objects)} objects")
            
            # Additional parsing with coordinate parser
            if self.settings.log_vlm_responses and 'response' in vlm_response:
                self.logger.info("Additional coordinate parsing...")
                response_text = str(vlm_response['response'])
                additional_objects = self.coordinate_parser.parse_coordinates(
                    response_text, 
                    self.settings.image_output_width, 
                    self.settings.image_output_height
                )
                
                # Merge objects (remove duplicates)
                objects.extend(additional_objects)
                objects = self._remove_duplicate_objects(objects)
                self.logger.info(f"After merging: {len(objects)} objects")
            
            # Generate response
            self.logger.info("Generating response...")
            response_text = self.response_generator.generate_response(
                objects, object_name, provider, processed_query
            )
            
            # Speak response if TTS is enabled
            if self.tts_handler.is_available():
                self.logger.info("Speaking response...")
                self.tts_handler.speak(response_text)
            
            # Annotate image
            self.logger.info("Annotating image...")
            annotated_image = self.image_annotator.annotate_objects(
                image, objects, object_name
            )
            
            # Save annotated image
            self.logger.info("Saving annotated image...")
            output_path = self._generate_output_path(image_path, object_name)
            self.image_processor.save_image(annotated_image, output_path)
            
            return {
                'success': True,
                'objects_found': len(objects),
                'objects': objects,
                'response_text': response_text,
                'annotated_image_path': output_path,
                'provider': provider,
                'query': processed_query,
                'object_name': object_name
            }
            
        except Exception as e:
            self.logger.error(f"Error in object detection: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_user_query(self) -> Optional[str]:
        """Get query from user via voice or text input with user choice."""
        print("\n🎤 Input Mode Selection")
        print("=" * 50)
        print("1. 🎙️  Voice Input")
        print("   - Speak your command")
        print("   - Automatically converted to text")
        print("   - Supports English and Chinese")
        print("")
        print("2. ⌨️  Text Input") 
        print("   - Type your command")
        print("   - Current default mode")
        print("   - Supports English and Chinese")
        print("=" * 50)
        
        while True:
            try:
                choice = input("Choose input mode (1 for Voice, 2 for Text): ").strip()
                
                if choice == "1":
                    if not self.settings.enable_voice_input:
                        print("❌ Voice input is disabled. Using text input instead.")
                        choice = "2"
                    else:
                        print("\n🎙️ Initiating voice input...")
                        try:
                            voice_query = self.voice_handler.get_voice_input_with_fallback()
                            if voice_query:
                                print("\n" + "🔥"*60)
                                print("✅ FINAL VOICE COMMAND CAPTURED")
                                print("🔥"*60)
                                print(f"📢 Your Command: '{voice_query}'")
                                print("🔥"*60)
                                return voice_query
                            else:
                                print("❌ Voice input failed. Falling back to text input...")
                                choice = "2"
                        except Exception as e:
                            print(f"❌ Voice input failed: {e}")
                            print("🔄 Falling back to text input...")
                            choice = "2"
                
                if choice == "2":
                    print("\n⌨️  Text input mode selected")
                    text_query = input("💬 Enter your command: ").strip()
                    if text_query:
                        print("\n" + "📝"*60)
                        print("✅ TEXT COMMAND ENTERED")
                        print("📝"*60)
                        print(f"⌨️  Your Command: '{text_query}'")
                        print("📝"*60)
                        return text_query
                    else:
                        print("❌ No command entered. Please try again.")
                        continue
                
                if choice not in ["1", "2"]:
                    print("❌ Invalid choice. Please enter 1 or 2.")
                    continue
                    
            except KeyboardInterrupt:
                return None
    
    def _remove_duplicate_objects(self, objects: list) -> list:
        """Remove duplicate objects based on coordinate similarity."""
        if not objects:
            return objects
        
        unique_objects = []
        tolerance = 10
        
        for obj in objects:
            coords = obj.get('coordinates', [])
            if not coords:
                continue
            
            is_duplicate = False
            for existing in unique_objects:
                existing_coords = existing.get('coordinates', [])
                if self._coords_similar(coords, existing_coords, tolerance):
                    # Keep the one with higher confidence
                    if obj.get('confidence', 0) > existing.get('confidence', 0):
                        unique_objects.remove(existing)
                        unique_objects.append(obj)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_objects.append(obj)
        
        return unique_objects
    
    def _coords_similar(self, coords1: list, coords2: list, tolerance: float) -> bool:
        """Check if two coordinate sets are similar within tolerance."""
        if len(coords1) != 4 or len(coords2) != 4:
            return False
        
        return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(coords1, coords2))
    
    def _generate_output_path(self, input_path: str, object_name: str) -> str:
        """Generate output path for annotated image."""
        base_dir = os.path.dirname(input_path)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        return os.path.join(base_dir, f"{base_name}_{object_name}_annotated.jpg")
    
    def list_available_providers(self) -> list:
        """List available VLM providers."""
        return self.vlm_factory.get_available_providers()
    
    def get_system_status(self) -> dict:
        """Get system status information."""
        return {
            'available_providers': self.vlm_factory.get_available_providers(),
            'voice_input_enabled': self.settings.enable_voice_input,
            'tts_enabled': self.tts_handler.is_available(),
            'settings': self.settings.to_dict(),
            'api_keys_status': self.api_keys.validate_keys()
        }

def main():
    """Main entry point for the application."""
    print("VLM Object Recognition System")
    print("=" * 40)
    
    # Initialize system
    vlm_system = VLMObjectRecognition()
    
    # Show system status
    status = vlm_system.get_system_status()
    print(f"Available providers: {', '.join(status['available_providers'])}")
    print(f"Voice input: {'Enabled' if status['voice_input_enabled'] else 'Disabled'}")
    print(f"TTS: {'Enabled' if status['tts_enabled'] else 'Disabled'}")
    print()
    
    # Get image path
    default_image = "~/Downloads/image_000777.jpg"
    image_path = input(f"Enter image path (default: {default_image}): ").strip()
    if not image_path:
        image_path = os.path.expanduser(default_image)
    else:
        image_path = os.path.expanduser(image_path)
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return
    
    # Get provider choice
    providers = status['available_providers']
    if not providers:
        print("Error: No VLM providers available. Please check your API keys.")
        return
    
    if len(providers) > 1:
        print(f"Available providers: {', '.join(providers)}")
        provider = input(f"Choose provider (default: {providers[0]}): ").strip()
        if not provider or provider not in providers:
            provider = providers[0]
    else:
        provider = providers[0]
    
    print(f"Using provider: {provider}")
    print()
    
    # Run detection
    result = vlm_system.run_object_detection(image_path, provider=provider)
    
    if result['success']:
        print(f"Detection completed successfully!")
        print(f"Objects found: {result['objects_found']}")
        print(f"Response: {result['response_text']}")
        print(f"Annotated image saved to: {result['annotated_image_path']}")
    else:
        print(f"Detection failed: {result['error']}")

if __name__ == "__main__":
    main()
