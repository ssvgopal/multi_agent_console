"""
Offline Capabilities for MultiAgentConsole.

This module provides offline functionality:
- Local model support
- Cached responses
- Offline knowledge base
"""

import os
import json
import logging
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import sqlite3
from datetime import datetime


class ResponseCache:
    """Caches responses for offline use."""
    
    def __init__(self, cache_dir: str = "data/cache"):
        """Initialize the response cache.
        
        Args:
            cache_dir: Directory for storing cached responses
        """
        self.cache_dir = cache_dir
        self.db_path = os.path.join(cache_dir, "response_cache.db")
        
        # Create directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        logging.info(f"Response cache initialized at {self.db_path}")
    
    def _init_db(self) -> None:
        """Initialize the cache database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache (
            query_hash TEXT PRIMARY KEY,
            query TEXT,
            response TEXT,
            model_id TEXT,
            timestamp DATETIME,
            metadata TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _hash_query(self, query: str, model_id: str) -> str:
        """Generate a hash for a query.
        
        Args:
            query: Query string
            model_id: Model identifier
            
        Returns:
            Hash string
        """
        hash_input = f"{query}|{model_id}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def get(self, query: str, model_id: str) -> Optional[Dict[str, Any]]:
        """Get a cached response.
        
        Args:
            query: Query string
            model_id: Model identifier
            
        Returns:
            Cached response or None if not found
        """
        query_hash = self._hash_query(query, model_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT query, response, model_id, timestamp, metadata FROM cache WHERE query_hash = ?",
            (query_hash,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "query": result[0],
                "response": result[1],
                "model_id": result[2],
                "timestamp": result[3],
                "metadata": json.loads(result[4]) if result[4] else {}
            }
        
        return None
    
    def put(self, query: str, response: str, model_id: str, metadata: Dict[str, Any] = None) -> None:
        """Store a response in the cache.
        
        Args:
            query: Query string
            response: Response string
            model_id: Model identifier
            metadata: Additional metadata
        """
        query_hash = self._hash_query(query, model_id)
        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR REPLACE INTO cache (query_hash, query, response, model_id, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?)",
            (query_hash, query, response, model_id, timestamp, metadata_json)
        )
        
        conn.commit()
        conn.close()
    
    def clear(self) -> None:
        """Clear the cache."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cache")
        
        conn.commit()
        conn.close()
        
        logging.info("Response cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM cache")
        count = cursor.fetchone()[0]
        
        cursor.execute("SELECT model_id, COUNT(*) FROM cache GROUP BY model_id")
        model_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM cache")
        time_range = cursor.fetchone()
        
        conn.close()
        
        return {
            "total_entries": count,
            "model_counts": model_counts,
            "oldest_entry": time_range[0] if time_range and time_range[0] else None,
            "newest_entry": time_range[1] if time_range and time_range[1] else None
        }


