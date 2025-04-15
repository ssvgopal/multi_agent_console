"""
Multi-Modal Support for MultiAgentConsole.

This module provides capabilities for handling different types of media:
- Image input and analysis
- Audio input and output
- Chart and graph generation
- PDF and document processing
"""

import os
import io
import base64
import logging
import tempfile
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class ImageProcessor:
    """Handles image processing and analysis."""

    def __init__(self, data_dir: str = "data/images"):
        """Initialize the image processor.

        Args:
            data_dir: Directory for storing images
        """
        self.data_dir = data_dir

        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Check if OCR is available
        self.ocr_available = OCR_AVAILABLE

        logging.info(f"Image Processor initialized. OCR available: {self.ocr_available}")

    def save_image(self, image_data: str, filename: Optional[str] = None) -> str:
        """Save an image from base64 data.

        Args:
            image_data: Base64-encoded image data
            filename: Optional filename (default: auto-generated)

        Returns:
            Path to the saved image
        """
        if filename is None:
            # Generate a unique filename
            import uuid
            filename = f"image_{uuid.uuid4().hex}.png"

        # Ensure the filename has an extension
        if not any(filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
            filename += '.png'

        # Create the full path
        file_path = os.path.join(self.data_dir, filename)

        try:
            # Remove header if present (e.g., "data:image/png;base64,")
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]

            # Decode the base64 data
            image_bytes = base64.b64decode(image_data)

            # Save the image
            with open(file_path, 'wb') as f:
                f.write(image_bytes)

            logging.info(f"Image saved to {file_path}")
            return file_path
        except Exception as e:
            logging.error(f"Error saving image: {e}")
            return f"Error saving image: {str(e)}"

    def load_image(self, file_path: str) -> Optional[Image.Image]:
        """Load an image from a file.

        Args:
            file_path: Path to the image file

        Returns:
            PIL Image object or None if loading fails
        """
        try:
            return Image.open(file_path)
        except Exception as e:
            logging.error(f"Error loading image {file_path}: {e}")
            return None

    def get_image_info(self, file_path: str) -> str:
        """Get information about an image.

        Args:
            file_path: Path to the image file

        Returns:
            Information about the image
        """
        try:
            image = self.load_image(file_path)
            if image is None:
                return f"Error: Could not load image {file_path}"

            # Get basic information
            width, height = image.size
            format_name = image.format
            mode = image.mode

            # Get file size
            file_size = os.path.getsize(file_path)
            file_size_kb = file_size / 1024

            # Format the information
            info = f"Image: {os.path.basename(file_path)}\n"
            info += f"Dimensions: {width} x {height} pixels\n"
            info += f"Format: {format_name}\n"
            info += f"Mode: {mode}\n"
            info += f"File size: {file_size_kb:.2f} KB\n"

            return info
        except Exception as e:
            logging.error(f"Error getting image info for {file_path}: {e}")
            return f"Error getting image info: {str(e)}"

    def extract_text_from_image(self, file_path: str) -> str:
        """Extract text from an image using OCR.

        Args:
            file_path: Path to the image file

        Returns:
            Extracted text or error message
        """
        if not self.ocr_available:
            return "OCR is not available. Please install pytesseract."

        try:
            image = self.load_image(file_path)
            if image is None:
                return f"Error: Could not load image {file_path}"

            # Extract text using pytesseract
            text = pytesseract.image_to_string(image)

            if not text.strip():
                return "No text found in the image."

            return text
        except Exception as e:
            logging.error(f"Error extracting text from image {file_path}: {e}")
            return f"Error extracting text: {str(e)}"

    def resize_image(self, file_path: str, width: int, height: int) -> str:
        """Resize an image.

        Args:
            file_path: Path to the image file
            width: New width
            height: New height

        Returns:
            Path to the resized image or error message
        """
        try:
            image = self.load_image(file_path)
            if image is None:
                return f"Error: Could not load image {file_path}"

            # Resize the image
            resized_image = image.resize((width, height))

            # Generate output filename
            filename, ext = os.path.splitext(os.path.basename(file_path))
            output_path = os.path.join(self.data_dir, f"{filename}_resized{ext}")

            # Save the resized image
            resized_image.save(output_path)

            return output_path
        except Exception as e:
            logging.error(f"Error resizing image {file_path}: {e}")
            return f"Error resizing image: {str(e)}"


