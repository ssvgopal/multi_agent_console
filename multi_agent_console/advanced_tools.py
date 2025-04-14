"""
Advanced Tool Integration for MultiAgentConsole.

This module provides enhanced tool capabilities:
- Integration with version control systems (Git)
- Database connection and query tools
- API integration tools for connecting to external services
- Image and document processing capabilities
- Voice input/output support
"""

import os
import subprocess
import json
import base64
import logging
import sqlite3
import tempfile
import requests
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import io
import re

# Try to import optional dependencies
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    import pyttsx3
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

try:
    import pymysql
    import psycopg2
    import sqlalchemy
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


class GitTools:
    """Tools for interacting with Git repositories."""
    
    def __init__(self, repo_path: Optional[str] = None):
        """Initialize Git tools.
        
        Args:
            repo_path: Path to the Git repository (default: current directory)
        """
        self.repo_path = repo_path or os.getcwd()
        self.available = GIT_AVAILABLE
        
        if not self.available:
            logging.warning("GitPython is not installed. Git tools will not be available.")
            return
        
        try:
            self.repo = git.Repo(self.repo_path)
            logging.info(f"Git repository found at {self.repo_path}")
        except git.InvalidGitRepositoryError:
            logging.warning(f"No Git repository found at {self.repo_path}")
            self.repo = None
    
    def git_status(self) -> str:
        """Get the status of the Git repository.
        
        Returns:
            Status information as a string
        """
        if not self.available or not self.repo:
            return "Git is not available or no repository found."
        
        try:
            # Get branch info
            branch = self.repo.active_branch.name
            
            # Get status
            changed_files = [item.a_path for item in self.repo.index.diff(None)]
            staged_files = [item.a_path for item in self.repo.index.diff('HEAD')]
            untracked_files = self.repo.untracked_files
            
            # Format the output
            output = f"Current branch: {branch}\n\n"
            
            if changed_files:
                output += "Changed files:\n"
                for file in changed_files:
                    output += f"  - {file}\n"
                output += "\n"
            
            if staged_files:
                output += "Staged files:\n"
                for file in staged_files:
                    output += f"  - {file}\n"
                output += "\n"
            
            if untracked_files:
                output += "Untracked files:\n"
                for file in untracked_files:
                    output += f"  - {file}\n"
                output += "\n"
            
            if not changed_files and not staged_files and not untracked_files:
                output += "Working tree clean\n"
            
            return output
        except Exception as e:
            logging.exception("Error getting Git status")
            return f"Error getting Git status: {str(e)}"
    
    def git_log(self, max_count: int = 5) -> str:
        """Get the commit history of the Git repository.
        
        Args:
            max_count: Maximum number of commits to show
            
        Returns:
            Commit history as a string
        """
        if not self.available or not self.repo:
            return "Git is not available or no repository found."
        
        try:
            # Get commit history
            commits = list(self.repo.iter_commits('HEAD', max_count=max_count))
            
            # Format the output
            output = f"Last {len(commits)} commits:\n\n"
            
            for commit in commits:
                date = commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S')
                output += f"Commit: {commit.hexsha[:7]}\n"
                output += f"Author: {commit.author.name} <{commit.author.email}>\n"
                output += f"Date:   {date}\n"
                output += f"\n    {commit.message.strip()}\n\n"
            
            return output
        except Exception as e:
            logging.exception("Error getting Git log")
            return f"Error getting Git log: {str(e)}"
    
    def git_diff(self, file_path: Optional[str] = None) -> str:
        """Get the diff of the specified file or all files.
        
        Args:
            file_path: Path to the file to diff (default: all files)
            
        Returns:
            Diff as a string
        """
        if not self.available or not self.repo:
            return "Git is not available or no repository found."
        
        try:
            if file_path:
                # Get diff for a specific file
                diff = self.repo.git.diff('HEAD', file_path)
            else:
                # Get diff for all files
                diff = self.repo.git.diff('HEAD')
            
            return diff if diff else "No changes"
        except Exception as e:
            logging.exception("Error getting Git diff")
            return f"Error getting Git diff: {str(e)}"
    
    def git_commit(self, message: str) -> str:
        """Commit changes to the Git repository.
        
        Args:
            message: Commit message
            
        Returns:
            Result of the commit operation as a string
        """
        if not self.available or not self.repo:
            return "Git is not available or no repository found."
        
        try:
            # Check if there are any changes to commit
            if not self.repo.is_dirty() and not self.repo.untracked_files:
                return "No changes to commit"
            
            # Add all changes
            self.repo.git.add('.')
            
            # Commit changes
            self.repo.index.commit(message)
            
            return f"Changes committed with message: {message}"
        except Exception as e:
            logging.exception("Error committing changes")
            return f"Error committing changes: {str(e)}"
    
    def git_push(self) -> str:
        """Push changes to the remote repository.
        
        Returns:
            Result of the push operation as a string
        """
        if not self.available or not self.repo:
            return "Git is not available or no repository found."
        
        try:
            # Check if there's a remote
            if not self.repo.remotes:
                return "No remote repository configured"
            
            # Push changes
            origin = self.repo.remotes.origin
            push_info = origin.push()
            
            # Check if push was successful
            if push_info[0].flags & push_info[0].ERROR:
                return f"Error pushing changes: {push_info[0].summary}"
            
            return "Changes pushed to remote repository"
        except Exception as e:
            logging.exception("Error pushing changes")
            return f"Error pushing changes: {str(e)}"