class KnowledgeBase:
    """Local knowledge base for offline use."""
    
    def __init__(self, data_dir: str = "data/knowledge"):
        """Initialize the knowledge base.
        
        Args:
            data_dir: Directory for storing knowledge base data
        """
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "knowledge_base.db")
        
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        logging.info(f"Knowledge base initialized at {self.db_path}")
    
    def _init_db(self) -> None:
        """Initialize the knowledge base database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            source TEXT,
            category TEXT,
            timestamp DATETIME,
            metadata TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS document_index USING fts5(
            title, content, source, category
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_document(self, title: str, content: str, source: str = None, 
                    category: str = None, metadata: Dict[str, Any] = None) -> int:
        """Add a document to the knowledge base.
        
        Args:
            title: Document title
            content: Document content
            source: Document source
            category: Document category
            metadata: Additional metadata
            
        Returns:
            Document ID
        """
        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert into documents table
        cursor.execute(
            "INSERT INTO documents (title, content, source, category, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?)",
            (title, content, source, category, timestamp, metadata_json)
        )
        
        # Get the document ID
        document_id = cursor.lastrowid
        
        # Insert into search index
        cursor.execute(
            "INSERT INTO document_index (rowid, title, content, source, category) VALUES (?, ?, ?, ?, ?)",
            (document_id, title, content, source or "", category or "")
        )
        
        conn.commit()
        conn.close()
        
        return document_id
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the knowledge base.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search the index
        cursor.execute(
            "SELECT rowid FROM document_index WHERE document_index MATCH ? LIMIT ?",
            (query, limit)
        )
        
        # Get document IDs
        document_ids = [row[0] for row in cursor.fetchall()]
        
        if not document_ids:
            conn.close()
            return []
        
        # Get document details
        placeholders = ", ".join(["?"] * len(document_ids))
        cursor.execute(
            f"SELECT id, title, content, source, category, timestamp, metadata FROM documents WHERE id IN ({placeholders})",
            document_ids
        )
        
        # Format results
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "source": row[3],
                "category": row[4],
                "timestamp": row[5],
                "metadata": json.loads(row[6]) if row[6] else {}
            })
        
        conn.close()
        
        return results
    
    def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, title, content, source, category, timestamp, metadata FROM documents WHERE id = ?",
            (document_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "source": row[3],
                "category": row[4],
                "timestamp": row[5],
                "metadata": json.loads(row[6]) if row[6] else {}
            }
        
        return None
    
    def update_document(self, document_id: int, title: str = None, content: str = None,
                       source: str = None, category: str = None, metadata: Dict[str, Any] = None) -> bool:
        """Update a document.
        
        Args:
            document_id: Document ID
            title: New title (or None to keep current)
            content: New content (or None to keep current)
            source: New source (or None to keep current)
            category: New category (or None to keep current)
            metadata: New metadata (or None to keep current)
            
        Returns:
            True if successful, False otherwise
        """
        # Get current document
        current = self.get_document(document_id)
        if not current:
            return False
        
        # Update fields
        new_title = title if title is not None else current["title"]
        new_content = content if content is not None else current["content"]
        new_source = source if source is not None else current["source"]
        new_category = category if category is not None else current["category"]
        new_metadata = metadata if metadata is not None else current["metadata"]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update documents table
        cursor.execute(
            "UPDATE documents SET title = ?, content = ?, source = ?, category = ?, metadata = ? WHERE id = ?",
            (new_title, new_content, new_source, new_category, json.dumps(new_metadata), document_id)
        )
        
        # Update search index
        cursor.execute(
            "DELETE FROM document_index WHERE rowid = ?",
            (document_id,)
        )
        
        cursor.execute(
            "INSERT INTO document_index (rowid, title, content, source, category) VALUES (?, ?, ?, ?, ?)",
            (document_id, new_title, new_content, new_source or "", new_category or "")
        )
        
        conn.commit()
        conn.close()
        
        return True
    
    def delete_document(self, document_id: int) -> bool:
        """Delete a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if document exists
        cursor.execute("SELECT id FROM documents WHERE id = ?", (document_id,))
        if not cursor.fetchone():
            conn.close()
            return False
        
        # Delete from documents table
        cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        
        # Delete from search index
        cursor.execute("DELETE FROM document_index WHERE rowid = ?", (document_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_categories(self) -> List[str]:
        """Get all categories.
        
        Returns:
            List of categories
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT category FROM documents WHERE category IS NOT NULL")
        
        categories = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        
        return categories
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics.
        
        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]
        
        cursor.execute("SELECT category, COUNT(*) FROM documents GROUP BY category")
        category_counts = {row[0] or "Uncategorized": row[1] for row in cursor.fetchall()}
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM documents")
        time_range = cursor.fetchone()
        
        conn.close()
        
        return {
            "total_documents": count,
            "category_counts": category_counts,
            "oldest_document": time_range[0] if time_range and time_range[0] else None,
            "newest_document": time_range[1] if time_range and time_range[1] else None
        }


class LocalModelManager:
    """Manages local models for offline use."""
    
    def __init__(self, models_dir: str = "data/models"):
        """Initialize the local model manager.
        
        Args:
            models_dir: Directory for storing local models
        """
        self.models_dir = models_dir
        
        # Create directory if it doesn't exist
        os.makedirs(models_dir, exist_ok=True)
        
        # Initialize available models
        self.available_models = self._scan_models()
        
        logging.info(f"Local model manager initialized with {len(self.available_models)} models")
    
    def _scan_models(self) -> Dict[str, Dict[str, Any]]:
        """Scan for available local models.
        
        Returns:
            Dictionary of model information
        """
        models = {}
        
        # Check for model directories
        for model_dir in os.listdir(self.models_dir):
            model_path = os.path.join(self.models_dir, model_dir)
            
            if not os.path.isdir(model_path):
                continue
            
            # Check for model metadata
            metadata_path = os.path.join(model_path, "metadata.json")
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    model_id = metadata.get("model_id", model_dir)
                    models[model_id] = {
                        "path": model_path,
                        "metadata": metadata
                    }
                except Exception as e:
                    logging.error(f"Error loading model metadata for {model_dir}: {e}")
        
        return models
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get information about available local models.
        
        Returns:
            List of model information
        """
        return [
            {
                "model_id": model_id,
                "name": info["metadata"].get("name", model_id),
                "description": info["metadata"].get("description", ""),
                "parameters": info["metadata"].get("parameters", 0),
                "context_window": info["metadata"].get("context_window", 0),
                "quantization": info["metadata"].get("quantization", ""),
                "license": info["metadata"].get("license", ""),
                "path": info["path"]
            }
            for model_id, info in self.available_models.items()
        ]
    
    def is_model_available(self, model_id: str) -> bool:
        """Check if a model is available locally.
        
        Args:
            model_id: Model identifier
            
        Returns:
            True if the model is available, False otherwise
        """
        return model_id in self.available_models
    
    def get_model_path(self, model_id: str) -> Optional[str]:
        """Get the path to a local model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Path to the model or None if not found
        """
        if model_id in self.available_models:
            return self.available_models[model_id]["path"]
        return None
    
    def get_model_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a local model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Model metadata or None if not found
        """
        if model_id in self.available_models:
            return self.available_models[model_id]["metadata"]
        return None


class OfflineManager:
    """Manages offline capabilities."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the offline manager.
        
        Args:
            data_dir: Base directory for offline data
        """
        self.data_dir = data_dir
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize components
        self.response_cache = ResponseCache(os.path.join(data_dir, "cache"))
        self.knowledge_base = KnowledgeBase(os.path.join(data_dir, "knowledge"))
        self.local_model_manager = LocalModelManager(os.path.join(data_dir, "models"))
        
        # Offline mode flag
        self.offline_mode = False
        
        logging.info("Offline Manager initialized")
    
    def set_offline_mode(self, enabled: bool) -> None:
        """Set offline mode.
        
        Args:
            enabled: Whether offline mode is enabled
        """
        self.offline_mode = enabled
        logging.info(f"Offline mode {'enabled' if enabled else 'disabled'}")
    
    def is_offline_mode(self) -> bool:
        """Check if offline mode is enabled.
        
        Returns:
            True if offline mode is enabled, False otherwise
        """
        return self.offline_mode
    
    def get_cached_response(self, query: str, model_id: str) -> Optional[str]:
        """Get a cached response.
        
        Args:
            query: Query string
            model_id: Model identifier
            
        Returns:
            Cached response or None if not found
        """
        cached = self.response_cache.get(query, model_id)
        if cached:
            return cached["response"]
        return None
    
    def cache_response(self, query: str, response: str, model_id: str, metadata: Dict[str, Any] = None) -> None:
        """Cache a response.
        
        Args:
            query: Query string
            response: Response string
            model_id: Model identifier
            metadata: Additional metadata
        """
        self.response_cache.put(query, response, model_id, metadata)
    
    def search_knowledge_base(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the knowledge base.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        return self.knowledge_base.search(query, limit)
    
    def add_to_knowledge_base(self, title: str, content: str, source: str = None,
                             category: str = None, metadata: Dict[str, Any] = None) -> int:
        """Add a document to the knowledge base.
        
        Args:
            title: Document title
            content: Document content
            source: Document source
            category: Document category
            metadata: Additional metadata
            
        Returns:
            Document ID
        """
        return self.knowledge_base.add_document(title, content, source, category, metadata)
    
    def get_available_local_models(self) -> List[Dict[str, Any]]:
        """Get information about available local models.
        
        Returns:
            List of model information
        """
        return self.local_model_manager.get_available_models()
    
    def is_model_available_locally(self, model_id: str) -> bool:
        """Check if a model is available locally.
        
        Args:
            model_id: Model identifier
            
        Returns:
            True if the model is available, False otherwise
        """
        return self.local_model_manager.is_model_available(model_id)
    
    def get_offline_status(self) -> Dict[str, Any]:
        """Get the status of offline capabilities.
        
        Returns:
            Dictionary with status information
        """
        cache_stats = self.response_cache.get_stats()
        kb_stats = self.knowledge_base.get_stats()
        local_models = self.local_model_manager.get_available_models()
        
        return {
            "offline_mode": self.offline_mode,
            "cache": {
                "total_entries": cache_stats["total_entries"],
                "model_counts": cache_stats["model_counts"]
            },
            "knowledge_base": {
                "total_documents": kb_stats["total_documents"],
                "categories": kb_stats["category_counts"]
            },
            "local_models": {
                "count": len(local_models),
                "models": [model["model_id"] for model in local_models]
            }
        }
