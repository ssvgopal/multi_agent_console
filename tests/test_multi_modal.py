"""Test the multi-modal module."""

import unittest
import os
import tempfile
import shutil
import base64
from unittest.mock import patch, MagicMock

from multi_agent_console.multi_modal import (
    ImageProcessor, AudioProcessor, ChartGenerator,
    DocumentProcessor, MultiModalManager
)


class TestImageProcessor(unittest.TestCase):
    """Test the ImageProcessor class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create an ImageProcessor with the test directory
        self.image_processor = ImageProcessor(self.test_dir)

        # Create a simple test image
        self.test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_save_image(self):
        """Test saving an image from base64 data."""
        # Save the test image
        file_path = self.image_processor.save_image(self.test_image_data)

        # Check that the file was created
        self.assertTrue(os.path.exists(file_path))

        # Check that the file is a valid image
        with open(file_path, 'rb') as f:
            image_data = f.read()
        self.assertTrue(len(image_data) > 0)

    def test_save_image_with_filename(self):
        """Test saving an image with a specific filename."""
        # Save the test image with a specific filename
        filename = "test_image.png"
        file_path = self.image_processor.save_image(self.test_image_data, filename)

        # Check that the file was created with the correct name
        self.assertTrue(os.path.exists(file_path))
        self.assertEqual(os.path.basename(file_path), filename)

    @patch('PIL.Image.open')
    def test_load_image(self, mock_open):
        """Test loading an image from a file."""
        # Mock the Image.open method
        mock_image = MagicMock()
        mock_open.return_value = mock_image

        # Create a test file
        test_file = os.path.join(self.test_dir, "test_image.png")
        with open(test_file, 'wb') as f:
            f.write(base64.b64decode(self.test_image_data))

        # Load the image
        image = self.image_processor.load_image(test_file)

        # Check that Image.open was called with the correct file path
        mock_open.assert_called_once_with(test_file)

        # Check that the image was returned
        self.assertEqual(image, mock_image)

    @patch('PIL.Image.open')
    def test_load_image_error(self, mock_open):
        """Test loading an image when an error occurs."""
        # Mock the Image.open method to raise an exception
        mock_open.side_effect = Exception("Error loading image")

        # Create a test file
        test_file = os.path.join(self.test_dir, "test_image.png")
        with open(test_file, 'wb') as f:
            f.write(base64.b64decode(self.test_image_data))

        # Load the image
        image = self.image_processor.load_image(test_file)

        # Check that None was returned
        self.assertIsNone(image)

    @patch('multi_agent_console.multi_modal.ImageProcessor.load_image')
    def test_get_image_info(self, mock_load_image):
        """Test getting information about an image."""
        # Mock the load_image method
        mock_image = MagicMock()
        mock_image.size = (100, 200)
        mock_image.format = "PNG"
        mock_image.mode = "RGB"
        mock_load_image.return_value = mock_image

        # Create a test file
        test_file = os.path.join(self.test_dir, "test_image.png")
        with open(test_file, 'wb') as f:
            f.write(base64.b64decode(self.test_image_data))

        # Get image info
        info = self.image_processor.get_image_info(test_file)

        # Check that the info contains the expected information
        self.assertIn("Dimensions: 100 x 200 pixels", info)
        self.assertIn("Format: PNG", info)
        self.assertIn("Mode: RGB", info)

    @patch('multi_agent_console.multi_modal.ImageProcessor.load_image')
    def test_get_image_info_error(self, mock_load_image):
        """Test getting image info when loading fails."""
        # Mock the load_image method to return None
        mock_load_image.return_value = None

        # Get image info for a non-existent file
        info = self.image_processor.get_image_info("non_existent.png")

        # Check that an error message was returned
        self.assertTrue(info.startswith("Error"))

    def test_extract_text_from_image_ocr_not_available(self):
        """Test extracting text when OCR is not available."""
        # Create a new ImageProcessor with ocr_available set to False
        image_processor = ImageProcessor(self.test_dir)
        image_processor.ocr_available = False

        # Extract text
        result = image_processor.extract_text_from_image("test_image.png")

        # Check that an error message was returned
        self.assertEqual(result, "OCR is not available. Please install pytesseract.")

    @patch('multi_agent_console.multi_modal.pytesseract', create=True)
    @patch('multi_agent_console.multi_modal.ImageProcessor.load_image')
    def test_extract_text_from_image(self, mock_load_image, mock_pytesseract):
        """Test extracting text from an image."""
        # Mock the load_image method
        mock_image = MagicMock()
        mock_load_image.return_value = mock_image

        # Mock the pytesseract.image_to_string method
        mock_pytesseract.image_to_string.return_value = "Test text"

        # Create a new ImageProcessor with ocr_available set to True
        image_processor = ImageProcessor(self.test_dir)
        image_processor.ocr_available = True

        # Extract text
        result = image_processor.extract_text_from_image("test_image.png")

        # Check that the text was returned
        self.assertEqual(result, "Test text")

        # Check that pytesseract.image_to_string was called with the correct image
        mock_pytesseract.image_to_string.assert_called_once_with(mock_image)

    @patch('multi_agent_console.multi_modal.ImageProcessor.load_image')
    def test_resize_image(self, mock_load_image):
        """Test resizing an image."""
        # Mock the load_image method
        mock_image = MagicMock()
        mock_resized_image = MagicMock()
        mock_image.resize.return_value = mock_resized_image
        mock_load_image.return_value = mock_image

        # Create a test file
        test_file = os.path.join(self.test_dir, "test_image.png")
        with open(test_file, 'wb') as f:
            f.write(base64.b64decode(self.test_image_data))

        # Mock the save method to create a file
        def mock_save(path):
            with open(path, 'w') as f:
                f.write('test')
        mock_resized_image.save.side_effect = mock_save

        # Resize the image
        result = self.image_processor.resize_image(test_file, 50, 100)

        # Check that the result is a file path
        self.assertTrue(os.path.exists(result))

        # Check that resize was called with the correct dimensions
        mock_image.resize.assert_called_once_with((50, 100))

        # Check that save was called on the resized image
        mock_resized_image.save.assert_called_once()


class TestAudioProcessor(unittest.TestCase):
    """Test the AudioProcessor class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create an AudioProcessor with the test directory
        self.audio_processor = AudioProcessor(self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_text_to_speech_not_available(self):
        """Test text-to-speech when it's not available."""
        # Create a new AudioProcessor with tts_available set to False
        audio_processor = AudioProcessor(self.test_dir)
        audio_processor.tts_available = False

        # Convert text to speech
        result = audio_processor.text_to_speech("Test text")

        # Check that an error message was returned
        self.assertEqual(result, "Text-to-speech is not available. Please install pyttsx3.")

    @patch('multi_agent_console.multi_modal.pyttsx3', create=True)
    def test_text_to_speech(self, mock_pyttsx3):
        """Test converting text to speech."""
        # Mock the pyttsx3.init method
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        # Create a new AudioProcessor with tts_available set to True
        audio_processor = AudioProcessor(self.test_dir)
        audio_processor.tts_available = True
        audio_processor.tts_engine = mock_engine

        # Mock the save_to_file method to create a file
        def mock_save_to_file(_text, path):
            with open(path, 'w') as f:
                f.write('test')
        mock_engine.save_to_file.side_effect = mock_save_to_file

        # Convert text to speech
        result = audio_processor.text_to_speech("Test text")

        # Check that the result indicates success
        self.assertTrue("Speech saved to" in result)

        # Check that save_to_file was called with the correct text
        mock_engine.save_to_file.assert_called_once()

        # Check that runAndWait was called
        mock_engine.runAndWait.assert_called_once()

    def test_speech_to_text_not_available(self):
        """Test speech-to-text when it's not available."""
        # Create a new AudioProcessor with stt_available set to False
        audio_processor = AudioProcessor(self.test_dir)
        audio_processor.stt_available = False

        # Convert speech to text
        result = audio_processor.speech_to_text()

        # Check that an error message was returned
        self.assertEqual(result, "Speech-to-text is not available. Please install speech_recognition.")


class TestChartGenerator(unittest.TestCase):
    """Test the ChartGenerator class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create a ChartGenerator with the test directory
        self.chart_generator = ChartGenerator(self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_generate_bar_chart_not_available(self):
        """Test generating a bar chart when matplotlib is not available."""
        # Create a new ChartGenerator with matplotlib_available set to False
        chart_generator = ChartGenerator(self.test_dir)
        chart_generator.matplotlib_available = False

        # Generate a bar chart
        result = chart_generator.generate_bar_chart({"A": 1, "B": 2}, "Title", "X", "Y")

        # Check that an error message was returned
        self.assertEqual(result, "Chart generation is not available. Please install matplotlib.")

    @patch('multi_agent_console.multi_modal.plt', create=True)
    def test_generate_bar_chart(self, mock_plt):
        """Test generating a bar chart."""
        # Mock the plt.figure method
        mock_figure = MagicMock()
        mock_plt.figure.return_value = mock_figure

        # Create a new ChartGenerator with matplotlib_available set to True
        chart_generator = ChartGenerator(self.test_dir)
        chart_generator.matplotlib_available = True

        # Mock the savefig method to create a file
        def mock_savefig(path):
            with open(path, 'w') as f:
                f.write('test')
        mock_plt.savefig.side_effect = mock_savefig

        # Generate a bar chart
        data = {"A": 1, "B": 2, "C": 3}
        result = chart_generator.generate_bar_chart(data, "Title", "X", "Y")

        # Check that the result is a file path
        self.assertTrue(os.path.exists(result))

        # Check that plt.xlabel, plt.ylabel, and plt.title were called with the correct labels
        mock_plt.xlabel.assert_called_once_with("X")
        mock_plt.ylabel.assert_called_once_with("Y")
        mock_plt.title.assert_called_once_with("Title")

        # Check that plt.savefig was called
        mock_plt.savefig.assert_called_once()

        # Check that plt.close was called
        mock_plt.close.assert_called_once()


class TestDocumentProcessor(unittest.TestCase):
    """Test the DocumentProcessor class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create a DocumentProcessor with the test directory
        self.document_processor = DocumentProcessor(self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_extract_text_from_pdf_not_available(self):
        """Test extracting text from a PDF when PyPDF2 is not available."""
        # Create a new DocumentProcessor with pdf_available set to False
        document_processor = DocumentProcessor(self.test_dir)
        document_processor.pdf_available = False

        # Extract text from a PDF
        result = document_processor.extract_text_from_pdf("test.pdf")

        # Check that an error message was returned
        self.assertEqual(result, "PDF processing is not available. Please install PyPDF2.")

    @patch('multi_agent_console.multi_modal.PyPDF2', create=True)
    def test_extract_text_from_pdf(self, mock_pypdf2):
        """Test extracting text from a PDF."""
        # Mock the PyPDF2.PdfReader class
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test text"
        mock_reader.pages = [mock_page]
        mock_pypdf2.PdfReader.return_value = mock_reader

        # Create a test PDF file
        test_file = os.path.join(self.test_dir, "test.pdf")
        with open(test_file, 'wb') as f:
            f.write(b'%PDF-1.4\n')

        # Create a new DocumentProcessor with pdf_available set to True
        document_processor = DocumentProcessor(self.test_dir)
        document_processor.pdf_available = True

        # Extract text from the PDF
        result = document_processor.extract_text_from_pdf(test_file)

        # Check that the text was returned
        self.assertEqual(result, "Test text\n\n")

        # Check that PyPDF2.PdfReader was called with the correct file
        mock_pypdf2.PdfReader.assert_called_once()

        # Check that extract_text was called on the page
        mock_page.extract_text.assert_called_once()


class TestMultiModalManager(unittest.TestCase):
    """Test the MultiModalManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create a MultiModalManager with the test directory
        self.multi_modal_manager = MultiModalManager(self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_init(self):
        """Test initializing the MultiModalManager."""
        # Check that the components were initialized
        self.assertIsInstance(self.multi_modal_manager.image_processor, ImageProcessor)
        self.assertIsInstance(self.multi_modal_manager.audio_processor, AudioProcessor)
        self.assertIsInstance(self.multi_modal_manager.chart_generator, ChartGenerator)
        self.assertIsInstance(self.multi_modal_manager.document_processor, DocumentProcessor)

    def test_get_capabilities(self):
        """Test getting the available capabilities."""
        # Get capabilities
        capabilities = self.multi_modal_manager.get_capabilities()

        # Check that the capabilities dictionary contains the expected keys
        self.assertIn("image_processing", capabilities)
        self.assertIn("ocr", capabilities)
        self.assertIn("text_to_speech", capabilities)
        self.assertIn("speech_to_text", capabilities)
        self.assertIn("chart_generation", capabilities)
        self.assertIn("pdf_processing", capabilities)

        # Check that image_processing is always True
        self.assertTrue(capabilities["image_processing"])

    def test_get_capability_status(self):
        """Test getting a human-readable status of available capabilities."""
        # Get capability status
        status = self.multi_modal_manager.get_capability_status()

        # Check that the status string contains the expected information
        self.assertIn("Multi-Modal Capabilities:", status)
        self.assertIn("Image Processing:", status)
        self.assertIn("Ocr:", status)
        self.assertIn("Text To Speech:", status)
        self.assertIn("Speech To Text:", status)
        self.assertIn("Chart Generation:", status)
        self.assertIn("Pdf Processing:", status)


if __name__ == "__main__":
    unittest.main()
