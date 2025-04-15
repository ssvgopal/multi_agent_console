"""
Caching Module for MultiAgentConsole.

This module provides caching capabilities for offline use.
"""

import os
import json
import logging
import hashlib
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path


class CacheEntry:
    """Represents a single cache entry."""

    def __init__(self, key: str, data: Any, ttl: int = 86400):
        """Initialize a cache entry.

        Args:
            key: Cache key
            data: Cached data
            ttl: Time to live in seconds (default: 24 hours)
        """
        self.key = key
        self.data = data
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl
        self.last_accessed = self.created_at
        self.access_count = 0

    def is_expired(self) -> bool:
        """Check if the cache entry is expired.

        Returns:
            True if expired, False otherwise
        """
        return time.time() > self.expires_at

    def access(self) -> None:
        """Update access statistics."""
        self.last_accessed = time.time()
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert the cache entry to a dictionary.

        Returns:
            Dictionary representation of the cache entry
        """
        return {
            "key": self.key,
            "data": self.data,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create a cache entry from a dictionary.

        Args:
            data: Dictionary representation of the cache entry

        Returns:
            CacheEntry instance
        """
        entry = cls(data["key"], data["data"])
        entry.created_at = data["created_at"]
        entry.expires_at = data["expires_at"]
        entry.last_accessed = data["last_accessed"]
        entry.access_count = data["access_count"]
        return entry


class CacheManager:
    """Manages cache entries."""

    def __init__(self, data_dir: str = "data/cache", max_size: int = 1000, ttl: int = 86400):
        """Initialize the cache manager.

        Args:
            data_dir: Directory for storing cache data
            max_size: Maximum number of cache entries
            ttl: Default time to live in seconds (default: 24 hours)
        """
        self.data_dir = data_dir
        self.max_size = max_size
        self.default_ttl = ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.metadata_file = os.path.join(data_dir, "metadata.json")

        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Load cache metadata
        self.load_metadata()

        logging.info(f"Cache Manager initialized with {len(self.cache)} entries")

    def load_metadata(self) -> None:
        """Load cache metadata from file."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, "r") as f:
                    metadata = json.load(f)
                    for key, entry_data in metadata.items():
                        self.cache[key] = CacheEntry.from_dict(entry_data)
                logging.info(f"Loaded {len(self.cache)} cache entries from {self.metadata_file}")
            except Exception as e:
                logging.error(f"Error loading cache metadata from {self.metadata_file}: {e}")
                self.cache = {}

    def save_metadata(self) -> None:
        """Save cache metadata to file."""
        try:
            metadata = {key: entry.to_dict() for key, entry in self.cache.items()}
            with open(self.metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            logging.info(f"Saved {len(self.cache)} cache entries to {self.metadata_file}")
        except Exception as e:
            logging.error(f"Error saving cache metadata to {self.metadata_file}: {e}")

    def generate_key(self, data: Any) -> str:
        """Generate a cache key from data.

        Args:
            data: Data to generate key from

        Returns:
            Cache key
        """
        # Convert data to string
        if isinstance(data, dict):
            # Sort dictionary keys for consistent hashing
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)

        # Generate hash
        return hashlib.md5(data_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found or expired
        """
        # Check if key exists
        if key not in self.cache:
            return None

        # Get cache entry
        entry = self.cache[key]

        # Check if expired
        if entry.is_expired():
            self.remove(key)
            return None

        # Update access statistics
        entry.access()

        return entry.data

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (default: use default TTL)
        """
        # Check if cache is full
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Remove least recently used entry
            self._remove_lru()

        # Set TTL
        if ttl is None:
            ttl = self.default_ttl

        # Create cache entry
        self.cache[key] = CacheEntry(key, data, ttl)

        # Save metadata
        self.save_metadata()

    def remove(self, key: str) -> bool:
        """Remove a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if removed, False if not found
        """
        if key in self.cache:
            del self.cache[key]
            self.save_metadata()
            return True
        return False

    def clear(self) -> None:
        """Clear the cache."""
        self.cache = {}
        self.save_metadata()

    def _remove_lru(self) -> None:
        """Remove the least recently used cache entry."""
        if not self.cache:
            return

        # Find least recently used entry
        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_accessed)
        self.remove(lru_key)

    def cleanup(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        # Find expired entries
        expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]

        # Remove expired entries
        for key in expired_keys:
            self.remove(key)

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics
        """
        return {
            "total_entries": len(self.cache),
            "max_size": self.max_size,
            "usage_percentage": len(self.cache) / self.max_size * 100 if self.max_size > 0 else 0,
            "expired_entries": sum(1 for entry in self.cache.values() if entry.is_expired()),
            "total_size_bytes": sum(len(json.dumps(entry.data)) for entry in self.cache.values()),
            "oldest_entry": min(entry.created_at for entry in self.cache.values()) if self.cache else None,
            "newest_entry": max(entry.created_at for entry in self.cache.values()) if self.cache else None,
            "most_accessed_key": max(self.cache.keys(), key=lambda k: self.cache[k].access_count) if self.cache else None,
            "most_accessed_count": max(entry.access_count for entry in self.cache.values()) if self.cache else 0
        }


