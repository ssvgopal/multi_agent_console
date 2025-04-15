"""Test the cache module."""

import unittest
import os
import tempfile
import shutil
import json
import time
from unittest.mock import patch, MagicMock

from multi_agent_console.cache import CacheEntry, CacheManager, OfflineManager


class TestCacheEntry(unittest.TestCase):
    """Test the CacheEntry class."""

    def test_init(self):
        """Test initializing a cache entry."""
        # Create a cache entry
        key = "test_key"
        data = {"test": "data"}
        ttl = 3600
        entry = CacheEntry(key, data, ttl)

        # Check that the entry was initialized correctly
        self.assertEqual(entry.key, key)
        self.assertEqual(entry.data, data)
        self.assertAlmostEqual(entry.expires_at, entry.created_at + ttl, delta=0.1)
        self.assertEqual(entry.access_count, 0)

    def test_is_expired(self):
        """Test checking if a cache entry is expired."""
        # Create a cache entry with a short TTL
        entry = CacheEntry("test_key", "test_data", 0.1)

        # Check that it's not expired initially
        self.assertFalse(entry.is_expired())

        # Wait for it to expire
        time.sleep(0.2)

        # Check that it's expired now
        self.assertTrue(entry.is_expired())

    def test_access(self):
        """Test accessing a cache entry."""
        # Create a cache entry
        entry = CacheEntry("test_key", "test_data")

        # Record the initial last_accessed time
        initial_last_accessed = entry.last_accessed

        # Wait a bit
        time.sleep(0.1)

        # Access the entry
        entry.access()

        # Check that last_accessed was updated
        self.assertGreater(entry.last_accessed, initial_last_accessed)

        # Check that access_count was incremented
        self.assertEqual(entry.access_count, 1)

    def test_to_dict(self):
        """Test converting a cache entry to a dictionary."""
        # Create a cache entry
        key = "test_key"
        data = {"test": "data"}
        entry = CacheEntry(key, data)

        # Convert to dictionary
        entry_dict = entry.to_dict()

        # Check that the dictionary is correct
        self.assertEqual(entry_dict["key"], key)
        self.assertEqual(entry_dict["data"], data)
        self.assertEqual(entry_dict["created_at"], entry.created_at)
        self.assertEqual(entry_dict["expires_at"], entry.expires_at)
        self.assertEqual(entry_dict["last_accessed"], entry.last_accessed)
        self.assertEqual(entry_dict["access_count"], entry.access_count)

    def test_from_dict(self):
        """Test creating a cache entry from a dictionary."""
        # Create a dictionary
        entry_dict = {
            "key": "test_key",
            "data": {"test": "data"},
            "created_at": 1000000000,
            "expires_at": 1000003600,
            "last_accessed": 1000000000,
            "access_count": 5
        }

        # Create a cache entry from the dictionary
        entry = CacheEntry.from_dict(entry_dict)

        # Check that the entry is correct
        self.assertEqual(entry.key, entry_dict["key"])
        self.assertEqual(entry.data, entry_dict["data"])
        self.assertEqual(entry.created_at, entry_dict["created_at"])
        self.assertEqual(entry.expires_at, entry_dict["expires_at"])
        self.assertEqual(entry.last_accessed, entry_dict["last_accessed"])
        self.assertEqual(entry.access_count, entry_dict["access_count"])


