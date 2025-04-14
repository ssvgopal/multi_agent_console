"""
Memory Manager for MultiAgentConsole.

This module provides enhanced memory and context management capabilities:
- Long-term memory storage for user preferences and past interactions
- Context-aware responses that reference previous conversations
- User-specific profiles with customized agent behaviors
- Ability to save and load specific conversation threads
"""

import json
import os
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import sqlite3
from pathlib import Path

from google.adk.sessions.session import Session
from google.adk.events.event import Event
from google.genai import types


class MemoryManager:
    """Enhanced memory management for MultiAgentConsole."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the memory manager.
        
        Args:
            data_dir: Directory to store memory data
        """
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "memory.db")
        self.user_profiles_path = os.path.join(data_dir, "user_profiles")
        self.conversation_path = os.path.join(data_dir, "conversations")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.user_profiles_path, exist_ok=True)
        os.makedirs(self.conversation_path, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Cache for frequently accessed data
        self._user_profile_cache = {}
        self._conversation_cache = {}
        
        logging.info(f"Memory Manager initialized with data directory: {data_dir}")
    
    def _init_database(self):
        """Initialize the SQLite database for memory storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            timestamp REAL NOT NULL,
            summary TEXT,
            tags TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp REAL NOT NULL,
            agent TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id TEXT PRIMARY KEY,
            preferences TEXT NOT NULL,
            last_updated REAL NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS semantic_index (
            id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL,
            embedding_file TEXT NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Database initialized")
    
    def save_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        """Save user profile data.
        
        Args:
            user_id: User identifier
            profile_data: Dictionary containing user profile information
        """
        profile_path = os.path.join(self.user_profiles_path, f"{user_id}.json")
        
        # Update timestamp
        profile_data["last_updated"] = time.time()
        
        with open(profile_path, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        # Update cache
        self._user_profile_cache[user_id] = profile_data
        
        # Also save to database for quick access
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR REPLACE INTO user_preferences (user_id, preferences, last_updated) VALUES (?, ?, ?)",
            (user_id, json.dumps(profile_data), time.time())
        )
        
        conn.commit()
        conn.close()
        logging.info(f"User profile saved for user: {user_id}")
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile data.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary containing user profile information
        """
        # Check cache first
        if user_id in self._user_profile_cache:
            return self._user_profile_cache[user_id]
        
        profile_path = os.path.join(self.user_profiles_path, f"{user_id}.json")
        
        # If profile exists, load it
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profile_data = json.load(f)
                self._user_profile_cache[user_id] = profile_data
                return profile_data
        
        # Otherwise, create a default profile
        default_profile = {
            "user_id": user_id,
            "created_at": time.time(),
            "last_updated": time.time(),
            "preferences": {
                "default_agent": "coordinator",
                "theme": "default",
                "model_preference": None
            },
            "topics_of_interest": [],
            "interaction_history": {
                "total_conversations": 0,
                "total_messages": 0,
                "frequent_topics": [],
                "last_conversation_id": None
            }
        }
        
        # Save the default profile
        self.save_user_profile(user_id, default_profile)
        return default_profile
    
    def update_user_preference(self, user_id: str, key: str, value: Any) -> None:
        """Update a specific user preference.
        
        Args:
            user_id: User identifier
            key: Preference key
            value: Preference value
        """
        profile = self.get_user_profile(user_id)
        profile["preferences"][key] = value
        profile["last_updated"] = time.time()
        self.save_user_profile(user_id, profile)
        logging.info(f"Updated preference '{key}' for user: {user_id}")
    
    def save_conversation(self, session: Session, title: Optional[str] = None, summary: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
        """Save a conversation from a session.
        
        Args:
            session: The session to save
            title: Optional title for the conversation
            summary: Optional summary of the conversation
            tags: Optional tags for the conversation
            
        Returns:
            Conversation ID
        """
        conversation_id = session.id
        user_id = session.user_id
        
        # Generate title if not provided
        if not title:
            title = f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Convert tags to JSON string if provided
        tags_str = json.dumps(tags) if tags else "[]"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Save conversation metadata
        cursor.execute(
            "INSERT OR REPLACE INTO conversations (id, user_id, title, timestamp, summary, tags) VALUES (?, ?, ?, ?, ?, ?)",
            (conversation_id, user_id, title, time.time(), summary or "", tags_str)
        )
        
        # Save messages
        for event in session.events:
            if event.content and event.content.parts:
                content = ''.join(part.text or '' for part in event.content.parts)
                if content:
                    message_id = event.id
                    cursor.execute(
                        "INSERT OR REPLACE INTO messages (id, conversation_id, role, content, timestamp, agent) VALUES (?, ?, ?, ?, ?, ?)",
                        (message_id, conversation_id, event.role if hasattr(event, 'role') else 'unknown', 
                         content, event.timestamp, event.author)
                    )
        
        conn.commit()
        conn.close()
        
        # Update user profile
        profile = self.get_user_profile(user_id)
        profile["interaction_history"]["total_conversations"] += 1
        profile["interaction_history"]["total_messages"] += len(session.events)
        profile["interaction_history"]["last_conversation_id"] = conversation_id
        self.save_user_profile(user_id, profile)
        
        logging.info(f"Saved conversation {conversation_id} for user {user_id}")
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Get a conversation by ID.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Dictionary containing conversation data
        """
        # Check cache first
        if conversation_id in self._conversation_cache:
            return self._conversation_cache[conversation_id]
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get conversation metadata
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        conversation_row = cursor.fetchone()
        
        if not conversation_row:
            conn.close()
            return None
        
        conversation = dict(conversation_row)
        
        # Get messages
        cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp", (conversation_id,))
        messages = [dict(row) for row in cursor.fetchall()]
        
        conversation["messages"] = messages
        
        conn.close()
        
        # Update cache
        self._conversation_cache[conversation_id] = conversation
        
        return conversation
    
    def list_conversations(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """List conversations for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of conversations to return
            offset: Offset for pagination
            
        Returns:
            List of conversation metadata
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset)
        )
        
        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return conversations
    
    def search_conversations(self, user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search conversations for a user.
        
        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching conversations
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Simple text search for now
        cursor.execute(
            """
            SELECT DISTINCT c.* 
            FROM conversations c
            JOIN messages m ON c.id = m.conversation_id
            WHERE c.user_id = ? AND (
                c.title LIKE ? OR
                c.summary LIKE ? OR
                m.content LIKE ?
            )
            ORDER BY c.timestamp DESC
            LIMIT ?
            """,
            (user_id, f"%{query}%", f"%{query}%", f"%{query}%", limit)
        )
        
        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return conversations
    
    def get_conversation_context(self, user_id: str, current_query: str, max_messages: int = 5) -> List[Dict[str, Any]]:
        """Get relevant context from past conversations.
        
        Args:
            user_id: User identifier
            current_query: Current user query
            max_messages: Maximum number of messages to include in context
            
        Returns:
            List of relevant messages as context
        """
        # For now, implement a simple keyword-based retrieval
        # In a future implementation, this would use embeddings and semantic search
        
        keywords = set(current_query.lower().split())
        relevant_messages = []
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get recent conversations
        cursor.execute(
            "SELECT id FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10",
            (user_id,)
        )
        
        conversation_ids = [row['id'] for row in cursor.fetchall()]
        
        # Search for relevant messages in these conversations
        for conv_id in conversation_ids:
            cursor.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp DESC",
                (conv_id,)
            )
            
            messages = [dict(row) for row in cursor.fetchall()]
            
            for message in messages:
                message_text = message['content'].lower()
                if any(keyword in message_text for keyword in keywords):
                    relevant_messages.append(message)
                    if len(relevant_messages) >= max_messages:
                        break
            
            if len(relevant_messages) >= max_messages:
                break
        
        conn.close()
        
        return relevant_messages
    
    def update_session_with_context(self, session: Session, context_messages: List[Dict[str, Any]]) -> None:
        """Update session state with context from previous conversations.
        
        Args:
            session: Current session
            context_messages: List of context messages
        """
        if not context_messages:
            return
        
        # Add context to session state
        if 'context' not in session.state:
            session.state['context'] = []
        
        for message in context_messages:
            context_entry = {
                'role': message['role'],
                'content': message['content'],
                'agent': message['agent'],
                'timestamp': message['timestamp']
            }
            session.state['context'].append(context_entry)
        
        logging.info(f"Added {len(context_messages)} context messages to session {session.id}")
    
    def extract_user_interests(self, user_id: str) -> List[str]:
        """Extract topics of interest from user's conversation history.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of topics of interest
        """
        # This is a placeholder for more sophisticated topic extraction
        # In a real implementation, this would use NLP techniques
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all user messages
        cursor.execute(
            """
            SELECT m.content
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = ? AND m.role = 'user'
            ORDER BY m.timestamp DESC
            LIMIT 100
            """,
            (user_id,)
        )
        
        messages = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Simple keyword extraction
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "about", "is", "are", "was", "were"}
        word_counts = {}
        
        for message in messages:
            words = message.lower().split()
            for word in words:
                if word not in common_words and len(word) > 3:
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get top words
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        topics = [word for word, count in sorted_words[:10]]
        
        return topics
    
    def update_user_interests(self, user_id: str) -> None:
        """Update user's topics of interest based on conversation history.
        
        Args:
            user_id: User identifier
        """
        topics = self.extract_user_interests(user_id)
        
        profile = self.get_user_profile(user_id)
        profile["topics_of_interest"] = topics
        self.save_user_profile(user_id, profile)
        
        logging.info(f"Updated topics of interest for user {user_id}: {topics}")
    
    def create_session_from_conversation(self, conversation_id: str, app_name: str) -> Session:
        """Create a new session from a saved conversation.
        
        Args:
            conversation_id: Conversation identifier
            app_name: Application name
            
        Returns:
            New session with conversation history
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        # Create new session
        session = Session(
            id=f"{conversation_id}_restored_{int(time.time())}",
            app_name=app_name,
            user_id=conversation["user_id"],
            state={"restored_from": conversation_id},
            events=[]
        )
        
        # Convert messages to events
        for message in conversation["messages"]:
            content = types.Content(
                role=message["role"],
                parts=[types.Part(text=message["content"])]
            )
            
            event = Event(
                id=message["id"],
                author=message["agent"] or "unknown",
                timestamp=message["timestamp"],
                content=content
            )
            
            session.events.append(event)
        
        logging.info(f"Created session from conversation {conversation_id}")
        return session
    
    def get_agent_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user's agent preferences.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of agent preferences
        """
        profile = self.get_user_profile(user_id)
        
        # Extract agent-specific preferences
        agent_prefs = {}
        
        # Default agent
        agent_prefs["default_agent"] = profile["preferences"].get("default_agent", "coordinator")
        
        # Agent-specific instructions
        agent_prefs["custom_instructions"] = profile["preferences"].get("custom_instructions", {})
        
        # Model preferences
        agent_prefs["model_preference"] = profile["preferences"].get("model_preference")
        
        return agent_prefs
    
    def close(self):
        """Close the memory manager and save any pending data."""
        # Save any cached data that might need persisting
        for user_id, profile in self._user_profile_cache.items():
            profile_path = os.path.join(self.user_profiles_path, f"{user_id}.json")
            with open(profile_path, 'w') as f:
                json.dump(profile, f, indent=2)
        
        logging.info("Memory Manager closed")