class OfflineManager:
    """Manages offline capabilities."""

    def __init__(self, data_dir: str = "data/offline"):
        """Initialize the offline manager.

        Args:
            data_dir: Directory for storing offline data
        """
        self.data_dir = data_dir
        self.cache_manager = CacheManager(os.path.join(data_dir, "cache"))
        self.knowledge_base_dir = os.path.join(data_dir, "knowledge_base")
        self.offline_mode = False

        # Create directories if they don't exist
        os.makedirs(self.knowledge_base_dir, exist_ok=True)

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

    def cache_response(self, request: Any, response: Any) -> None:
        """Cache a response.

        Args:
            request: Request data
            response: Response data
        """
        key = self.cache_manager.generate_key(request)
        self.cache_manager.set(key, response)

    def get_cached_response(self, request: Any) -> Optional[Any]:
        """Get a cached response.

        Args:
            request: Request data

        Returns:
            Cached response or None if not found
        """
        key = self.cache_manager.generate_key(request)
        return self.cache_manager.get(key)

    def add_to_knowledge_base(self, topic: str, content: str) -> None:
        """Add content to the knowledge base.

        Args:
            topic: Topic name
            content: Content to add
        """
        # Create topic directory if it doesn't exist
        topic_dir = os.path.join(self.knowledge_base_dir, topic)
        os.makedirs(topic_dir, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}.txt"

        # Save content
        with open(os.path.join(topic_dir, filename), "w") as f:
            f.write(content)

        logging.info(f"Added content to knowledge base: {topic}/{filename}")

    def search_knowledge_base(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search the knowledge base.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of matching entries
        """
        results = []

        # Convert query to lowercase for case-insensitive search
        query = query.lower()

        # Search all files in knowledge base
        for topic_dir in os.listdir(self.knowledge_base_dir):
            topic_path = os.path.join(self.knowledge_base_dir, topic_dir)
            if not os.path.isdir(topic_path):
                continue

            for filename in os.listdir(topic_path):
                file_path = os.path.join(topic_path, filename)
                if not os.path.isfile(file_path) or not filename.endswith(".txt"):
                    continue

                try:
                    # Read file content
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Check if query matches
                    if query in content.lower():
                        # Extract timestamp from filename
                        timestamp = filename[:-4]  # Remove .txt extension
                        try:
                            date = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
                        except ValueError:
                            date = None

                        # Add to results
                        results.append({
                            "topic": topic_dir,
                            "filename": filename,
                            "date": date.isoformat() if date else None,
                            "content": content,
                            "path": file_path
                        })

                        # Check if we have enough results
                        if len(results) >= max_results:
                            break
                except Exception as e:
                    logging.error(f"Error reading knowledge base file {file_path}: {e}")

            # Check if we have enough results
            if len(results) >= max_results:
                break

        # Sort results by date (newest first)
        results.sort(key=lambda x: x["date"] if x["date"] else "", reverse=True)

        return results[:max_results]

    def get_knowledge_base_topics(self) -> List[Dict[str, Any]]:
        """Get all topics in the knowledge base.

        Returns:
            List of topics with metadata
        """
        topics = []

        for topic_dir in os.listdir(self.knowledge_base_dir):
            topic_path = os.path.join(self.knowledge_base_dir, topic_dir)
            if not os.path.isdir(topic_path):
                continue

            # Count files
            file_count = sum(1 for f in os.listdir(topic_path) if os.path.isfile(os.path.join(topic_path, f)) and f.endswith(".txt"))

            # Get latest file date
            latest_date = None
            for filename in os.listdir(topic_path):
                if not filename.endswith(".txt"):
                    continue

                # Extract timestamp from filename
                timestamp = filename[:-4]  # Remove .txt extension
                try:
                    date = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
                    if latest_date is None or date > latest_date:
                        latest_date = date
                except ValueError:
                    pass

            # Add to topics
            topics.append({
                "name": topic_dir,
                "file_count": file_count,
                "latest_date": latest_date.isoformat() if latest_date else None
            })

        # Sort topics by name
        topics.sort(key=lambda x: x["name"])

        return topics

    def get_topic_entries(self, topic: str) -> List[Dict[str, Any]]:
        """Get all entries for a topic.

        Args:
            topic: Topic name

        Returns:
            List of entries with metadata
        """
        entries = []

        topic_path = os.path.join(self.knowledge_base_dir, topic)
        if not os.path.isdir(topic_path):
            return entries

        for filename in os.listdir(topic_path):
            file_path = os.path.join(topic_path, filename)
            if not os.path.isfile(file_path) or not filename.endswith(".txt"):
                continue

            # Extract timestamp from filename
            timestamp = filename[:-4]  # Remove .txt extension
            try:
                date = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
            except ValueError:
                date = None

            # Get file size
            file_size = os.path.getsize(file_path)

            # Add to entries
            entries.append({
                "filename": filename,
                "date": date.isoformat() if date else None,
                "size_bytes": file_size,
                "path": file_path
            })

        # Sort entries by date (newest first)
        entries.sort(key=lambda x: x["date"] if x["date"] else "", reverse=True)

        return entries

    def get_entry_content(self, topic: str, filename: str) -> Optional[str]:
        """Get the content of an entry.

        Args:
            topic: Topic name
            filename: Filename

        Returns:
            Entry content or None if not found
        """
        file_path = os.path.join(self.knowledge_base_dir, topic, filename)
        if not os.path.isfile(file_path):
            return None

        try:
            with open(file_path, "r") as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error reading knowledge base file {file_path}: {e}")
            return None

    def delete_entry(self, topic: str, filename: str) -> bool:
        """Delete an entry.

        Args:
            topic: Topic name
            filename: Filename

        Returns:
            True if deleted, False otherwise
        """
        file_path = os.path.join(self.knowledge_base_dir, topic, filename)
        if not os.path.isfile(file_path):
            return False

        try:
            os.remove(file_path)
            logging.info(f"Deleted knowledge base entry: {topic}/{filename}")
            return True
        except Exception as e:
            logging.error(f"Error deleting knowledge base file {file_path}: {e}")
            return False

    def delete_topic(self, topic: str) -> bool:
        """Delete a topic and all its entries.

        Args:
            topic: Topic name

        Returns:
            True if deleted, False otherwise
        """
        topic_path = os.path.join(self.knowledge_base_dir, topic)
        if not os.path.isdir(topic_path):
            return False

        try:
            # Delete all files in the topic directory
            for filename in os.listdir(topic_path):
                file_path = os.path.join(topic_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

            # Delete the topic directory
            os.rmdir(topic_path)
            logging.info(f"Deleted knowledge base topic: {topic}")
            return True
        except Exception as e:
            logging.error(f"Error deleting knowledge base topic {topic}: {e}")
            return False