class AudioProcessor:
    """Handles audio processing and synthesis."""

    def __init__(self, data_dir: str = "data/audio"):
        """Initialize the audio processor.

        Args:
            data_dir: Directory for storing audio files
        """
        self.data_dir = data_dir

        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Check if TTS and STT are available
        self.tts_available = TTS_AVAILABLE
        self.stt_available = STT_AVAILABLE

        # Initialize TTS engine if available
        self.tts_engine = None
        if self.tts_available:
            try:
                self.tts_engine = pyttsx3.init()
            except Exception as e:
                logging.error(f"Error initializing TTS engine: {e}")
                self.tts_available = False

        logging.info(f"Audio Processor initialized. TTS available: {self.tts_available}, STT available: {self.stt_available}")

    def text_to_speech(self, text: str, output_file: Optional[str] = None) -> str:
        """Convert text to speech.

        Args:
            text: Text to convert to speech
            output_file: Optional output file path

        Returns:
            Path to the audio file or error message
        """
        if not self.tts_available or self.tts_engine is None:
            return "Text-to-speech is not available. Please install pyttsx3."

        try:
            # Generate output filename if not provided
            if output_file is None:
                import uuid
                output_file = os.path.join(self.data_dir, f"speech_{uuid.uuid4().hex}.mp3")

            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Convert text to speech and save to file
            self.tts_engine.save_to_file(text, output_file)
            self.tts_engine.runAndWait()

            return f"Speech saved to {output_file}"
        except Exception as e:
            logging.error(f"Error converting text to speech: {e}")
            return f"Error converting text to speech: {str(e)}"

    def text_to_speech_with_voice(self, text: str, output_file: Optional[str] = None, voice: str = "default") -> str:
        """Convert text to speech with a specific voice.

        Args:
            text: Text to convert to speech
            output_file: Optional output file path
            voice: Voice to use (default, male, female)

        Returns:
            Path to the audio file or error message
        """
        if not self.tts_available or self.tts_engine is None:
            return "Text-to-speech is not available. Please install pyttsx3."

        try:
            # Generate output filename if not provided
            if output_file is None:
                import uuid
                output_file = os.path.join(self.data_dir, f"speech_{uuid.uuid4().hex}.mp3")

            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Get available voices
            voices = self.tts_engine.getProperty('voices')

            # Set voice based on parameter
            if voice == "male" and len(voices) > 0:
                self.tts_engine.setProperty('voice', voices[0].id)
            elif voice == "female" and len(voices) > 1:
                self.tts_engine.setProperty('voice', voices[1].id)
            # Default voice is already set

            # Convert text to speech and save to file
            self.tts_engine.save_to_file(text, output_file)
            self.tts_engine.runAndWait()

            return f"Speech saved to {output_file}"
        except Exception as e:
            logging.error(f"Error converting text to speech with voice {voice}: {e}")
            return f"Error converting text to speech: {str(e)}"

    def speech_to_text(self, audio_file: Optional[str] = None, duration: int = 5) -> str:
        """Convert speech to text.

        Args:
            audio_file: Path to the audio file (if None, record from microphone)
            duration: Duration to record in seconds (only used when recording from microphone)

        Returns:
            Transcribed text or error message
        """
        if not self.stt_available:
            return "Speech-to-text is not available. Please install speech_recognition."

        try:
            recognizer = sr.Recognizer()

            if audio_file is None:
                # Record from microphone
                with sr.Microphone() as source:
                    logging.info(f"Recording audio for {duration} seconds...")
                    audio_data = recognizer.record(source, duration=duration)
            else:
                # Load from file
                with sr.AudioFile(audio_file) as source:
                    audio_data = recognizer.record(source)

            # Recognize speech using Google Speech Recognition
            text = recognizer.recognize_google(audio_data)

            return text
        except sr.UnknownValueError:
            return "Speech could not be understood"
        except sr.RequestError as e:
            return f"Could not request results from Google Speech Recognition service: {e}"
        except Exception as e:
            logging.error(f"Error converting speech to text: {e}")
            return f"Error converting speech to text: {str(e)}"