class ContextEnhancer:
    """Enhances agent responses with contextual information."""
    
    def __init__(self, memory_manager: MemoryManager):
        """Initialize the context enhancer.
        
        Args:
            memory_manager: Memory manager instance
        """
        self.memory_manager = memory_manager
    
    def enhance_prompt(self, user_id: str, prompt: str, session: Session) -> str:
        """Enhance user prompt with contextual information.
        
        Args:
            user_id: User identifier
            prompt: Original user prompt
            session: Current session
            
        Returns:
            Enhanced prompt with context
        """
        # Get relevant context
        context_messages = self.memory_manager.get_conversation_context(user_id, prompt)
        
        # Update session with context
        self.memory_manager.update_session_with_context(session, context_messages)
        
        # If no context, return original prompt
        if not context_messages:
            return prompt
        
        # Create enhanced prompt with context
        enhanced_prompt = f"{prompt}\n\nContext from previous conversations:\n"
        
        for i, message in enumerate(context_messages):
            enhanced_prompt += f"[{i+1}] {message['agent']}: {message['content']}\n"
        
        enhanced_prompt += "\nPlease consider this context in your response."
        
        return enhanced_prompt
    
    def get_personalization_info(self, user_id: str) -> str:
        """Get personalization information for the user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Personalization information as a string
        """
        profile = self.memory_manager.get_user_profile(user_id)
        
        # Extract relevant personalization info
        interests = profile.get("topics_of_interest", [])
        interaction_history = profile.get("interaction_history", {})
        
        personalization = "User Information:\n"
        
        if interests:
            personalization += f"Topics of interest: {', '.join(interests)}\n"
        
        if interaction_history:
            total_convs = interaction_history.get("total_conversations", 0)
            personalization += f"Previous interactions: {total_convs} conversations\n"
        
        return personalization
    
    def create_agent_instructions(self, user_id: str, agent_name: str, base_instructions: str) -> str:
        """Create personalized instructions for an agent.
        
        Args:
            user_id: User identifier
            agent_name: Name of the agent
            base_instructions: Base instructions for the agent
            
        Returns:
            Personalized instructions
        """
        agent_prefs = self.memory_manager.get_agent_preferences(user_id)
        
        # Get custom instructions for this agent if available
        custom_instructions = agent_prefs.get("custom_instructions", {}).get(agent_name)
        
        if custom_instructions:
            # Combine base and custom instructions
            instructions = f"{base_instructions}\n\n{custom_instructions}"
        else:
            instructions = base_instructions
        
        # Add personalization
        personalization = self.get_personalization_info(user_id)
        if personalization:
            instructions = f"{instructions}\n\n{personalization}"
        
        return instructions
