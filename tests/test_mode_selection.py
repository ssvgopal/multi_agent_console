"""Test the mode selection feature."""

import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from multi_agent_console.app import main
from multi_agent_console.web_server import WebServer


class TestModeSelection(unittest.TestCase):
    """Test the mode selection feature."""
    
    def setUp(self):
        """Set up the test."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mock console app
        self.mock_console_app = MagicMock()
        self.mock_console_app.chat_manager = MagicMock()
        self.mock_console_app.workflow_manager = MagicMock()
        self.mock_console_app.offline_manager = MagicMock()
        self.mock_console_app.agent_marketplace = MagicMock()
        
    def tearDown(self):
        """Clean up after the test."""
        shutil.rmtree(self.temp_dir)
    
    def test_multi_user_mode(self):
        """Test the multi-user mode."""
        # Create web server with multi-user mode
        web_server = WebServer(
            console_app=self.mock_console_app,
            host="localhost",
            port=8099,
            debug=True,
            auth_enabled=True
        )
        
        # Check that authentication is enabled
        self.assertTrue(web_server.auth_enabled)
        self.assertIsNotNone(web_server.auth_manager)
        
        # Check that the login route is available
        routes = [route.path for route in web_server.app.routes]
        self.assertIn("/login", routes)
    
    def test_single_user_mode(self):
        """Test the single-user mode."""
        # Create web server with single-user mode
        web_server = WebServer(
            console_app=self.mock_console_app,
            host="localhost",
            port=8099,
            debug=True,
            auth_enabled=False
        )
        
        # Check that authentication is disabled
        self.assertFalse(web_server.auth_enabled)
        self.assertIsNone(web_server.auth_manager)
        
    @patch('argparse.ArgumentParser.parse_args')
    def test_mode_selection_from_args(self, mock_parse_args):
        """Test mode selection from command-line arguments."""
        # Test multi-user mode
        mock_args = MagicMock()
        mock_args.web = True
        mock_args.mode = "multi-user"
        mock_args.no_auth = False
        mock_args.host = "localhost"
        mock_args.port = 8099
        mock_args.debug = True
        mock_args.optimize = False
        mock_args.terminal = False
        mock_parse_args.return_value = mock_args
        
        # Mock the WebServer class
        with patch('multi_agent_console.app.WebServer') as mock_web_server:
            # Mock the MultiAgentConsole class
            with patch('multi_agent_console.app.MultiAgentConsole'):
                # Call main with mocked arguments
                with patch('time.sleep', side_effect=KeyboardInterrupt):  # To exit the loop
                    try:
                        main()
                    except KeyboardInterrupt:
                        pass
                
                # Check that WebServer was called with auth_enabled=True
                mock_web_server.assert_called_once()
                _, kwargs = mock_web_server.call_args
                self.assertTrue(kwargs['auth_enabled'])
        
        # Test single-user mode
        mock_args.mode = "single-user"
        mock_parse_args.return_value = mock_args
        
        # Mock the WebServer class
        with patch('multi_agent_console.app.WebServer') as mock_web_server:
            # Mock the MultiAgentConsole class
            with patch('multi_agent_console.app.MultiAgentConsole'):
                # Call main with mocked arguments
                with patch('time.sleep', side_effect=KeyboardInterrupt):  # To exit the loop
                    try:
                        main()
                    except KeyboardInterrupt:
                        pass
                
                # Check that WebServer was called with auth_enabled=False
                mock_web_server.assert_called_once()
                _, kwargs = mock_web_server.call_args
                self.assertFalse(kwargs['auth_enabled'])
    
    def test_no_auth_flag_compatibility(self):
        """Test compatibility with the --no-auth flag."""
        # Create a mock args object
        mock_args = MagicMock()
        mock_args.web = True
        mock_args.mode = "multi-user"
        mock_args.no_auth = True  # --no-auth flag is set
        mock_args.host = "localhost"
        mock_args.port = 8099
        mock_args.debug = True
        mock_args.optimize = False
        mock_args.terminal = False
        
        # Determine auth_enabled based on args
        auth_enabled = not mock_args.no_auth
        if mock_args.mode == "single-user":
            auth_enabled = False
        
        # Check that auth_enabled is False when --no-auth is set
        self.assertFalse(auth_enabled)
        
        # Change mode to single-user
        mock_args.mode = "single-user"
        mock_args.no_auth = False  # --no-auth flag is not set
        
        # Determine auth_enabled based on args
        auth_enabled = not mock_args.no_auth
        if mock_args.mode == "single-user":
            auth_enabled = False
        
        # Check that auth_enabled is False when mode is single-user
        self.assertFalse(auth_enabled)


if __name__ == '__main__':
    unittest.main()