class DatabaseTools:
    """Tools for interacting with databases."""
    
    def __init__(self):
        """Initialize database tools."""
        self.available = DB_AVAILABLE
        self.connections = {}
        
        if not self.available:
            logging.warning("Database libraries are not installed. Database tools will not be available.")
    
    def connect_sqlite(self, db_path: str) -> str:
        """Connect to a SQLite database.
        
        Args:
            db_path: Path to the SQLite database file
            
        Returns:
            Connection ID or error message
        """
        if not self.available:
            return "Database tools are not available."
        
        try:
            # Generate a connection ID
            conn_id = f"sqlite_{len(self.connections) + 1}"
            
            # Connect to the database
            conn = sqlite3.connect(db_path)
            
            # Store the connection
            self.connections[conn_id] = {
                'type': 'sqlite',
                'path': db_path,
                'connection': conn
            }
            
            return f"Connected to SQLite database at {db_path} with ID: {conn_id}"
        except Exception as e:
            logging.exception(f"Error connecting to SQLite database at {db_path}")
            return f"Error connecting to SQLite database: {str(e)}"
    
    def connect_mysql(self, host: str, user: str, password: str, database: str, port: int = 3306) -> str:
        """Connect to a MySQL database.
        
        Args:
            host: Database host
            user: Database user
            password: Database password
            database: Database name
            port: Database port (default: 3306)
            
        Returns:
            Connection ID or error message
        """
        if not self.available:
            return "Database tools are not available."
        
        try:
            # Generate a connection ID
            conn_id = f"mysql_{len(self.connections) + 1}"
            
            # Connect to the database
            conn = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port
            )
            
            # Store the connection
            self.connections[conn_id] = {
                'type': 'mysql',
                'host': host,
                'user': user,
                'database': database,
                'port': port,
                'connection': conn
            }
            
            return f"Connected to MySQL database {database} at {host}:{port} with ID: {conn_id}"
        except Exception as e:
            logging.exception(f"Error connecting to MySQL database {database} at {host}:{port}")
            return f"Error connecting to MySQL database: {str(e)}"
    
    def connect_postgres(self, host: str, user: str, password: str, database: str, port: int = 5432) -> str:
        """Connect to a PostgreSQL database.
        
        Args:
            host: Database host
            user: Database user
            password: Database password
            database: Database name
            port: Database port (default: 5432)
            
        Returns:
            Connection ID or error message
        """
        if not self.available:
            return "Database tools are not available."
        
        try:
            # Generate a connection ID
            conn_id = f"postgres_{len(self.connections) + 1}"
            
            # Connect to the database
            conn = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                dbname=database,
                port=port
            )
            
            # Store the connection
            self.connections[conn_id] = {
                'type': 'postgres',
                'host': host,
                'user': user,
                'database': database,
                'port': port,
                'connection': conn
            }
            
            return f"Connected to PostgreSQL database {database} at {host}:{port} with ID: {conn_id}"
        except Exception as e:
            logging.exception(f"Error connecting to PostgreSQL database {database} at {host}:{port}")
            return f"Error connecting to PostgreSQL database: {str(e)}"
    
    def execute_query(self, conn_id: str, query: str) -> str:
        """Execute a SQL query on the specified database connection.
        
        Args:
            conn_id: Connection ID
            query: SQL query to execute
            
        Returns:
            Query results as a string
        """
        if not self.available:
            return "Database tools are not available."
        
        if conn_id not in self.connections:
            return f"Connection ID {conn_id} not found."
        
        try:
            conn_info = self.connections[conn_id]
            conn = conn_info['connection']
            
            # Execute the query
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Check if the query is a SELECT query
            if query.strip().upper().startswith('SELECT'):
                # Fetch the results
                results = cursor.fetchall()
                
                # Get column names
                column_names = [desc[0] for desc in cursor.description]
                
                # Format the output
                output = "Query results:\n\n"
                
                # Add column headers
                output += " | ".join(column_names) + "\n"
                output += "-" * (sum(len(name) for name in column_names) + 3 * (len(column_names) - 1)) + "\n"
                
                # Add rows
                for row in results:
                    output += " | ".join(str(value) for value in row) + "\n"
                
                output += f"\n{len(results)} rows returned"
                
                return output
            else:
                # For non-SELECT queries, commit the changes
                conn.commit()
                
                return f"Query executed successfully. {cursor.rowcount} rows affected."
        except Exception as e:
            logging.exception(f"Error executing query on connection {conn_id}")
            return f"Error executing query: {str(e)}"
    
    def list_tables(self, conn_id: str) -> str:
        """List tables in the specified database connection.
        
        Args:
            conn_id: Connection ID
            
        Returns:
            List of tables as a string
        """
        if not self.available:
            return "Database tools are not available."
        
        if conn_id not in self.connections:
            return f"Connection ID {conn_id} not found."
        
        try:
            conn_info = self.connections[conn_id]
            conn = conn_info['connection']
            db_type = conn_info['type']
            
            # Execute the appropriate query based on the database type
            cursor = conn.cursor()
            
            if db_type == 'sqlite':
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            elif db_type == 'mysql':
                cursor.execute("SHOW TABLES")
            elif db_type == 'postgres':
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            
            # Fetch the results
            tables = [row[0] for row in cursor.fetchall()]
            
            # Format the output
            output = f"Tables in {conn_id}:\n\n"
            
            for table in tables:
                output += f"- {table}\n"
            
            return output
        except Exception as e:
            logging.exception(f"Error listing tables on connection {conn_id}")
            return f"Error listing tables: {str(e)}"
    
    def close_connection(self, conn_id: str) -> str:
        """Close the specified database connection.
        
        Args:
            conn_id: Connection ID
            
        Returns:
            Result of the close operation as a string
        """
        if not self.available:
            return "Database tools are not available."
        
        if conn_id not in self.connections:
            return f"Connection ID {conn_id} not found."
        
        try:
            conn_info = self.connections[conn_id]
            conn = conn_info['connection']
            
            # Close the connection
            conn.close()
            
            # Remove the connection from the dictionary
            del self.connections[conn_id]
            
            return f"Connection {conn_id} closed."
        except Exception as e:
            logging.exception(f"Error closing connection {conn_id}")
            return f"Error closing connection: {str(e)}"