class ChartGenerator:
    """Generates charts and graphs."""

    def __init__(self, data_dir: str = "data/charts"):
        """Initialize the chart generator.

        Args:
            data_dir: Directory for storing charts
        """
        self.data_dir = data_dir

        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Check if matplotlib is available
        self.matplotlib_available = MATPLOTLIB_AVAILABLE

        logging.info(f"Chart Generator initialized. Matplotlib available: {self.matplotlib_available}")

    def generate_bar_chart(self, data: Dict[str, float], title: str, xlabel: str, ylabel: str) -> str:
        """Generate a bar chart.

        Args:
            data: Dictionary mapping categories to values
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label

        Returns:
            Path to the generated chart or error message
        """
        if not self.matplotlib_available:
            return "Chart generation is not available. Please install matplotlib."

        try:
            # Create figure and axis
            plt.figure(figsize=(10, 6))

            # Create bar chart
            plt.bar(data.keys(), data.values())

            # Add labels and title
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.title(title)

            # Rotate x-axis labels if there are many categories
            if len(data) > 5:
                plt.xticks(rotation=45, ha='right')

            # Adjust layout
            plt.tight_layout()

            # Generate output filename
            import uuid
            output_path = os.path.join(self.data_dir, f"bar_chart_{uuid.uuid4().hex}.png")

            # Save the chart
            plt.savefig(output_path)
            plt.close()

            return output_path
        except Exception as e:
            logging.error(f"Error generating bar chart: {e}")
            return f"Error generating bar chart: {str(e)}"

    def generate_line_chart(self, data: Dict[str, List[float]], x_values: List[Any], title: str, xlabel: str, ylabel: str) -> str:
        """Generate a line chart.

        Args:
            data: Dictionary mapping series names to lists of values
            x_values: List of x-axis values
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label

        Returns:
            Path to the generated chart or error message
        """
        if not self.matplotlib_available:
            return "Chart generation is not available. Please install matplotlib."

        try:
            # Create figure and axis
            plt.figure(figsize=(10, 6))

            # Create line chart for each series
            for series_name, y_values in data.items():
                plt.plot(x_values[:len(y_values)], y_values, label=series_name)

            # Add labels and title
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.title(title)

            # Add legend
            if len(data) > 1:
                plt.legend()

            # Adjust layout
            plt.tight_layout()

            # Generate output filename
            import uuid
            output_path = os.path.join(self.data_dir, f"line_chart_{uuid.uuid4().hex}.png")

            # Save the chart
            plt.savefig(output_path)
            plt.close()

            return output_path
        except Exception as e:
            logging.error(f"Error generating line chart: {e}")
            return f"Error generating line chart: {str(e)}"

    def generate_pie_chart(self, data: Dict[str, float], title: str) -> str:
        """Generate a pie chart.

        Args:
            data: Dictionary mapping categories to values
            title: Chart title

        Returns:
            Path to the generated chart or error message
        """
        if not self.matplotlib_available:
            return "Chart generation is not available. Please install matplotlib."

        try:
            # Create figure and axis
            plt.figure(figsize=(8, 8))

            # Create pie chart
            plt.pie(data.values(), labels=data.keys(), autopct='%1.1f%%', startangle=90)

            # Add title
            plt.title(title)

            # Ensure the pie chart is drawn as a circle
            plt.axis('equal')

            # Adjust layout
            plt.tight_layout()

            # Generate output filename
            import uuid
            output_path = os.path.join(self.data_dir, f"pie_chart_{uuid.uuid4().hex}.png")

            # Save the chart
            plt.savefig(output_path)
            plt.close()

            return output_path
        except Exception as e:
            logging.error(f"Error generating pie chart: {e}")
            return f"Error generating pie chart: {str(e)}"


