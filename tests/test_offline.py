"""Test the offline module."""

import unittest
import os
import tempfile
import shutil
import json
import sqlite3
import time
from unittest.mock import patch, MagicMock
from datetime import datetime

from multi_agent_console.offline import ResponseCache, KnowledgeBase, LocalModelManager, OfflineManager


class TestResponseCache(unittest.TestCase):
    """Test the ResponseCache class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create a ResponseCache with the test directory
        self.response_cache = ResponseCache(self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_init(self):
        """Test initializing a response cache."""
        # Check that the cache directory was created
        self.assertTrue(os.path.exists(self.test_dir))

        # Check that the database was created
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "response_cache.db")))

        # Check that the database has the expected tables
        conn = sqlite3.connect(os.path.join(self.test_dir, "response_cache.db"))
        cursor = conn.cursor()

        # Check that the cache table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cache'")
        self.assertIsNotNone(cursor.fetchone())

        conn.close()

    def test_put_and_get(self):
        """Test storing and retrieving a response."""
        # Store a response
        query = "Test query"
        response = "Test response"
        model_id = "test-model"
        metadata = {"test_key": "test_value"}

        self.response_cache.put(query, response, model_id, metadata)

        # Retrieve the response
        result = self.response_cache.get(query, model_id)

        # Check that the response was retrieved correctly
        self.assertIsNotNone(result)
        self.assertEqual(result["query"], query)
        self.assertEqual(result["response"], response)
        self.assertEqual(result["model_id"], model_id)
        self.assertEqual(result["metadata"]["test_key"], "test_value")

        # Try to retrieve a non-existent response
        result = self.response_cache.get("Non-existent query", model_id)
        self.assertIsNone(result)

    def test_hash_query(self):
        """Test generating a hash for a query."""
        # Generate a hash
        query = "Test query"
        model_id = "test-model"
        hash1 = self.response_cache._hash_query(query, model_id)

        # Check that the hash is a string
        self.assertIsInstance(hash1, str)

        # Check that the same query and model ID produce the same hash
        hash2 = self.response_cache._hash_query(query, model_id)
        self.assertEqual(hash1, hash2)

        # Check that different queries produce different hashes
        hash3 = self.response_cache._hash_query("Different query", model_id)
        self.assertNotEqual(hash1, hash3)

        # Check that different model IDs produce different hashes
        hash4 = self.response_cache._hash_query(query, "different-model")
        self.assertNotEqual(hash1, hash4)


class TestKnowledgeBase(unittest.TestCase):
    """Test the KnowledgeBase class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create a KnowledgeBase with the test directory
        self.knowledge_base = KnowledgeBase(self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_init(self):
        """Test initializing a knowledge base."""
        # Check that the knowledge base directory was created
        self.assertTrue(os.path.exists(self.test_dir))

        # Check that the database was created
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "knowledge_base.db")))

        # Check that the database has the expected tables
        conn = sqlite3.connect(os.path.join(self.test_dir, "knowledge_base.db"))
        cursor = conn.cursor()

        # Check that the documents table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        self.assertIsNotNone(cursor.fetchone())

        # Check that the document_index table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_index'")
        self.assertIsNotNone(cursor.fetchone())

        conn.close()

    def test_add_document(self):
        """Test adding a document to the knowledge base."""
        # Add a document
        title = "Test Document"
        content = "This is a test document."
        source = "Test Source"
        category = "Test Category"
        metadata = {"test_key": "test_value"}

        document_id = self.knowledge_base.add_document(title, content, source, category, metadata)

        # Check that the document ID is a positive integer
        self.assertIsInstance(document_id, int)
        self.assertGreater(document_id, 0)

        # Check that the document was added to the database
        conn = sqlite3.connect(os.path.join(self.test_dir, "knowledge_base.db"))
        cursor = conn.cursor()

        cursor.execute("SELECT title, content, source, category FROM documents WHERE id = ?", (document_id,))
        result = cursor.fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(result[0], title)
        self.assertEqual(result[1], content)
        self.assertEqual(result[2], source)
        self.assertEqual(result[3], category)

        conn.close()

    def test_search(self):
        """Test searching the knowledge base."""
        # Add some documents
        self.knowledge_base.add_document(
            "Python Programming",
            "Python is a high-level programming language.",
            "Book",
            "Programming"
        )

        self.knowledge_base.add_document(
            "JavaScript Basics",
            "JavaScript is a scripting language for web development.",
            "Website",
            "Programming"
        )

        # Search for documents
        results = self.knowledge_base.search("Python")

        # Check that the search returned the expected document
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Python Programming")

        # Search for a term that appears in multiple documents
        results = self.knowledge_base.search("programming")

        # Check that the search returned both documents
        self.assertEqual(len(results), 2)

        # Search for a non-existent term
        results = self.knowledge_base.search("nonexistent")

        # Check that the search returned no documents
        self.assertEqual(len(results), 0)

    def test_get_document(self):
        """Test getting a document from the knowledge base."""
        # Add a document
        title = "Test Document"
        content = "This is a test document."
        document_id = self.knowledge_base.add_document(title, content)

        # Get the document
        document = self.knowledge_base.get_document(document_id)

        # Check that the document was retrieved correctly
        self.assertIsNotNone(document)
        self.assertEqual(document["title"], title)
        self.assertEqual(document["content"], content)

        # Try to get a non-existent document
        document = self.knowledge_base.get_document(9999)

        # Check that None was returned
        self.assertIsNone(document)

    def test_update_document(self):
        """Test updating a document in the knowledge base."""
        # Add a document
        title = "Original Title"
        content = "Original content."
        document_id = self.knowledge_base.add_document(title, content)

        # Update the document
        new_title = "Updated Title"
        new_content = "Updated content."
        result = self.knowledge_base.update_document(document_id, new_title, new_content)

        # Check that the update was successful
        self.assertTrue(result)

        # Get the updated document
        document = self.knowledge_base.get_document(document_id)

        # Check that the document was updated correctly
        self.assertEqual(document["title"], new_title)
        self.assertEqual(document["content"], new_content)

        # Try to update a non-existent document
        result = self.knowledge_base.update_document(9999, "New Title", "New content.")

        # Check that the update failed
        self.assertFalse(result)

    def test_delete_document(self):
        """Test deleting a document from the knowledge base."""
        # Add a document
        document_id = self.knowledge_base.add_document("Test Document", "Test content.")

        # Delete the document
        result = self.knowledge_base.delete_document(document_id)

        # Check that the deletion was successful
        self.assertTrue(result)

        # Try to get the deleted document
        document = self.knowledge_base.get_document(document_id)

        # Check that the document was deleted
        self.assertIsNone(document)

        # Try to delete a non-existent document
        result = self.knowledge_base.delete_document(9999)

        # Check that the deletion failed
        self.assertFalse(result)

    def test_get_stats(self):
        """Test getting knowledge base statistics."""
        # Add some documents
        self.knowledge_base.add_document(
            "Document 1",
            "Content 1",
            category="Category A"
        )

        self.knowledge_base.add_document(
            "Document 2",
            "Content 2",
            category="Category A"
        )

        self.knowledge_base.add_document(
            "Document 3",
            "Content 3",
            category="Category B"
        )

        # Get statistics
        stats = self.knowledge_base.get_stats()

        # Check that the statistics are correct
        self.assertEqual(stats["total_documents"], 3)
        self.assertEqual(stats["category_counts"]["Category A"], 2)
        self.assertEqual(stats["category_counts"]["Category B"], 1)
        self.assertIsNotNone(stats["newest_document"])
        self.assertIsNotNone(stats["oldest_document"])