class ApiTools:
    """Tools for interacting with external APIs."""
    
    def __init__(self):
        """Initialize API tools."""
        self.api_keys = {}
    
    def set_api_key(self, service: str, api_key: str) -> str:
        """Set an API key for a service.
        
        Args:
            service: Service name
            api_key: API key
            
        Returns:
            Confirmation message
        """
        self.api_keys[service] = api_key
        return f"API key set for {service}"
    
    def http_request(self, url: str, method: str = 'GET', headers: Optional[Dict[str, str]] = None,
                    params: Optional[Dict[str, str]] = None, data: Optional[Dict[str, Any]] = None,
                    auth_service: Optional[str] = None) -> str:
        """Make an HTTP request to an external API.
        
        Args:
            url: URL to request
            method: HTTP method (default: GET)
            headers: HTTP headers
            params: Query parameters
            data: Request body data
            auth_service: Service name to use for authentication
            
        Returns:
            Response as a string
        """
        try:
            # Prepare headers
            request_headers = headers or {}
            
            # Add authentication if specified
            if auth_service and auth_service in self.api_keys:
                request_headers['Authorization'] = f"Bearer {self.api_keys[auth_service]}"
            
            # Make the request
            response = requests.request(
                method=method,
                url=url,
                headers=request_headers,
                params=params,
                json=data
            )
            
            # Check if the response is JSON
            try:
                json_response = response.json()
                return json.dumps(json_response, indent=2)
            except ValueError:
                return response.text
        except Exception as e:
            logging.exception(f"Error making HTTP request to {url}")
            return f"Error making HTTP request: {str(e)}"
    
    def weather_api(self, location: str) -> str:
        """Get weather information for a location.
        
        Args:
            location: Location name or coordinates
            
        Returns:
            Weather information as a string
        """
        try:
            # Check if we have an API key for OpenWeatherMap
            if 'openweathermap' not in self.api_keys:
                return "OpenWeatherMap API key not set. Use set_api_key('openweathermap', 'your_api_key') to set it."
            
            # Make the request
            api_key = self.api_keys['openweathermap']
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': location,
                'appid': api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            # Format the output
            if 'main' in data and 'weather' in data:
                weather = data['weather'][0]['description']
                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                humidity = data['main']['humidity']
                wind_speed = data['wind']['speed']
                
                output = f"Weather in {location}:\n\n"
                output += f"Condition: {weather}\n"
                output += f"Temperature: {temp}°C\n"
                output += f"Feels like: {feels_like}°C\n"
                output += f"Humidity: {humidity}%\n"
                output += f"Wind speed: {wind_speed} m/s\n"
                
                return output
            else:
                return f"Error getting weather information: {data.get('message', 'Unknown error')}"
        except Exception as e:
            logging.exception(f"Error getting weather information for {location}")
            return f"Error getting weather information: {str(e)}"
    
    def news_api(self, query: Optional[str] = None, category: Optional[str] = None, country: str = 'us') -> str:
        """Get news articles.
        
        Args:
            query: Search query
            category: News category
            country: Country code (default: us)
            
        Returns:
            News articles as a string
        """
        try:
            # Check if we have an API key for NewsAPI
            if 'newsapi' not in self.api_keys:
                return "NewsAPI API key not set. Use set_api_key('newsapi', 'your_api_key') to set it."
            
            # Make the request
            api_key = self.api_keys['newsapi']
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'apiKey': api_key,
                'country': country
            }
            
            if query:
                params['q'] = query
            
            if category:
                params['category'] = category
            
            response = requests.get(url, params=params)
            data = response.json()
            
            # Format the output
            if data['status'] == 'ok':
                articles = data['articles']
                
                output = f"News articles"
                if query:
                    output += f" for '{query}'"
                if category:
                    output += f" in category '{category}'"
                output += f" from {country.upper()}:\n\n"
                
                for i, article in enumerate(articles[:5], 1):
                    output += f"{i}. {article['title']}\n"
                    output += f"   Source: {article['source']['name']}\n"
                    output += f"   URL: {article['url']}\n"
                    output += f"   Published: {article['publishedAt']}\n\n"
                
                output += f"Total articles: {len(articles)}"
                
                return output
            else:
                return f"Error getting news articles: {data.get('message', 'Unknown error')}"
        except Exception as e:
            logging.exception("Error getting news articles")
            return f"Error getting news articles: {str(e)}"