class DocumentProcessor:
    """Processes PDF and other document formats."""

    def __init__(self, data_dir: str = "data/documents"):
        """Initialize the document processor.

        Args:
            data_dir: Directory for storing documents
        """
        self.data_dir = data_dir

        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Check if PDF processing is available
        self.pdf_available = PDF_AVAILABLE

        logging.info(f"Document Processor initialized. PDF processing available: {self.pdf_available}")

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text or error message
        """
        if not self.pdf_available:
            return "PDF processing is not available. Please install PyPDF2."

        try:
            # Open the PDF file
            with open(file_path, 'rb') as file:
                # Create a PDF reader object
                reader = PyPDF2.PdfReader(file)

                # Get the number of pages
                num_pages = len(reader.pages)

                # Extract text from each page
                text = ""
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n\n"

                if not text.strip():
                    return "No text found in the PDF."

                return text
        except Exception as e:
            logging.error(f"Error extracting text from PDF {file_path}: {e}")
            return f"Error extracting text from PDF: {str(e)}"

    def get_pdf_info(self, file_path: str) -> str:
        """Get information about a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Information about the PDF or error message
        """
        if not self.pdf_available:
            return "PDF processing is not available. Please install PyPDF2."

        try:
            # Open the PDF file
            with open(file_path, 'rb') as file:
                # Create a PDF reader object
                reader = PyPDF2.PdfReader(file)

                # Get the number of pages
                num_pages = len(reader.pages)

                # Get file size
                file_size = os.path.getsize(file_path)
                file_size_kb = file_size / 1024

                # Get metadata
                metadata = reader.metadata

                # Format the information
                info = f"PDF: {os.path.basename(file_path)}\n"
                info += f"Number of pages: {num_pages}\n"
                info += f"File size: {file_size_kb:.2f} KB\n"

                if metadata:
                    info += "\nMetadata:\n"
                    for key, value in metadata.items():
                        if value and str(value).strip():
                            # Remove the /prefix from keys
                            clean_key = key[1:] if key.startswith('/') else key
                            info += f"  {clean_key}: {value}\n"

                return info
        except Exception as e:
            logging.error(f"Error getting PDF info for {file_path}: {e}")
            return f"Error getting PDF info: {str(e)}"


class MultiModalManager:
    """Manages multi-modal capabilities."""

    def __init__(self, data_dir: str = "data"):
        """Initialize the multi-modal manager.

        Args:
            data_dir: Base directory for multi-modal data
        """
        self.data_dir = data_dir

        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Initialize components
        self.image_processor = ImageProcessor(os.path.join(data_dir, "images"))
        self.audio_processor = AudioProcessor(os.path.join(data_dir, "audio"))
        self.chart_generator = ChartGenerator(os.path.join(data_dir, "charts"))
        self.document_processor = DocumentProcessor(os.path.join(data_dir, "documents"))

        logging.info("Multi-Modal Manager initialized")

    def get_capabilities(self) -> Dict[str, bool]:
        """Get the available multi-modal capabilities.

        Returns:
            Dictionary of capabilities and their availability
        """
        return {
            "image_processing": True,
            "ocr": self.image_processor.ocr_available,
            "text_to_speech": self.audio_processor.tts_available,
            "speech_to_text": self.audio_processor.stt_available,
            "chart_generation": self.chart_generator.matplotlib_available,
            "pdf_processing": self.document_processor.pdf_available
        }

    def get_capability_status(self) -> str:
        """Get a human-readable status of available capabilities.

        Returns:
            Status string
        """
        capabilities = self.get_capabilities()

        status = "Multi-Modal Capabilities:\n"
        for capability, available in capabilities.items():
            status += f"- {capability.replace('_', ' ').title()}: {'Available' if available else 'Not Available'}\n"

        return status