class TestLocalModelManager(unittest.TestCase):
    """Test the LocalModelManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create a LocalModelManager with the test directory
        self.model_manager = LocalModelManager(self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_init(self):
        """Test initializing a local model manager."""
        # Check that the models directory was created
        self.assertTrue(os.path.exists(self.test_dir))

        # Check that the available models dictionary was initialized
        self.assertIsInstance(self.model_manager.available_models, dict)

    @patch('multi_agent_console.offline.LocalModelManager._scan_models')
    def test_scan_models(self, mock_scan_models):
        """Test scanning for available models."""
        # Mock the _scan_models method to return some test models
        test_models = [
            {"model_id": "model1", "name": "Model 1", "size": 1000000},
            {"model_id": "model2", "name": "Model 2", "size": 2000000}
        ]
        mock_scan_models.return_value = test_models

        # Create a new LocalModelManager to trigger the scan
        model_manager = LocalModelManager(self.test_dir)

        # Check that the available models were set correctly
        self.assertEqual(model_manager.available_models, test_models)

        # Check that _scan_models was called
        mock_scan_models.assert_called_once()

    def test_get_available_models(self):
        """Test getting available models."""
        # Mock the get_available_models method to return test models
        test_models = [
            {"model_id": "model1", "name": "Model 1", "size": 1000000},
            {"model_id": "model2", "name": "Model 2", "size": 2000000}
        ]
        self.model_manager.get_available_models = MagicMock(return_value=test_models)

        # Get available models
        models = self.model_manager.get_available_models()

        # Check that the models were returned correctly
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]["model_id"], "model1")
        self.assertEqual(models[1]["model_id"], "model2")

    def test_download_model(self):
        """Test downloading a model."""
        # Mock the download_model method to return success
        self.model_manager.download_model = MagicMock(return_value=True)

        # Download a model
        result = self.model_manager.download_model("test-model")

        # Check that the download was successful
        self.assertTrue(result)

        # Check that download_model was called with the correct model ID
        self.model_manager.download_model.assert_called_once_with("test-model")

    def test_load_model(self):
        """Test loading a model."""
        # Mock the load_model method to return a test model
        test_model = {"model_id": "test-model", "name": "Test Model"}
        self.model_manager.load_model = MagicMock(return_value=test_model)

        # Load a model
        model = self.model_manager.load_model("test-model")

        # Check that the model was loaded correctly
        self.assertEqual(model, test_model)

        # Check that load_model was called with the correct model ID
        self.model_manager.load_model.assert_called_once_with("test-model")


class TestOfflineManager(unittest.TestCase):
    """Test the OfflineManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create an OfflineManager with the test directory
        self.offline_manager = OfflineManager(self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_init(self):
        """Test initializing an offline manager."""
        # Check that the data directory was created
        self.assertTrue(os.path.exists(self.test_dir))

        # Check that the components were initialized
        self.assertIsInstance(self.offline_manager.response_cache, ResponseCache)
        self.assertIsInstance(self.offline_manager.knowledge_base, KnowledgeBase)
        self.assertIsInstance(self.offline_manager.local_model_manager, LocalModelManager)

        # Check that offline mode is initially disabled
        self.assertFalse(self.offline_manager.offline_mode)

    def test_set_offline_mode(self):
        """Test setting offline mode."""
        # Set offline mode to enabled
        self.offline_manager.set_offline_mode(True)

        # Check that offline mode was enabled
        self.assertTrue(self.offline_manager.offline_mode)

        # Set offline mode to disabled
        self.offline_manager.set_offline_mode(False)

        # Check that offline mode was disabled
        self.assertFalse(self.offline_manager.offline_mode)

    def test_is_offline_mode(self):
        """Test checking if offline mode is enabled."""
        # Initially, offline mode should be disabled
        self.assertFalse(self.offline_manager.is_offline_mode())

        # Enable offline mode
        self.offline_manager.set_offline_mode(True)

        # Check that is_offline_mode returns True
        self.assertTrue(self.offline_manager.is_offline_mode())

    def test_get_cached_response(self):
        """Test getting a cached response."""
        # Mock the response_cache.get method
        self.offline_manager.response_cache.get = MagicMock(return_value={
            "response": "Cached response"
        })

        # Get a cached response
        response = self.offline_manager.get_cached_response("Test query", "test-model")

        # Check that the response was returned correctly
        self.assertEqual(response, "Cached response")

        # Check that response_cache.get was called with the correct parameters
        self.offline_manager.response_cache.get.assert_called_once_with("Test query", "test-model")

        # Mock the response_cache.get method to return None
        self.offline_manager.response_cache.get = MagicMock(return_value=None)

        # Try to get a non-existent cached response
        response = self.offline_manager.get_cached_response("Non-existent query", "test-model")

        # Check that None was returned
        self.assertIsNone(response)

    def test_cache_response(self):
        """Test caching a response."""
        # Mock the response_cache.put method
        self.offline_manager.response_cache.put = MagicMock()

        # Cache a response
        query = "Test query"
        response = "Test response"
        model_id = "test-model"
        metadata = {"test_key": "test_value"}

        self.offline_manager.cache_response(query, response, model_id, metadata)

        # Check that response_cache.put was called with the correct parameters
        self.offline_manager.response_cache.put.assert_called_once_with(query, response, model_id, metadata)

    def test_search_knowledge_base(self):
        """Test searching the knowledge base."""
        # Mock the knowledge_base.search method
        test_results = [{"title": "Test Document", "content": "Test content"}]
        self.offline_manager.knowledge_base.search = MagicMock(return_value=test_results)

        # Search the knowledge base
        results = self.offline_manager.search_knowledge_base("test query", 5)

        # Check that the results were returned correctly
        self.assertEqual(results, test_results)

        # Check that knowledge_base.search was called with the correct parameters
        self.offline_manager.knowledge_base.search.assert_called_once_with("test query", 5)

    def test_add_to_knowledge_base(self):
        """Test adding a document to the knowledge base."""
        # Mock the knowledge_base.add_document method
        self.offline_manager.knowledge_base.add_document = MagicMock(return_value=123)

        # Add a document to the knowledge base
        title = "Test Document"
        content = "Test content"
        source = "Test Source"
        category = "Test Category"
        metadata = {"test_key": "test_value"}

        document_id = self.offline_manager.add_to_knowledge_base(title, content, source, category, metadata)

        # Check that the document ID was returned correctly
        self.assertEqual(document_id, 123)

        # Check that knowledge_base.add_document was called with the correct parameters
        self.offline_manager.knowledge_base.add_document.assert_called_once_with(title, content, source, category, metadata)

    def test_get_available_local_models(self):
        """Test getting available local models."""
        # Mock the local_model_manager.get_available_models method
        test_models = [{"model_id": "model1", "name": "Model 1"}]
        self.offline_manager.local_model_manager.get_available_models = MagicMock(return_value=test_models)

        # Get available local models
        models = self.offline_manager.get_available_local_models()

        # Check that the models were returned correctly
        self.assertEqual(models, test_models)

        # Check that local_model_manager.get_available_models was called
        self.offline_manager.local_model_manager.get_available_models.assert_called_once()

    def test_get_offline_status(self):
        """Test getting the status of offline capabilities."""
        # Mock the component methods
        self.offline_manager.response_cache.get_stats = MagicMock(return_value={
            "total_entries": 10,
            "model_counts": {"model1": 5, "model2": 5}
        })

        self.offline_manager.knowledge_base.get_stats = MagicMock(return_value={
            "total_documents": 20,
            "category_counts": {"category1": 10, "category2": 10}
        })

        self.offline_manager.local_model_manager.get_available_models = MagicMock(return_value=[
            {"model_id": "model1", "name": "Model 1"},
            {"model_id": "model2", "name": "Model 2"}
        ])

        # Get offline status
        status = self.offline_manager.get_offline_status()

        # Check that the status contains the expected information
        self.assertIn("offline_mode", status)
        self.assertIn("cache", status)
        self.assertIn("knowledge_base", status)
        self.assertIn("local_models", status)

        self.assertEqual(status["cache"]["total_entries"], 10)
        self.assertEqual(status["knowledge_base"]["total_documents"], 20)
        self.assertEqual(status["local_models"]["count"], 2)


if __name__ == "__main__":
    unittest.main()