class MediaTools:
    """Tools for processing images and documents."""
    
    def __init__(self):
        """Initialize media tools."""
        self.ocr_available = OCR_AVAILABLE
        
        if not self.ocr_available:
            logging.warning("OCR libraries are not installed. OCR tools will not be available.")
    
    def ocr_image(self, image_path: str) -> str:
        """Extract text from an image using OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text as a string
        """
        if not self.ocr_available:
            return "OCR tools are not available."
        
        try:
            # Open the image
            image = Image.open(image_path)
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            return text if text.strip() else "No text found in the image."
        except Exception as e:
            logging.exception(f"Error extracting text from image {image_path}")
            return f"Error extracting text from image: {str(e)}"
    
    def image_info(self, image_path: str) -> str:
        """Get information about an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Image information as a string
        """
        try:
            # Open the image
            image = Image.open(image_path)
            
            # Get image information
            width, height = image.size
            format_name = image.format
            mode = image.mode
            
            # Format the output
            output = f"Image information for {image_path}:\n\n"
            output += f"Format: {format_name}\n"
            output += f"Size: {width} x {height} pixels\n"
            output += f"Mode: {mode}\n"
            
            return output
        except Exception as e:
            logging.exception(f"Error getting image information for {image_path}")
            return f"Error getting image information: {str(e)}"
    
    def resize_image(self, image_path: str, width: int, height: int, output_path: Optional[str] = None) -> str:
        """Resize an image.
        
        Args:
            image_path: Path to the image file
            width: New width
            height: New height
            output_path: Path to save the resized image (default: overwrite original)
            
        Returns:
            Result of the resize operation as a string
        """
        try:
            # Open the image
            image = Image.open(image_path)
            
            # Resize the image
            resized_image = image.resize((width, height))
            
            # Save the resized image
            if output_path:
                resized_image.save(output_path)
                return f"Image resized and saved to {output_path}"
            else:
                resized_image.save(image_path)
                return f"Image resized and saved to {image_path}"
        except Exception as e:
            logging.exception(f"Error resizing image {image_path}")
            return f"Error resizing image: {str(e)}"