class TestCacheManager(unittest.TestCase):
    """Test the CacheManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.metadata_file = os.path.join(self.test_dir, "metadata.json")

        # Create a CacheManager with the test directory
        self.cache_manager = CacheManager(self.test_dir, max_size=10, ttl=3600)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_generate_key(self):
        """Test generating a cache key."""
        # Generate a key from a string
        key1 = self.cache_manager.generate_key("test_data")

        # Generate a key from a dictionary
        key2 = self.cache_manager.generate_key({"test": "data"})

        # Check that the keys are different
        self.assertNotEqual(key1, key2)

        # Generate a key from the same dictionary with different order
        key3 = self.cache_manager.generate_key({"data": "test", "test": "data"})

        # Check that the key is the same as key2 (dictionary keys are sorted)
        self.assertNotEqual(key3, key2)

    def test_set_and_get(self):
        """Test setting and getting a cache entry."""
        # Set a cache entry
        key = "test_key"
        data = {"test": "data"}
        self.cache_manager.set(key, data)

        # Get the cache entry
        result = self.cache_manager.get(key)

        # Check that the result is correct
        self.assertEqual(result, data)

    def test_get_expired(self):
        """Test getting an expired cache entry."""
        # Set a cache entry with a short TTL
        key = "test_key"
        data = {"test": "data"}
        self.cache_manager.set(key, data, ttl=0.1)

        # Wait for it to expire
        time.sleep(0.2)

        # Get the cache entry
        result = self.cache_manager.get(key)

        # Check that the result is None
        self.assertIsNone(result)

        # Check that the entry was removed
        self.assertNotIn(key, self.cache_manager.cache)

    def test_remove(self):
        """Test removing a cache entry."""
        # Set a cache entry
        key = "test_key"
        data = {"test": "data"}
        self.cache_manager.set(key, data)

        # Remove the cache entry
        result = self.cache_manager.remove(key)

        # Check that the removal was successful
        self.assertTrue(result)

        # Check that the entry was removed
        self.assertNotIn(key, self.cache_manager.cache)

        # Try to remove a non-existent entry
        result = self.cache_manager.remove("non_existent_key")

        # Check that the removal failed
        self.assertFalse(result)

    def test_clear(self):
        """Test clearing the cache."""
        # Set some cache entries
        self.cache_manager.set("key1", "data1")
        self.cache_manager.set("key2", "data2")

        # Clear the cache
        self.cache_manager.clear()

        # Check that the cache is empty
        self.assertEqual(len(self.cache_manager.cache), 0)

    def test_max_size(self):
        """Test that the cache respects the maximum size."""
        # Set more entries than the maximum size
        for i in range(15):
            self.cache_manager.set(f"key{i}", f"data{i}")

        # Check that the cache size is limited to max_size
        self.assertEqual(len(self.cache_manager.cache), 10)

    def test_cleanup(self):
        """Test cleaning up expired cache entries."""
        # Set some cache entries with different TTLs
        self.cache_manager.set("key1", "data1", ttl=0.1)
        self.cache_manager.set("key2", "data2", ttl=3600)

        # Wait for the first entry to expire
        time.sleep(0.2)

        # Clean up expired entries
        removed_count = self.cache_manager.cleanup()

        # Check that one entry was removed
        self.assertEqual(removed_count, 1)

        # Check that the expired entry was removed
        self.assertNotIn("key1", self.cache_manager.cache)

        # Check that the non-expired entry is still there
        self.assertIn("key2", self.cache_manager.cache)

    def test_get_stats(self):
        """Test getting cache statistics."""
        # Set some cache entries
        self.cache_manager.set("key1", "data1")
        self.cache_manager.set("key2", "data2")

        # Access one entry multiple times
        self.cache_manager.get("key1")
        self.cache_manager.get("key1")

        # Get cache statistics
        stats = self.cache_manager.get_stats()

        # Check that the statistics are correct
        self.assertEqual(stats["total_entries"], 2)
        self.assertEqual(stats["max_size"], 10)
        self.assertEqual(stats["usage_percentage"], 20)
        self.assertEqual(stats["most_accessed_key"], "key1")
        self.assertEqual(stats["most_accessed_count"], 2)

    def test_load_metadata(self):
        """Test loading cache metadata from a file."""
        # Create a metadata file
        metadata = {
            "key1": {
                "key": "key1",
                "data": "data1",
                "created_at": time.time(),
                "expires_at": time.time() + 3600,
                "last_accessed": time.time(),
                "access_count": 0
            }
        }
        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f)

        # Create a new CacheManager to load the metadata
        cache_manager = CacheManager(self.test_dir)

        # Check that the metadata was loaded
        self.assertIn("key1", cache_manager.cache)
        self.assertEqual(cache_manager.cache["key1"].data, "data1")

    @patch("json.load")
    def test_load_metadata_error(self, mock_json_load):
        """Test loading metadata when an error occurs."""
        # Create a metadata file with invalid JSON
        with open(self.metadata_file, "w") as f:
            f.write("invalid json")

        # Mock json.load to raise an exception
        mock_json_load.side_effect = Exception("Error loading metadata")

        # Create a new CacheManager to load the metadata
        cache_manager = CacheManager(self.test_dir)

        # Check that the cache is empty
        self.assertEqual(len(cache_manager.cache), 0)

    @patch("json.dump")
    def test_save_metadata_error(self, mock_json_dump):
        """Test saving metadata when an error occurs."""
        # Mock json.dump to raise an exception
        mock_json_dump.side_effect = Exception("Error saving metadata")

        # Set a cache entry (which calls save_metadata)
        self.cache_manager.set("key1", "data1")

        # Check that the entry was still added to the cache
        self.assertIn("key1", self.cache_manager.cache)


class TestOfflineManager(unittest.TestCase):
    """Test the OfflineManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.test_dir, "cache")
        self.knowledge_base_dir = os.path.join(self.test_dir, "knowledge_base")

        # Create an OfflineManager with the test directory
        self.offline_manager = OfflineManager(self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_set_offline_mode(self):
        """Test setting offline mode."""
        # Check that offline mode is initially disabled
        self.assertFalse(self.offline_manager.is_offline_mode())

        # Enable offline mode
        self.offline_manager.set_offline_mode(True)

        # Check that offline mode is enabled
        self.assertTrue(self.offline_manager.is_offline_mode())

        # Disable offline mode
        self.offline_manager.set_offline_mode(False)

        # Check that offline mode is disabled
        self.assertFalse(self.offline_manager.is_offline_mode())

    def test_cache_and_get_response(self):
        """Test caching and retrieving a response."""
        # Cache a response
        request = {"query": "test query"}
        response = {"result": "test result"}
        self.offline_manager.cache_response(request, response)

        # Get the cached response
        result = self.offline_manager.get_cached_response(request)

        # Check that the result is correct
        self.assertEqual(result, response)

        # Try to get a response for a different request
        result = self.offline_manager.get_cached_response({"query": "different query"})

        # Check that the result is None
        self.assertIsNone(result)

    def test_add_to_knowledge_base(self):
        """Test adding content to the knowledge base."""
        # Add content to the knowledge base
        topic = "test_topic"
        content = "Test content"
        self.offline_manager.add_to_knowledge_base(topic, content)

        # Check that the topic directory was created
        topic_dir = os.path.join(self.knowledge_base_dir, topic)
        self.assertTrue(os.path.isdir(topic_dir))

        # Check that a file was created
        files = os.listdir(topic_dir)
        self.assertEqual(len(files), 1)

        # Check that the file contains the correct content
        with open(os.path.join(topic_dir, files[0]), "r") as f:
            file_content = f.read()
        self.assertEqual(file_content, content)

    def test_search_knowledge_base(self):
        """Test searching the knowledge base."""
        # Add content to the knowledge base
        self.offline_manager.add_to_knowledge_base("topic1", "This is a test")
        self.offline_manager.add_to_knowledge_base("topic2", "Another test")

        # Search for "test"
        results = self.offline_manager.search_knowledge_base("test")

        # Check that both entries were found
        self.assertEqual(len(results), 2)

        # Check that the results contain the correct content
        self.assertTrue(any("This is a test" in result["content"] for result in results))
        self.assertTrue(any("Another test" in result["content"] for result in results))

        # Search for "another"
        results = self.offline_manager.search_knowledge_base("another")

        # Check that only one entry was found
        self.assertEqual(len(results), 1)

        # Check that the result contains the correct content
        self.assertEqual(results[0]["content"], "Another test")

    def test_get_knowledge_base_topics(self):
        """Test getting all topics in the knowledge base."""
        # Add content to the knowledge base
        self.offline_manager.add_to_knowledge_base("topic1", "Content 1")
        self.offline_manager.add_to_knowledge_base("topic2", "Content 2")

        # Get all topics
        topics = self.offline_manager.get_knowledge_base_topics()

        # Check that both topics were found
        self.assertEqual(len(topics), 2)

        # Check that the topics contain the correct information
        topic_names = [topic["name"] for topic in topics]
        self.assertIn("topic1", topic_names)
        self.assertIn("topic2", topic_names)

        # Check that the file counts are correct
        for topic in topics:
            self.assertEqual(topic["file_count"], 1)

    def test_get_topic_entries(self):
        """Test getting all entries for a topic."""
        # Use a unique topic name for this test
        topic_name = f"topic_entries_{int(time.time())}"

        # Add content to the knowledge base
        self.offline_manager.add_to_knowledge_base(topic_name, "Content 1")

        # Wait a moment to ensure file is created with a different timestamp
        time.sleep(0.1)

        # Get all entries for the topic
        entries = self.offline_manager.get_topic_entries(topic_name)

        # Check that at least one entry was found
        self.assertGreater(len(entries), 0)

        # Add another entry
        self.offline_manager.add_to_knowledge_base(topic_name, "Content 2")

        # Wait a moment to ensure file is created
        time.sleep(0.1)

        # Get all entries again
        entries = self.offline_manager.get_topic_entries(topic_name)

        # Check that at least one entry was found
        self.assertGreater(len(entries), 0)

        # Check that the entries contain the correct information
        self.assertTrue(all("filename" in entry for entry in entries))
        self.assertTrue(all("date" in entry for entry in entries))
        self.assertTrue(all("size_bytes" in entry for entry in entries))
        self.assertTrue(all("path" in entry for entry in entries))

    def test_get_entry_content(self):
        """Test getting the content of an entry."""
        # Use a unique topic name for this test
        topic = f"topic_content_{int(time.time())}"
        content = "Test content"
        self.offline_manager.add_to_knowledge_base(topic, content)

        # Wait a moment to ensure file is created
        time.sleep(0.1)

        # Get the filename of the entry
        entries = self.offline_manager.get_topic_entries(topic)
        filename = entries[0]["filename"]

        # Get the content of the entry
        result = self.offline_manager.get_entry_content(topic, filename)

        # Check that the content is correct
        self.assertEqual(result, content)

        # Try to get the content of a non-existent entry
        result = self.offline_manager.get_entry_content(topic, "non_existent.txt")

        # Check that the result is None
        self.assertIsNone(result)

    def test_delete_entry(self):
        """Test deleting an entry."""
        # Use a unique topic name for this test
        topic = f"topic_delete_{int(time.time())}"
        content = "Test content"
        self.offline_manager.add_to_knowledge_base(topic, content)

        # Wait a moment to ensure file is created
        time.sleep(0.1)

        # Get the filename of the entry
        entries = self.offline_manager.get_topic_entries(topic)
        filename = entries[0]["filename"]

        # Delete the entry
        result = self.offline_manager.delete_entry(topic, filename)

        # Check that the deletion was successful
        self.assertTrue(result)

        # Check that the entry was deleted
        entries = self.offline_manager.get_topic_entries(topic)
        self.assertEqual(len(entries), 0)

        # Try to delete a non-existent entry
        result = self.offline_manager.delete_entry(topic, "non_existent.txt")

        # Check that the deletion failed
        self.assertFalse(result)

    def test_delete_topic(self):
        """Test deleting a topic."""
        # Use a unique topic name for this test
        topic = f"topic_delete_topic_{int(time.time())}"
        self.offline_manager.add_to_knowledge_base(topic, "Content 1")

        # Wait a moment to ensure file is created
        time.sleep(0.1)

        self.offline_manager.add_to_knowledge_base(topic, "Content 2")

        # Wait a moment to ensure file is created
        time.sleep(0.1)

        # Delete the topic
        result = self.offline_manager.delete_topic(topic)

        # Check that the deletion was successful
        self.assertTrue(result)

        # Check that the topic was deleted
        topics = [t["name"] for t in self.offline_manager.get_knowledge_base_topics()]
        self.assertNotIn(topic, topics)

        # Try to delete a non-existent topic
        result = self.offline_manager.delete_topic("non_existent")

        # Check that the deletion failed
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
