"""Test the cross-platform module."""

import unittest
import tempfile
import shutil
from unittest.mock import MagicMock, patch

from multi_agent_console.cross_platform import (
    CrossPlatformManager, PlatformDetector, CloudSyncManager,
    AccessibilityManager, MobileOptimizer
)


class TestPlatformDetector(unittest.TestCase):
    """Test the PlatformDetector class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a PlatformDetector
        self.detector = PlatformDetector()

    def test_init(self):
        """Test initializing a platform detector."""
        # Check that the attributes were initialized correctly
        self.assertIsNotNone(self.detector.platform)
        self.assertIsNotNone(self.detector.release)
        self.assertIsNotNone(self.detector.version)
        self.assertIsNotNone(self.detector.machine)
        self.assertIsNotNone(self.detector.processor)
        self.assertIsNotNone(self.detector.is_64bit)
        self.assertIsNotNone(self.detector.is_mobile)
        self.assertIsNotNone(self.detector.is_cloud)

    def test_get_platform_info(self):
        """Test getting platform information."""
        # Get platform information
        platform_info = self.detector.get_platform_info()

        # Check that the platform info contains the expected keys
        self.assertIn("platform", platform_info)
        self.assertIn("release", platform_info)
        self.assertIn("version", platform_info)
        self.assertIn("machine", platform_info)
        self.assertIn("processor", platform_info)
        self.assertIn("is_64bit", platform_info)
        self.assertIn("is_mobile", platform_info)
        self.assertIn("is_cloud", platform_info)

        # Check that the platform info values are not empty
        self.assertIsNotNone(platform_info["platform"])
        self.assertIsNotNone(platform_info["release"])
        self.assertIsNotNone(platform_info["version"])
        self.assertIsNotNone(platform_info["machine"])
        self.assertIsNotNone(platform_info["processor"])

    def test_detect_mobile(self):
        """Test detecting if the platform is mobile."""
        # Mock the platform.system function
        with patch.object(self.detector, 'platform', 'Android'):
            # Call _detect_mobile
            result = self.detector._detect_mobile()

            # Check that the result is correct
            self.assertTrue(result)

        # Mock the platform.system function
        with patch.object(self.detector, 'platform', 'iOS'):
            # Call _detect_mobile
            result = self.detector._detect_mobile()

            # Check that the result is correct
            self.assertTrue(result)

        # Mock the platform.system function and machine
        with patch.object(self.detector, 'platform', 'Linux'):
            with patch.object(self.detector, 'machine', 'armv7l'):
                # Call _detect_mobile
                result = self.detector._detect_mobile()

                # Check that the result is correct
                self.assertTrue(result)

        # Mock the platform.system function and machine
        with patch.object(self.detector, 'platform', 'Windows'):
            with patch.object(self.detector, 'machine', 'AMD64'):
                # Call _detect_mobile
                result = self.detector._detect_mobile()

                # Check that the result is correct
                self.assertFalse(result)

    def test_detect_cloud(self):
        """Test detecting if the platform is in the cloud."""
        # Mock the os.environ.get function
        with patch('os.environ.get', return_value='us-west-2'):
            # Call _detect_cloud
            result = self.detector._detect_cloud()

            # Check that the result is correct
            self.assertTrue(result)

        # Mock the os.environ.get function
        with patch('os.environ.get', return_value=None):
            # Call _detect_cloud
            result = self.detector._detect_cloud()

            # Check that the result is correct
            self.assertFalse(result)


class TestCloudSyncManager(unittest.TestCase):
    """Test the CloudSyncManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

        # Create a CloudSyncManager
        self.sync_manager = CloudSyncManager(data_dir=self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_init(self):
        """Test initializing a cloud sync manager."""
        # Check that the attributes were initialized correctly
        self.assertEqual(self.sync_manager.data_dir, self.test_dir)
        self.assertFalse(self.sync_manager.sync_enabled)
        self.assertIsNone(self.sync_manager.last_sync_time)
        self.assertIsNotNone(self.sync_manager.sync_queue)
        self.assertIsNone(self.sync_manager.sync_thread)
        self.assertEqual(self.sync_manager.sync_interval, 300)

    def test_enable_sync(self):
        """Test enabling cloud synchronization."""
        # Enable sync with a URL
        result = self.sync_manager.enable_sync("https://example.com/sync")

        # Check that the result is True
        self.assertTrue(result)

        # Check that sync_enabled was set to True
        self.assertTrue(self.sync_manager.sync_enabled)

        # Check that the sync URL was set
        self.assertEqual(self.sync_manager.sync_url, "https://example.com/sync")

        # Check that the config was updated
        self.assertTrue(self.sync_manager.config["enabled"])
        self.assertEqual(self.sync_manager.config["sync_url"], "https://example.com/sync")

    def test_disable_sync(self):
        """Test disabling cloud synchronization."""
        # Enable sync first
        self.sync_manager.enable_sync("https://example.com/sync")

        # Disable sync
        self.sync_manager.disable_sync()

        # Check that sync_enabled was set to False
        self.assertFalse(self.sync_manager.sync_enabled)

        # Check that the config was updated
        self.assertFalse(self.sync_manager.config["enabled"])

    def test_get_sync_status(self):
        """Test getting the sync status."""
        # Enable sync first
        self.sync_manager.enable_sync("https://example.com/sync")

        # Get sync status
        status = self.sync_manager.get_sync_status()

        # Check that the status contains the expected keys
        self.assertIn("enabled", status)
        self.assertIn("sync_url", status)
        self.assertIn("last_sync_time", status)
        self.assertIn("sync_interval", status)
        self.assertIn("sync_types", status)

        # Check that the status contains the correct values
        self.assertTrue(status["enabled"])
        self.assertEqual(status["sync_url"], "https://example.com/sync")
        self.assertEqual(status["sync_interval"], 300)

    def test_queue_sync_item(self):
        """Test queuing an item for synchronization."""
        # Enable sync first
        self.sync_manager.enable_sync("https://example.com/sync")

        # Queue an item
        self.sync_manager.queue_sync_item("conversation", "123", {"text": "Hello, world!"})

        # Check that the item was added to the queue
        self.assertEqual(self.sync_manager.sync_queue.qsize(), 1)

        # Get the item from the queue
        item = self.sync_manager.sync_queue.get()

        # Check that the item contains the expected keys
        self.assertIn("type", item)
        self.assertIn("id", item)
        self.assertIn("data", item)
        self.assertIn("timestamp", item)

        # Check that the item contains the correct values
        self.assertEqual(item["type"], "conversation")
        self.assertEqual(item["id"], "123")
        self.assertEqual(item["data"], {"text": "Hello, world!"})

        # Try to queue an item when sync is disabled
        self.sync_manager.disable_sync()
        self.sync_manager.queue_sync_item("conversation", "456", {"text": "Hello again!"})

        # Check that the item was not added to the queue
        self.assertEqual(self.sync_manager.sync_queue.qsize(), 0)


class TestAccessibilityManager(unittest.TestCase):
    """Test the AccessibilityManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Create an AccessibilityManager
        self.accessibility_manager = AccessibilityManager()

    def test_init(self):
        """Test initializing an accessibility manager."""
        # Check that the data_dir was set correctly
        self.assertEqual(self.accessibility_manager.data_dir, "data")

        # Check that the config was loaded
        self.assertIsNotNone(self.accessibility_manager.config)

    def test_set_high_contrast(self):
        """Test setting high contrast mode."""
        # Set high contrast mode to True
        self.accessibility_manager.set_high_contrast(True)

        # Check that the config was updated
        self.assertTrue(self.accessibility_manager.config["high_contrast"])

        # Set high contrast mode to False
        self.accessibility_manager.set_high_contrast(False)

        # Check that the config was updated
        self.assertFalse(self.accessibility_manager.config["high_contrast"])

    def test_set_large_text(self):
        """Test setting large text mode."""
        # Set large text mode to True
        self.accessibility_manager.set_large_text(True)

        # Check that the config was updated
        self.assertTrue(self.accessibility_manager.config["large_text"])

        # Set large text mode to False
        self.accessibility_manager.set_large_text(False)

        # Check that the config was updated
        self.assertFalse(self.accessibility_manager.config["large_text"])

    def test_set_screen_reader_mode(self):
        """Test setting screen reader mode."""
        # Set screen reader mode to True
        self.accessibility_manager.set_screen_reader_mode(True)

        # Check that the config was updated
        self.assertTrue(self.accessibility_manager.config["screen_reader_mode"])

        # Set screen reader mode to False
        self.accessibility_manager.set_screen_reader_mode(False)

        # Check that the config was updated
        self.assertFalse(self.accessibility_manager.config["screen_reader_mode"])

    def test_set_reduced_motion(self):
        """Test setting reduced motion mode."""
        # Set reduced motion mode to True
        self.accessibility_manager.set_reduced_motion(True)

        # Check that the config was updated
        self.assertTrue(self.accessibility_manager.config["reduced_motion"])

        # Set reduced motion mode to False
        self.accessibility_manager.set_reduced_motion(False)

        # Check that the config was updated
        self.assertFalse(self.accessibility_manager.config["reduced_motion"])

    def test_set_keyboard_shortcuts_enabled(self):
        """Test setting keyboard shortcuts enabled."""
        # Set keyboard shortcuts enabled to False
        self.accessibility_manager.set_keyboard_shortcuts_enabled(False)

        # Check that the config was updated
        self.assertFalse(self.accessibility_manager.config["keyboard_shortcuts_enabled"])

        # Set keyboard shortcuts enabled to True
        self.accessibility_manager.set_keyboard_shortcuts_enabled(True)

        # Check that the config was updated
        self.assertTrue(self.accessibility_manager.config["keyboard_shortcuts_enabled"])

    def test_set_custom_shortcut(self):
        """Test setting a custom keyboard shortcut."""
        # Set a custom shortcut
        self.accessibility_manager.set_custom_shortcut("new_conversation", "Ctrl+N")

        # Check that the config was updated
        self.assertEqual(self.accessibility_manager.config["custom_shortcuts"]["new_conversation"], "Ctrl+N")

    def test_get_accessibility_settings(self):
        """Test getting accessibility settings."""
        # Set some accessibility settings
        self.accessibility_manager.set_high_contrast(True)
        self.accessibility_manager.set_large_text(True)
        self.accessibility_manager.set_screen_reader_mode(True)

        # Get the accessibility settings
        settings = self.accessibility_manager.get_accessibility_settings()

        # Check that the settings contain the expected keys
        self.assertIn("high_contrast", settings)
        self.assertIn("large_text", settings)
        self.assertIn("screen_reader_mode", settings)
        self.assertIn("reduced_motion", settings)
        self.assertIn("keyboard_shortcuts_enabled", settings)
        self.assertIn("custom_shortcuts", settings)

        # Check that the settings contain the correct values
        self.assertTrue(settings["high_contrast"])
        self.assertTrue(settings["large_text"])
        self.assertTrue(settings["screen_reader_mode"])


class TestMobileOptimizer(unittest.TestCase):
    """Test the MobileOptimizer class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a MobileOptimizer
        self.optimizer = MobileOptimizer()

    def test_init(self):
        """Test initializing a mobile optimizer."""
        # Check that the attributes were initialized correctly
        self.assertIsNotNone(self.optimizer.is_mobile)
        self.assertEqual(self.optimizer.optimizations_enabled, self.optimizer.is_mobile)

    def test_enable_optimizations(self):
        """Test enabling mobile optimizations."""
        # Enable optimizations
        self.optimizer.enable_optimizations(True)

        # Check that optimizations_enabled was set to True
        self.assertTrue(self.optimizer.optimizations_enabled)

        # Disable optimizations
        self.optimizer.enable_optimizations(False)

        # Check that optimizations_enabled was set to False
        self.assertFalse(self.optimizer.optimizations_enabled)

    def test_get_optimized_ui_settings(self):
        """Test getting optimized UI settings."""
        # Enable optimizations
        self.optimizer.enable_optimizations(True)

        # Get optimized UI settings
        settings = self.optimizer.get_optimized_ui_settings()

        # Check that the settings contain the expected keys
        self.assertIn("simplified_ui", settings)
        self.assertIn("touch_friendly", settings)
        self.assertIn("reduced_animations", settings)
        self.assertIn("compact_layout", settings)
        self.assertIn("larger_touch_targets", settings)

        # Check that the settings contain the correct values
        self.assertTrue(settings["simplified_ui"])
        self.assertTrue(settings["touch_friendly"])
        self.assertTrue(settings["reduced_animations"])
        self.assertTrue(settings["compact_layout"])
        self.assertTrue(settings["larger_touch_targets"])

        # Disable optimizations
        self.optimizer.enable_optimizations(False)

        # Get optimized UI settings
        settings = self.optimizer.get_optimized_ui_settings()

        # Check that the settings are empty
        self.assertEqual(settings, {})

    def test_get_optimized_performance_settings(self):
        """Test getting optimized performance settings."""
        # Enable optimizations
        self.optimizer.enable_optimizations(True)

        # Get optimized performance settings
        settings = self.optimizer.get_optimized_performance_settings()

        # Check that the settings contain the expected keys
        self.assertIn("reduced_memory_usage", settings)
        self.assertIn("battery_saving_mode", settings)
        self.assertIn("offline_first", settings)
        self.assertIn("compressed_data", settings)
        self.assertIn("lazy_loading", settings)

        # Check that the settings contain the correct values
        self.assertTrue(settings["reduced_memory_usage"])
        self.assertTrue(settings["battery_saving_mode"])
        self.assertTrue(settings["offline_first"])
        self.assertTrue(settings["compressed_data"])
        self.assertTrue(settings["lazy_loading"])

        # Disable optimizations
        self.optimizer.enable_optimizations(False)

        # Get optimized performance settings
        settings = self.optimizer.get_optimized_performance_settings()

        # Check that the settings are empty
        self.assertEqual(settings, {})

    def test_is_optimization_needed(self):
        """Test checking if optimization is needed."""
        # Set is_mobile to True and enable optimizations
        self.optimizer.is_mobile = True
        self.optimizer.enable_optimizations(True)

        # Check if optimization is needed
        result = self.optimizer.is_optimization_needed()

        # Check that the result is True
        self.assertTrue(result)

        # Disable optimizations
        self.optimizer.enable_optimizations(False)

        # Check if optimization is needed
        result = self.optimizer.is_optimization_needed()

        # Check that the result is False
        self.assertFalse(result)


class TestCrossPlatformManager(unittest.TestCase):
    """Test the CrossPlatformManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

        # Create a CrossPlatformManager
        self.manager = CrossPlatformManager(data_dir=self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_init(self):
        """Test initializing a cross-platform manager."""
        # Check that the attributes were initialized correctly
        self.assertEqual(self.manager.data_dir, self.test_dir)
        self.assertIsInstance(self.manager.platform_detector, PlatformDetector)
        self.assertIsInstance(self.manager.cloud_sync_manager, CloudSyncManager)
        self.assertIsInstance(self.manager.accessibility_manager, AccessibilityManager)
        self.assertIsInstance(self.manager.mobile_optimizer, MobileOptimizer)

    def test_get_platform_info(self):
        """Test getting platform information."""
        # Mock the platform_detector.get_platform_info method
        self.manager.platform_detector.get_platform_info = MagicMock(return_value={"key": "value"})

        # Get platform information
        platform_info = self.manager.get_platform_info()

        # Check that platform_detector.get_platform_info was called
        self.manager.platform_detector.get_platform_info.assert_called_once()

        # Check that the platform information was returned
        self.assertEqual(platform_info, {"key": "value"})

    def test_enable_cloud_sync(self):
        """Test enabling cloud synchronization."""
        # Mock the cloud_sync_manager.enable_sync method
        self.manager.cloud_sync_manager.enable_sync = MagicMock(return_value=True)

        # Enable cloud sync
        result = self.manager.enable_cloud_sync("https://example.com/sync")

        # Check that the result is True
        self.assertTrue(result)

        # Check that cloud_sync_manager.enable_sync was called with the correct parameters
        self.manager.cloud_sync_manager.enable_sync.assert_called_once_with("https://example.com/sync")

    def test_disable_cloud_sync(self):
        """Test disabling cloud synchronization."""
        # Mock the cloud_sync_manager.disable_sync method
        self.manager.cloud_sync_manager.disable_sync = MagicMock()

        # Disable cloud sync
        self.manager.disable_cloud_sync()

        # Check that cloud_sync_manager.disable_sync was called
        self.manager.cloud_sync_manager.disable_sync.assert_called_once()

    def test_get_sync_status(self):
        """Test getting the sync status."""
        # Mock the cloud_sync_manager.get_sync_status method
        self.manager.cloud_sync_manager.get_sync_status = MagicMock(return_value={"key": "value"})

        # Get sync status
        status = self.manager.get_sync_status()

        # Check that cloud_sync_manager.get_sync_status was called
        self.manager.cloud_sync_manager.get_sync_status.assert_called_once()

        # Check that the status was returned
        self.assertEqual(status, {"key": "value"})

    def test_set_accessibility_setting(self):
        """Test setting an accessibility setting."""
        # Mock the accessibility_manager methods
        self.manager.accessibility_manager.set_high_contrast = MagicMock()
        self.manager.accessibility_manager.set_large_text = MagicMock()
        self.manager.accessibility_manager.set_screen_reader_mode = MagicMock()
        self.manager.accessibility_manager.set_reduced_motion = MagicMock()
        self.manager.accessibility_manager.set_keyboard_shortcuts_enabled = MagicMock()

        # Set high contrast
        self.manager.set_accessibility_setting("high_contrast", True)

        # Check that accessibility_manager.set_high_contrast was called with the correct parameters
        self.manager.accessibility_manager.set_high_contrast.assert_called_once_with(True)

        # Set large text
        self.manager.set_accessibility_setting("large_text", True)

        # Check that accessibility_manager.set_large_text was called with the correct parameters
        self.manager.accessibility_manager.set_large_text.assert_called_once_with(True)

        # Set screen reader mode
        self.manager.set_accessibility_setting("screen_reader_mode", True)

        # Check that accessibility_manager.set_screen_reader_mode was called with the correct parameters
        self.manager.accessibility_manager.set_screen_reader_mode.assert_called_once_with(True)

        # Set reduced motion
        self.manager.set_accessibility_setting("reduced_motion", True)

        # Check that accessibility_manager.set_reduced_motion was called with the correct parameters
        self.manager.accessibility_manager.set_reduced_motion.assert_called_once_with(True)

        # Set keyboard shortcuts
        self.manager.set_accessibility_setting("keyboard_shortcuts", True)

        # Check that accessibility_manager.set_keyboard_shortcuts_enabled was called with the correct parameters
        self.manager.accessibility_manager.set_keyboard_shortcuts_enabled.assert_called_once_with(True)

    def test_get_accessibility_settings(self):
        """Test getting accessibility settings."""
        # Mock the accessibility_manager.get_accessibility_settings method
        self.manager.accessibility_manager.get_accessibility_settings = MagicMock(return_value={"key": "value"})

        # Get accessibility settings
        settings = self.manager.get_accessibility_settings()

        # Check that accessibility_manager.get_accessibility_settings was called
        self.manager.accessibility_manager.get_accessibility_settings.assert_called_once()

        # Check that the settings were returned
        self.assertEqual(settings, {"key": "value"})

    def test_enable_mobile_optimizations(self):
        """Test enabling mobile optimizations."""
        # Mock the mobile_optimizer.enable_optimizations method
        self.manager.mobile_optimizer.enable_optimizations = MagicMock()

        # Enable mobile optimizations
        self.manager.enable_mobile_optimizations(True)

        # Check that mobile_optimizer.enable_optimizations was called with the correct parameters
        self.manager.mobile_optimizer.enable_optimizations.assert_called_once_with(True)

    def test_get_optimized_settings(self):
        """Test getting optimized settings."""
        # Mock the mobile_optimizer.is_optimization_needed method
        self.manager.mobile_optimizer.is_optimization_needed = MagicMock(return_value=True)

        # Mock the mobile_optimizer.get_optimized_ui_settings method
        self.manager.mobile_optimizer.get_optimized_ui_settings = MagicMock(return_value={"ui_key": "ui_value"})

        # Mock the mobile_optimizer.get_optimized_performance_settings method
        self.manager.mobile_optimizer.get_optimized_performance_settings = MagicMock(return_value={"perf_key": "perf_value"})

        # Mock the accessibility_manager.get_accessibility_settings method
        self.manager.accessibility_manager.get_accessibility_settings = MagicMock(return_value={"acc_key": "acc_value"})

        # Get optimized settings
        settings = self.manager.get_optimized_settings()

        # Check that mobile_optimizer.is_optimization_needed was called
        self.manager.mobile_optimizer.is_optimization_needed.assert_called_once()

        # Check that mobile_optimizer.get_optimized_ui_settings was called
        self.manager.mobile_optimizer.get_optimized_ui_settings.assert_called_once()

        # Check that mobile_optimizer.get_optimized_performance_settings was called
        self.manager.mobile_optimizer.get_optimized_performance_settings.assert_called_once()

        # Check that accessibility_manager.get_accessibility_settings was called
        self.manager.accessibility_manager.get_accessibility_settings.assert_called_once()

        # Check that the settings were returned
        self.assertEqual(settings, {
            "ui": {"ui_key": "ui_value"},
            "performance": {"perf_key": "perf_value"},
            "accessibility": {"acc_key": "acc_value"}
        })


if __name__ == "__main__":
    unittest.main()