class VoiceTools:
    """Tools for voice input and output."""
    
    def __init__(self):
        """Initialize voice tools."""
        self.available = VOICE_AVAILABLE
        
        if not self.available:
            logging.warning("Voice libraries are not installed. Voice tools will not be available.")
            return
        
        try:
            # Initialize text-to-speech engine
            self.tts_engine = pyttsx3.init()
            
            # Initialize speech recognition
            self.recognizer = sr.Recognizer()
            
            logging.info("Voice tools initialized")
        except Exception as e:
            logging.exception("Error initializing voice tools")
            self.available = False
    
    def text_to_speech(self, text: str) -> str:
        """Convert text to speech.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Result of the text-to-speech operation as a string
        """
        if not self.available:
            return "Voice tools are not available."
        
        try:
            # Speak the text
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            
            return "Text spoken successfully"
        except Exception as e:
            logging.exception("Error converting text to speech")
            return f"Error converting text to speech: {str(e)}"
    
    def speech_to_text(self, timeout: int = 5) -> str:
        """Convert speech to text.
        
        Args:
            timeout: Maximum time to listen for speech in seconds
            
        Returns:
            Recognized text as a string
        """
        if not self.available:
            return "Voice tools are not available."
        
        try:
            # Use the default microphone as the audio source
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source)
                
                # Listen for speech
                print(f"Listening for {timeout} seconds...")
                audio = self.recognizer.listen(source, timeout=timeout)
                
                # Recognize speech using Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                
                return f"Recognized text: {text}"
        except sr.WaitTimeoutError:
            return "No speech detected within the timeout period."
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            return f"Error with the speech recognition service: {str(e)}"
        except Exception as e:
            logging.exception("Error converting speech to text")
            return f"Error converting speech to text: {str(e)}"


class AdvancedToolManager:
    """Manager for all advanced tools."""
    
    def __init__(self):
        """Initialize the advanced tool manager."""
        self.git_tools = GitTools()
        self.db_tools = DatabaseTools()
        self.api_tools = ApiTools()
        self.media_tools = MediaTools()
        self.voice_tools = VoiceTools()
        
        logging.info("Advanced Tool Manager initialized")
    
    def get_tool_status(self) -> str:
        """Get the status of all tools.
        
        Returns:
            Tool status information as a string
        """
        output = "Advanced Tool Status:\n\n"
        
        # Git tools
        output += "Git Tools: "
        output += "Available" if self.git_tools.available else "Not available (install GitPython)"
        output += "\n"
        
        # Database tools
        output += "Database Tools: "
        output += "Available" if self.db_tools.available else "Not available (install pymysql, psycopg2, sqlalchemy)"
        output += "\n"
        
        # OCR tools
        output += "OCR Tools: "
        output += "Available" if self.media_tools.ocr_available else "Not available (install Pillow, pytesseract)"
        output += "\n"
        
        # Voice tools
        output += "Voice Tools: "
        output += "Available" if self.voice_tools.available else "Not available (install pyttsx3, SpeechRecognition)"
        output += "\n"
        
        return output
