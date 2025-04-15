"""
MultiAgentConsole - A terminal-based multi-agent system powered by Google's ADK.

Author: Sai Sunkara
Copyright 2025 Sai Sunkara
License: MIT
"""

import json
import logging
import os
import platform
import subprocess
import uuid
import argparse
import secrets
from datetime import datetime
from logging import FileHandler
import asyncio
from typing import Dict, List, Optional, Any, Union

from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import Header, Input, Footer, Markdown, Button, Label, Select, ListView, ListItem
from textual.containers import VerticalScroll, Horizontal, Container
from textual.binding import Binding

from google.adk.agents import Agent, LlmAgent
from google.adk.tools import google_search, FunctionTool
from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.sessions.session import Session
from google.genai import types

# Import our custom modules
from .memory_manager import MemoryManager, ContextEnhancer
from .advanced_tools import AdvancedToolManager, GitTools, DatabaseTools, ApiTools, MediaTools, VoiceTools
from .security_manager import SecurityManager, PermissionManager, CodeSandbox, CredentialManager
from .ui_enhancements import UIEnhancementManager, ThemeManager, SyntaxHighlighter, ProgressIndicator, AutoCompleter
from .multi_modal import MultiModalManager, ImageProcessor, AudioProcessor, ChartGenerator, DocumentProcessor
from .workflow import WorkflowManager, Workflow, WorkflowStep, WorkflowTemplate, ScheduledTask, BatchProcessor
from .offline import OfflineManager, ResponseCache, KnowledgeBase, LocalModelManager
from .debugging import DebuggingManager, PerformanceMonitor, ErrorTracker, LogEnhancer, DebugTools
from .marketplace import MarketplaceManager, AgentDefinition, PluginDefinition
from .cross_platform import CrossPlatformManager, PlatformDetector, CloudSyncManager, AccessibilityManager, MobileOptimizer
from .mcp_server import MCPServer, MCPPluginManager, MCPAgent, MCPMessage, MCPPlugin
from .plugins.logger_plugin import LoggerPlugin
from .thought_graph import ThoughtGraphManager, ThoughtGraphAnalyzer
from .plugins.graph_analysis_plugin import GraphAnalysisPlugin, InfraNodusPlugin, SimpleGraphPlugin
from .a2a_adapter import A2AAdapter, A2ATextArtifact, A2AFileArtifact, A2ADataArtifact
from .plugins.a2a_plugin import A2APlugin
from .web_server import WebServer
from .optimization import setup_optimization, get_optimization_stats, cached, memoize, optimize_function, batch_process, parallel_process
from .security_enhancements import InputValidator, OutputSanitizer, setup_security

# Define default system prompts for different agents
COORDINATOR_PROMPT = """You are the coordinator for MultiAgentConsole.
Your job is to understand user requests and delegate to the appropriate specialized agent.
Only delegate when appropriate - you can handle simple requests yourself.
Always introduce the specialized agent when delegating a task."""

CODE_ASSISTANT_PROMPT = """You are a coding expert specialized in helping users write, debug, and understand code.
Focus on providing clear, efficient, and well-documented code examples.
Explain your code thoroughly and suggest best practices."""

RESEARCH_ASSISTANT_PROMPT = """You are a research assistant specialized in finding and synthesizing information.
Use search tools when needed to provide accurate and up-to-date information.
Always cite your sources and provide balanced perspectives."""

SYSTEM_ASSISTANT_PROMPT = """You are a system administration expert specialized in helping users manage their computer systems.
Provide clear instructions for system tasks, focusing on security and efficiency.
Explain potential risks and best practices for system administration."""

DATA_ASSISTANT_PROMPT = """You are a data analysis expert specialized in helping users understand and work with data.
Provide clear explanations of data concepts and techniques for data manipulation and visualization.
Focus on practical approaches to data problems."""

# Configuration paths
CONFIG_PATH = "config.json"
DEFAULT_CONFIG = {
    "model_identifier": "gemini-2.0-pro",
    "active_agents": ["coordinator", "code_assistant", "research_assistant", "system_assistant", "data_assistant"],
    "system_prompts": {
        "coordinator": COORDINATOR_PROMPT,
        "code_assistant": CODE_ASSISTANT_PROMPT,
        "research_assistant": RESEARCH_ASSISTANT_PROMPT,
        "system_assistant": SYSTEM_ASSISTANT_PROMPT,
        "data_assistant": DATA_ASSISTANT_PROMPT
    }
}

class Prompt(Markdown):
    """Widget for user prompts"""
    pass

class Response(Markdown):
    """Widget for AI responses"""
    pass

class MultiAgentConsole(App):
    """A terminal-based console interface powered by multiple specialized AI agents."""

    AUTO_FOCUS = "Input"

    CSS = """
    Prompt {
        background: $primary 10%;
        color: $text;
        margin: 1;
        margin-right: 8;
        padding: 1 2 0 2;
    }

    Response {
        border: wide $success;
        background: $success 10%;
        color: $text;
        margin: 1;
        margin-left: 8;
        padding: 1 2 0 2;
    }

    #chat-view {
        height: 1fr;
    }

    Horizontal {
        height: auto;
    }

    #memory-panel {
        width: 30;
        height: 100%;
        border-right: solid $primary;
    }

    #conversation-list {
        height: 1fr;
        border-bottom: solid $primary;
    }

    #user-profile {
        height: auto;
        padding: 1;
        background: $surface;
    }

    .memory-button {
        margin: 1 0;
        width: 100%;
    }

    Label.label {
        margin: 1 1 1 2;
        width: 15;
        text-align: right;
    }

    #agent-selector {
        width: 1fr;
    }

    #model-input {
        width: 1fr;
    }

    #config-buttons {
        height: auto;
        margin-top: 1;
        align: center middle;
    }

    /* Progress bar styling */
    .progress-bar {
        width: 100%;
        height: 1;
        margin: 1 0;
    }

    /* Code block styling */
    .code-block {
        background: $surface;
        color: $text;
        border: wide $primary;
        padding: 1;
        margin: 1;
    }
    """

    BINDINGS = [
        # Basic navigation
        Binding("ctrl+n", "new_session", "New Session"),
        Binding("ctrl+q", "quit", "Quit"),

        # File operations
        Binding("ctrl+s", "save_conversation", "Save Conversation"),
        Binding("ctrl+o", "load_conversation", "Load Conversation"),

        # UI customization
        Binding("ctrl+t", "cycle_theme", "Cycle Theme"),
        Binding("ctrl+p", "toggle_memory_panel", "Toggle Memory Panel"),

        # Memory and search
        Binding("ctrl+f", "search_memory", "Search Memory"),
        Binding("ctrl+e", "edit_preferences", "Edit Preferences"),

        # Configuration
        Binding("ctrl+r", "reload_config", "Reload Config"),
        Binding("ctrl+c", "edit_config", "Edit Config"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the UI layout"""
        yield Header(show_clock=True)

        with Horizontal():
            # Left panel for memory management
            with Container(id="memory-panel"):
                yield Label("Memory & Context", classes="label")
                with VerticalScroll(id="conversation-list"):
                    yield Button("Recent Conversations", classes="memory-button", id="recent-conversations-button")
                    yield Button("Search Memory", classes="memory-button", id="search-memory-button")
                    yield Button("Save Current Session", classes="memory-button", id="save-session-button")

                with Container(id="user-profile"):
                    yield Label("User Profile", classes="label")
                    yield Button("Edit Preferences", classes="memory-button", id="edit-preferences-button")

            # Main chat interface
            with Container(id="main-panel"):
                with Horizontal():
                    yield Label("Model:", classes="label")
                    yield Input(id="model-input", placeholder="Model (e.g., gemini-2.0-pro)")

                with Horizontal():
                    yield Label("Active Agent:", classes="label")
                    yield Select(
                        [(agent, agent) for agent in DEFAULT_CONFIG["active_agents"]],
                        id="agent-selector",
                        prompt="Select agent or 'coordinator' for auto-delegation"
                    )

                with Horizontal(id="config-buttons"):
                    yield Button("Edit Config", id="edit-config-button")
                    yield Button("Reload Config", id="reload-config-button")

                with VerticalScroll(id="chat-view"):
                    yield Response(f"# {self.get_time_greeting()} Welcome to MultiAgentConsole\n\nYour intelligent terminal assistant powered by multiple specialized agents.")

                with Horizontal():
                    yield Button("New Session", id="new-session-button")
                    yield Input(id="chat-input", placeholder="Ask me anything...")

        yield Footer()

    def get_time_greeting(self) -> str:
        """Return appropriate greeting based on time of day"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning!"
        elif 12 <= hour < 18:
            return "Good afternoon!"
        else:
            return "Good evening!"

    def ensure_config_file(self, path: str = CONFIG_PATH) -> None:
        """Creates the default config file if it doesn't exist."""
        if not os.path.exists(path):
            logging.info(f"Configuration file not found at {path}. Creating default.")
            try:
                with open(path, 'w') as f:
                    json.dump(DEFAULT_CONFIG, f, indent=2)
                logging.info(f"Default configuration file created at {path}.")
            except Exception as e:
                logging.error(f"Failed to create default configuration file at {path}: {e}")

    def load_config(self, path: str = CONFIG_PATH) -> dict:
        """Loads configuration from the JSON file."""
        self.ensure_config_file(path)
        try:
            with open(path, 'r') as f:
                config_data = json.load(f)
            logging.info(f"Loaded configuration from {path}")
            return config_data
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from {path}: {e}. Using default config.")
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            logging.error(f"An unexpected error occurred while loading configuration from {path}: {e}")
            return DEFAULT_CONFIG.copy()

    def save_config(self, config_data: dict, path: str = CONFIG_PATH) -> None:
        """Saves the configuration to the JSON file."""
        try:
            with open(path, 'w') as f:
                json.dump(config_data, f, indent=2)
            logging.info(f"Configuration saved to {path}")
        except Exception as e:
            logging.error(f"Failed to save configuration to {path}: {e}")
            self.query_one("#chat-view").mount(Markdown(f"*Error saving configuration to `{path}`: {e}*"))

    def on_mount(self) -> None:
        """Initialize the agent system and UI on mount"""
        # Configure logging
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')
        log_handler = FileHandler('multi_agent_console.log', mode='w')
        log_handler.setFormatter(log_formatter)
        logging.basicConfig(
            level=logging.INFO,
            handlers=[log_handler]
        )

        # Create data directories if they don't exist
        os.makedirs("data", exist_ok=True)

        # Set up optimization features
        setup_optimization(
            max_cache_size=1000,
            cache_ttl=3600,  # 1 hour cache TTL
            max_memory_mb=1024,  # 1GB memory limit
            max_cpu_percent=80,  # 80% CPU limit
            lazy_loading=True
        )
        logging.info("Optimization features initialized")
        logging.info(f"Optimization stats: {get_optimization_stats()}")


        # Initialize memory manager
        self.memory_manager = MemoryManager(data_dir="data")
        self.context_enhancer = ContextEnhancer(self.memory_manager)

        # Initialize advanced tools
        self.tool_manager = AdvancedToolManager()
        logging.info("Advanced tools initialized")
        logging.info(self.tool_manager.get_tool_status())

        # Initialize security manager
        self.security_manager = SecurityManager(data_dir="data")
        logging.info("Security manager initialized")

        # Initialize UI enhancement manager
        self.ui_manager = UIEnhancementManager(data_dir="data")
        logging.info("UI enhancement manager initialized")

        # Apply theme CSS
        # Just use the default stylesheet for now
        pass

        # Initialize multi-modal manager
        self.multi_modal_manager = MultiModalManager(data_dir="data")
        logging.info("Multi-modal manager initialized")
        logging.info(self.multi_modal_manager.get_capability_status())

        # Initialize workflow manager
        self.workflow_manager = WorkflowManager(data_dir="data/workflows")
        logging.info("Workflow manager initialized")

        # Initialize offline manager
        self.offline_manager = OfflineManager(data_dir="data")
        logging.info("Offline manager initialized")

        # Initialize debugging manager
        self.debugging_manager = DebuggingManager(data_dir="data")
        logging.info("Debugging manager initialized")

        # Initialize marketplace manager
        self.marketplace_manager = MarketplaceManager(data_dir="data/marketplace")
        logging.info("Marketplace manager initialized")

        # Initialize cross-platform manager
        self.cross_platform_manager = CrossPlatformManager(data_dir="data/cross_platform")
        logging.info("Cross-platform manager initialized")

        # Initialize MCP server and plugin manager
        self.mcp_server = MCPServer()
        self.mcp_plugin_manager = MCPPluginManager(self.mcp_server)

        # Register the console as an agent
        console_agent = MCPAgent(
            agent_id="console",
            name="MultiAgentConsole",
            capabilities=["user_interface", "agent_coordination"]
        )
        self.mcp_server.register_agent(console_agent)

        # Register the logger plugin
        logger_plugin = LoggerPlugin()
        self.mcp_plugin_manager.register_plugin(logger_plugin)

        logging.info("MCP server and plugin manager initialized")

        # Initialize thought graph manager
        self.thought_graph_manager = ThoughtGraphManager(data_dir="data/thought_graphs")

        # Register graph analysis plugins
        infranodus_plugin = InfraNodusPlugin()
        simple_graph_plugin = SimpleGraphPlugin()
        self.thought_graph_manager.register_plugin("infranodus", infranodus_plugin)
        self.thought_graph_manager.register_plugin("simple_graph", simple_graph_plugin)

        logging.info("Thought graph manager and plugins initialized")

        # Register A2A plugin
        a2a_plugin = A2APlugin()
        self.mcp_plugin_manager.register_plugin(a2a_plugin)

        logging.info("A2A plugin registered")

        # Load configuration
        self.config = self.load_config()

        # Initialize session
        self.artifact_service = InMemoryArtifactService()
        self.session_service = InMemorySessionService()

        # Initialize user profile
        self.user_id = "user"  # In a real app, this would be the authenticated user

        # Update UI with loaded configuration if we're in terminal mode
        try:
            self.query_one("#model-input", Input).value = self.config.get("model_identifier", DEFAULT_CONFIG["model_identifier"])
        except Exception as e:
            # This will happen when running in web mode, which is fine
            logging.debug(f"Could not update UI: {e}")

        # Initialize agent system
        self.initialize_agent_system()

        # Initialize user profile
        self.user_profile = self.memory_manager.get_user_profile(self.user_id)

        # Hide memory panel by default on small screens
        self.memory_panel_visible = True

        # Set focus to chat input if we're in terminal mode
        try:
            self.query_one("#chat-input", Input).focus()
        except Exception as e:
            # This will happen when running in web mode, which is fine
            logging.debug(f"Could not set focus: {e}")

    def initialize_agent_system(self):
        """Initialize the multi-agent system with ADK"""
        model_identifier = self.config.get("model_identifier", DEFAULT_CONFIG["model_identifier"])
        system_prompts = self.config.get("system_prompts", DEFAULT_CONFIG["system_prompts"])
        api_key = self.config.get("api_key", None)

        # Check if API key is provided
        logging.info(f"API key from config: {api_key}")
        if not api_key:
            logging.warning("No API key provided in config.json. Please add your API key.")
            try:
                self.query_one("#chat-view").mount(Markdown("*Error: No API key provided. Please edit config.json to add your API key.*"))
            except Exception as e:
                logging.debug(f"Could not update UI: {e}")
            return

        # Set the API key as an environment variable for the ADK library
        os.environ["GOOGLE_API_KEY"] = api_key
        logging.info(f"Set GOOGLE_API_KEY environment variable with API key from config.json")

        # Disable Vertex AI to use the API key directly
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "0"
        logging.info("Disabled Vertex AI to use API key directly")

        # Get agent preferences if available
        agent_prefs = {}
        if hasattr(self, 'memory_manager') and hasattr(self, 'user_id'):
            agent_prefs = self.memory_manager.get_agent_preferences(self.user_id)

            # Override model if user has a preference
            if agent_prefs.get("model_preference"):
                model_identifier = agent_prefs["model_preference"]
                logging.info(f"Using user's preferred model: {model_identifier}")

        # Get advanced tools
        # Basic tools (same as before)
        def execute_python_code(code: str) -> str:
            """Execute Python code and return the result."""
            # Use the secure code execution from the security manager
            return self.security_manager.secure_execute_code(self.user_id, code)

        def list_files(directory: str = ".") -> str:
            """List files in the specified directory."""
            # Check if the user has read permission for the directory
            if not self.security_manager.permission_manager.check_path_permission(
                self.user_id, directory, self.security_manager.permission_manager.PERMISSION_READ):
                return f"Permission denied: You do not have read permission for {directory}."

            try:
                files = os.listdir(directory)
                return "\n".join(files)
            except Exception as e:
                return f"Error listing files: {str(e)}"

        def read_file(file_path: str) -> str:
            """Read the contents of a file."""
            # Use the secure file read from the security manager
            return self.security_manager.secure_file_read(self.user_id, file_path)

        # Git tools
        def git_status() -> str:
            """Get the status of the Git repository."""
            return self.tool_manager.git_tools.git_status()

        def git_log(max_count: int = 5) -> str:
            """Get the commit history of the Git repository."""
            return self.tool_manager.git_tools.git_log(max_count)

        def git_diff(file_path: str = None) -> str:
            """Get the diff of the specified file or all files."""
            return self.tool_manager.git_tools.git_diff(file_path)

        # Database tools
        def connect_sqlite(db_path: str) -> str:
            """Connect to a SQLite database."""
            return self.tool_manager.db_tools.connect_sqlite(db_path)

        def execute_query(conn_id: str, query: str) -> str:
            """Execute a SQL query on the specified database connection."""
            return self.tool_manager.db_tools.execute_query(conn_id, query)

        def list_tables(conn_id: str) -> str:
            """List tables in the specified database connection."""
            return self.tool_manager.db_tools.list_tables(conn_id)

        # API tools
        def http_request(url: str, method: str = 'GET', headers: dict = None, params: dict = None, data: dict = None) -> str:
            """Make an HTTP request to an external API."""
            # Use the secure HTTP request from the security manager
            return self.security_manager.secure_http_request(self.user_id, url, method, headers, params, data)

        def weather_api(location: str) -> str:
            """Get weather information for a location."""
            # Get API key securely
            api_key = self.security_manager.get_api_key("openweathermap")
            if not api_key:
                return "OpenWeatherMap API key not set. Use set_api_key('openweathermap', 'your_api_key') to set it."

            # Set the API key in the tool manager
            self.tool_manager.api_tools.set_api_key("openweathermap", api_key)

            # Check domain permission
            if not self.security_manager.permission_manager.check_domain_permission(self.user_id, "api.openweathermap.org"):
                return "Permission denied: You do not have permission to access api.openweathermap.org."

            return self.tool_manager.api_tools.weather_api(location)

        def news_api(query: str = None, category: str = None, country: str = 'us') -> str:
            """Get news articles."""
            # Get API key securely
            api_key = self.security_manager.get_api_key("newsapi")
            if not api_key:
                return "NewsAPI API key not set. Use set_api_key('newsapi', 'your_api_key') to set it."

            # Set the API key in the tool manager
            self.tool_manager.api_tools.set_api_key("newsapi", api_key)

            # Check domain permission
            if not self.security_manager.permission_manager.check_domain_permission(self.user_id, "newsapi.org"):
                return "Permission denied: You do not have permission to access newsapi.org."

            return self.tool_manager.api_tools.news_api(query, category, country)

        # Media tools
        def image_info(image_path: str) -> str:
            """Get information about an image."""
            return self.multi_modal_manager.image_processor.get_image_info(image_path)

        def save_image(image_data: str, filename: str = None) -> str:
            """Save an image from base64 data."""
            return self.multi_modal_manager.image_processor.save_image(image_data, filename)

        def ocr_image(image_path: str) -> str:
            """Extract text from an image using OCR."""
            return self.multi_modal_manager.image_processor.extract_text_from_image(image_path)

        def resize_image(file_path: str, width: int, height: int) -> str:
            """Resize an image."""
            return self.multi_modal_manager.image_processor.resize_image(file_path, width, height)

        # Voice tools
        def text_to_speech(text: str) -> str:
            """Convert text to speech."""
            return self.multi_modal_manager.audio_processor.text_to_speech(text)

        def speech_to_text(audio_file: str = None, duration: int = 5) -> str:
            """Convert speech to text."""
            return self.multi_modal_manager.audio_processor.speech_to_text(audio_file, duration)

        # Chart tools
        def generate_bar_chart(data: dict, title: str, xlabel: str, ylabel: str) -> str:
            """Generate a bar chart."""
            return self.multi_modal_manager.chart_generator.generate_bar_chart(data, title, xlabel, ylabel)

        def generate_line_chart(data: dict, x_values: list, title: str, xlabel: str, ylabel: str) -> str:
            """Generate a line chart."""
            return self.multi_modal_manager.chart_generator.generate_line_chart(data, x_values, title, xlabel, ylabel)

        def generate_pie_chart(data: dict, title: str) -> str:
            """Generate a pie chart."""
            return self.multi_modal_manager.chart_generator.generate_pie_chart(data, title)

        # Document tools
        def extract_text_from_pdf(file_path: str) -> str:
            """Extract text from a PDF file."""
            return self.multi_modal_manager.document_processor.extract_text_from_pdf(file_path)

        def get_pdf_info(file_path: str) -> str:
            """Get information about a PDF file."""
            return self.multi_modal_manager.document_processor.get_pdf_info(file_path)

        # Workflow tools
        def create_workflow(name: str, description: str) -> str:
            """Create a new workflow."""
            workflow = self.workflow_manager.create_workflow(name, description)
            self.workflow_manager.save_workflow(workflow)
            return f"Created workflow '{name}'"

        def list_workflows() -> str:
            """List available workflows."""
            workflows = self.workflow_manager.list_workflows()
            if not workflows:
                return "No workflows found"
            return "Available workflows:\n" + "\n".join([f"- {w}" for w in workflows])

        def list_templates() -> str:
            """List available workflow templates."""
            templates = self.workflow_manager.list_templates()
            if not templates:
                return "No templates found"
            return "Available templates:\n" + "\n".join([f"- {t}" for t in templates])

        def create_workflow_from_template(template_name: str, params: dict = None) -> str:
            """Create a workflow from a template."""
            try:
                template = self.workflow_manager.load_template(template_name)
                workflow = template.create_workflow(self.workflow_manager.action_registry, params)
                self.workflow_manager.save_workflow(workflow)
                return f"Created workflow '{workflow.name}' from template '{template_name}'"
            except FileNotFoundError:
                return f"Template '{template_name}' not found"

        def schedule_workflow(workflow_name: str, schedule_time: str, repeat_interval: int = None) -> str:
            """Schedule a workflow for execution."""
            try:
                workflow = self.workflow_manager.load_workflow(workflow_name)

                # Parse schedule time
                from datetime import datetime, timedelta
                if schedule_time.lower() == "now":
                    schedule_time_dt = datetime.now()
                else:
                    schedule_time_dt = datetime.fromisoformat(schedule_time)

                # Parse repeat interval
                repeat_interval_td = None
                if repeat_interval is not None:
                    repeat_interval_td = timedelta(seconds=repeat_interval)

                task = self.workflow_manager.schedule_workflow(
                    workflow, schedule_time_dt, repeat_interval_td
                )

                return f"Scheduled workflow '{workflow_name}' for execution at {schedule_time_dt.isoformat()}"
            except FileNotFoundError:
                return f"Workflow '{workflow_name}' not found"

        def list_scheduled_tasks() -> str:
            """List scheduled tasks."""
            tasks = self.workflow_manager.list_scheduled_tasks()
            if not tasks:
                return "No scheduled tasks found"

            result = "Scheduled tasks:\n"
            for i, task in enumerate(tasks):
                result += f"{i+1}. Workflow: {task['workflow']}\n"
                result += f"   Schedule time: {task['schedule_time']}\n"
                result += f"   Next execution: {task['next_execution_time']}\n"
                result += f"   Status: {task['status']}\n"

            return result

        # Offline capabilities
        def toggle_offline_mode(enable: bool = None) -> str:
            """Toggle offline mode."""
            if enable is None:
                # Toggle current state
                enable = not self.offline_manager.is_offline_mode()

            self.offline_manager.set_offline_mode(enable)
            status = "enabled" if enable else "disabled"
            return f"Offline mode {status}"

        def get_offline_status() -> str:
            """Get the status of offline capabilities."""
            status = self.offline_manager.get_offline_status()

            result = f"Offline mode: {'Enabled' if status['offline_mode'] else 'Disabled'}\n\n"

            result += "Cache:\n"
            result += f"- Total entries: {status['cache']['total_entries']}\n"
            if status['cache']['model_counts']:
                result += "- Models:\n"
                for model, count in status['cache']['model_counts'].items():
                    result += f"  - {model}: {count} entries\n"

            result += "\nKnowledge Base:\n"
            result += f"- Total documents: {status['knowledge_base']['total_documents']}\n"
            if status['knowledge_base']['categories']:
                result += "- Categories:\n"
                for category, count in status['knowledge_base']['categories'].items():
                    result += f"  - {category}: {count} documents\n"

            result += "\nLocal Models:\n"
            result += f"- Available models: {status['local_models']['count']}\n"
            if status['local_models']['models']:
                result += "- Models:\n"
                for model in status['local_models']['models']:
                    result += f"  - {model}\n"

            return result

        def add_to_knowledge_base(title: str, content: str, source: str = None, category: str = None) -> str:
            """Add a document to the knowledge base."""
            document_id = self.offline_manager.add_to_knowledge_base(title, content, source, category)
            return f"Added document '{title}' to knowledge base with ID {document_id}"

        def search_knowledge_base(query: str, limit: int = 10) -> str:
            """Search the knowledge base."""
            results = self.offline_manager.search_knowledge_base(query, limit)

            if not results:
                return f"No results found for query: {query}"

            output = f"Found {len(results)} results for query: {query}\n\n"

            for i, doc in enumerate(results):
                output += f"{i+1}. {doc['title']}\n"
                if doc['source']:
                    output += f"   Source: {doc['source']}\n"
                if doc['category']:
                    output += f"   Category: {doc['category']}\n"

                # Add a snippet of the content
                content_snippet = doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content']
                output += f"   Snippet: {content_snippet}\n\n"

            return output

        def list_local_models() -> str:
            """List available local models."""
            models = self.offline_manager.get_available_local_models()

            if not models:
                return "No local models available"

            result = "Available local models:\n"
            for i, model in enumerate(models):
                result += f"{i+1}. {model['name']} ({model['model_id']})\n"
                if model['description']:
                    result += f"   Description: {model['description']}\n"
                result += f"   Parameters: {model['parameters']}\n"
                result += f"   Context window: {model['context_window']}\n"
                if model['quantization']:
                    result += f"   Quantization: {model['quantization']}\n"
                result += "\n"

            return result

        # Debugging and monitoring tools
        def toggle_debug_mode(enable: bool = None) -> str:
            """Toggle debug mode."""
            if enable is None:
                # Toggle current state
                enable = not self.debugging_manager.is_debug_mode()

            self.debugging_manager.set_debug_mode(enable)
            status = "enabled" if enable else "disabled"
            return f"Debug mode {status}"

        def get_debug_status() -> str:
            """Get the status of debugging tools."""
            status = self.debugging_manager.get_debug_status()

            result = f"Debug mode: {'Enabled' if status['debug_mode'] else 'Disabled'}\n\n"
            result += f"Breakpoints: {status['breakpoints']}\n"
            result += f"Watches: {status['watches']}\n"
            result += f"Error count: {status['error_count']}\n"
            result += f"Performance metrics: {status['performance_metrics']}\n"

            return result

        def add_breakpoint(component: str, condition: str = None) -> str:
            """Add a breakpoint."""
            breakpoint_id = self.debugging_manager.add_breakpoint(component, condition)
            return f"Added breakpoint {breakpoint_id} for component {component}"

        def list_breakpoints() -> str:
            """List all breakpoints."""
            breakpoints = self.debugging_manager.list_breakpoints()

            if not breakpoints:
                return "No breakpoints set"

            result = "Breakpoints:\n"
            for bp_id, bp in breakpoints.items():
                result += f"{bp_id}: Component '{bp['component']}'"
                if bp['condition']:
                    result += f" with condition '{bp['condition']}'"
                result += f" - {'Enabled' if bp['enabled'] else 'Disabled'}\n"

            return result

        def get_performance_stats(operation_type: str = None) -> str:
            """Get performance statistics."""
            stats = self.debugging_manager.get_performance_stats(operation_type)

            if not stats:
                return "No performance statistics available"

            result = "Performance Statistics:\n"
            for op_type, op_stats in stats.items():
                result += f"\nOperation: {op_type}\n"
                result += f"  Count: {op_stats['count']}\n"
                result += f"  Average duration: {op_stats.get('avg_duration', 0):.3f} seconds\n"
                result += f"  Min duration: {op_stats['min_duration']:.3f} seconds\n"
                result += f"  Max duration: {op_stats['max_duration']:.3f} seconds\n"

                if op_stats.get('status_counts'):
                    result += "  Status counts:\n"
                    for status, count in op_stats['status_counts'].items():
                        result += f"    {status}: {count}\n"

            return result

        def get_error_stats() -> str:
            """Get error statistics."""
            stats = self.debugging_manager.get_error_stats()

            result = f"Total errors: {stats['total_count']}\n\n"

            if stats['type_counts']:
                result += "Error types:\n"
                for error_type, count in stats['type_counts'].items():
                    result += f"  {error_type}: {count}\n"

            if stats['component_counts']:
                result += "\nComponents with errors:\n"
                for component, count in stats['component_counts'].items():
                    result += f"  {component}: {count}\n"

            if stats['severity_counts']:
                result += "\nError severity:\n"
                for severity, count in stats['severity_counts'].items():
                    result += f"  {severity}: {count}\n"

            if stats['recent_errors']:
                result += "\nRecent errors:\n"
                for error in stats['recent_errors']:
                    result += f"  [{error['timestamp']}] {error['error_type']} in {error['component']}: {error['message']}\n"

            return result

        def get_logs(level: str = "info", limit: int = 20) -> str:
            """Get logs."""
            logs = self.debugging_manager.get_logs(level, limit)

            if not logs:
                return f"No {level} logs found"

            result = f"{level.upper()} Logs (last {len(logs)} entries):\n\n"
            for log in logs:
                result += log

            return result

        # Marketplace tools
        def list_agent_definitions(tag: str = None) -> str:
            """List available agent definitions."""
            agents = self.marketplace_manager.list_agent_definitions(tag)

            if not agents:
                return "No agent definitions found"

            result = "Available Agent Definitions:\n"
            for i, agent in enumerate(agents):
                result += f"{i+1}. {agent.name} (v{agent.version})\n"
                result += f"   Description: {agent.description}\n"
                result += f"   Author: {agent.author}\n"
                if agent.tags:
                    result += f"   Tags: {', '.join(agent.tags)}\n"
                result += "\n"

            return result

        def search_agent_definitions(query: str) -> str:
            """Search for agent definitions."""
            agents = self.marketplace_manager.search_agent_definitions(query)

            if not agents:
                return f"No agent definitions found matching '{query}'"

            result = f"Search Results for '{query}':\n"
            for i, agent in enumerate(agents):
                result += f"{i+1}. {agent.name} (v{agent.version})\n"
                result += f"   Description: {agent.description}\n"
                result += f"   Author: {agent.author}\n"
                if agent.tags:
                    result += f"   Tags: {', '.join(agent.tags)}\n"
                result += "\n"

            return result

        def list_plugins(tag: str = None) -> str:
            """List installed plugins."""
            plugins = self.marketplace_manager.list_plugins(tag)

            if not plugins:
                return "No plugins found"

            result = "Installed Plugins:\n"
            for i, plugin in enumerate(plugins):
                result += f"{i+1}. {plugin.name} (v{plugin.version})\n"
                result += f"   Description: {plugin.description}\n"
                result += f"   Author: {plugin.author}\n"
                if plugin.tags:
                    result += f"   Tags: {', '.join(plugin.tags)}\n"
                if plugin.tools:
                    result += f"   Tools: {len(plugin.tools)}\n"
                result += "\n"

            return result

        def search_plugins(query: str) -> str:
            """Search for plugins."""
            plugins = self.marketplace_manager.search_plugins(query)

            if not plugins:
                return f"No plugins found matching '{query}'"

            result = f"Search Results for '{query}':\n"
            for i, plugin in enumerate(plugins):
                result += f"{i+1}. {plugin.name} (v{plugin.version})\n"
                result += f"   Description: {plugin.description}\n"
                result += f"   Author: {plugin.author}\n"
                if plugin.tags:
                    result += f"   Tags: {', '.join(plugin.tags)}\n"
                if plugin.tools:
                    result += f"   Tools: {len(plugin.tools)}\n"
                result += "\n"

            return result

        def list_extensions() -> str:
            """List registered extensions."""
            extensions = self.marketplace_manager.list_extensions()

            if not extensions:
                return "No extensions registered"

            result = "Registered Extensions:\n"
            for i, extension in enumerate(extensions):
                result += f"{i+1}. {extension}\n"

            return result

        # Cross-platform tools
        def get_platform_info() -> str:
            """Get information about the current platform."""
            info = self.cross_platform_manager.get_platform_info()

            result = "Platform Information:\n"
            result += f"Platform: {info['platform']}\n"
            result += f"Release: {info['release']}\n"
            result += f"Version: {info['version']}\n"
            result += f"Machine: {info['machine']}\n"
            result += f"Processor: {info['processor']}\n"
            result += f"64-bit: {'Yes' if info['is_64bit'] else 'No'}\n"
            result += f"Mobile device: {'Yes' if info['is_mobile'] else 'No'}\n"
            result += f"Cloud environment: {'Yes' if info['is_cloud'] else 'No'}\n"

            return result

        def toggle_cloud_sync(enable: bool = None, sync_url: str = None) -> str:
            """Toggle cloud synchronization."""
            if enable is None:
                # Get current status
                status = self.cross_platform_manager.get_sync_status()
                enable = not status["enabled"]

            if enable:
                success = self.cross_platform_manager.enable_cloud_sync(sync_url)
                if success:
                    return f"Cloud synchronization enabled{' with URL: ' + sync_url if sync_url else ''}"
                else:
                    return "Failed to enable cloud synchronization. No sync URL provided."
            else:
                self.cross_platform_manager.disable_cloud_sync()
                return "Cloud synchronization disabled"

        def get_sync_status() -> str:
            """Get the status of cloud synchronization."""
            status = self.cross_platform_manager.get_sync_status()

            result = f"Cloud Sync Status: {'Enabled' if status['enabled'] else 'Disabled'}\n"
            if status["enabled"]:
                result += f"Sync URL: {status['sync_url']}\n"
                result += f"Last sync: {status['last_sync_time'] or 'Never'}\n"
                result += f"Sync interval: {status['sync_interval']} seconds\n"
                result += f"Sync types: {', '.join(status['sync_types'])}\n"

            return result

        def set_accessibility_setting(setting: str, enabled: bool) -> str:
            """Set an accessibility setting."""
            valid_settings = [
                "high_contrast",
                "large_text",
                "screen_reader_mode",
                "reduced_motion",
                "keyboard_shortcuts"
            ]

            if setting not in valid_settings:
                return f"Invalid accessibility setting: {setting}. Valid settings are: {', '.join(valid_settings)}"

            self.cross_platform_manager.set_accessibility_setting(setting, enabled)
            return f"Accessibility setting '{setting}' {'enabled' if enabled else 'disabled'}"

        def get_accessibility_settings() -> str:
            """Get accessibility settings."""
            settings = self.cross_platform_manager.get_accessibility_settings()

            result = "Accessibility Settings:\n"
            result += f"High contrast mode: {'Enabled' if settings.get('high_contrast') else 'Disabled'}\n"
            result += f"Large text mode: {'Enabled' if settings.get('large_text') else 'Disabled'}\n"
            result += f"Screen reader mode: {'Enabled' if settings.get('screen_reader_mode') else 'Disabled'}\n"
            result += f"Reduced motion: {'Enabled' if settings.get('reduced_motion') else 'Disabled'}\n"
            result += f"Keyboard shortcuts: {'Enabled' if settings.get('keyboard_shortcuts_enabled') else 'Disabled'}\n"

            if settings.get("custom_shortcuts"):
                result += "\nCustom shortcuts:\n"
                for action, shortcut in settings["custom_shortcuts"].items():
                    result += f"  {action}: {shortcut}\n"

            return result

        def toggle_mobile_optimizations(enable: bool = None) -> str:
            """Toggle mobile optimizations."""
            if enable is None:
                # Get platform info to determine if we're on a mobile device
                info = self.cross_platform_manager.get_platform_info()
                enable = info["is_mobile"]

            self.cross_platform_manager.enable_mobile_optimizations(enable)
            return f"Mobile optimizations {'enabled' if enable else 'disabled'}"

        # MCP tools
        def list_mcp_agents() -> str:
            """List all registered MCP agents."""
            agents = self.mcp_server.list_agents()

            if not agents:
                return "No MCP agents registered"

            result = "Registered MCP Agents:\n"
            for i, agent in enumerate(agents):
                result += f"{i+1}. {agent.name} ({agent.agent_id})\n"
                if agent.capabilities:
                    result += f"   Capabilities: {', '.join(agent.capabilities)}\n"
                result += f"   Status: {'Active' if agent.is_active else 'Inactive'}\n"
                result += "\n"

            return result

        def list_mcp_plugins() -> str:
            """List all registered MCP plugins."""
            plugins = self.mcp_plugin_manager.list_plugins()

            if not plugins:
                return "No MCP plugins registered"

            result = "Registered MCP Plugins:\n"
            for i, plugin in enumerate(plugins):
                result += f"{i+1}. {plugin.name} ({plugin.plugin_id})\n"
                result += f"   Description: {plugin.description}\n"
                result += f"   Status: {'Enabled' if plugin.is_enabled else 'Disabled'}\n"
                result += "\n"

            return result

        def send_mcp_message(sender: str, receiver: str, message_type: str, content: str) -> str:
            """Send a message through the MCP server.

            Args:
                sender: ID of the sending agent
                receiver: ID of the receiving agent (or 'broadcast')
                message_type: Type of message
                content: Message content
            """
            # Create the message
            message = MCPMessage(
                sender=sender,
                receiver=receiver,
                message_type=message_type,
                content=content
            )

            # Send the message
            success = self.mcp_server.send_message(message)

            if success:
                return f"Message sent from {sender} to {receiver}"
            else:
                return f"Failed to send message from {sender} to {receiver}"

        def get_recent_mcp_messages(count: int = 5) -> str:
            """Get recent messages from the MCP server.

            Args:
                count: Maximum number of messages to return
            """
            messages = self.mcp_server.get_recent_messages(count)

            if not messages:
                return "No MCP messages found"

            result = f"Recent MCP Messages (last {len(messages)}):\n\n"
            for i, message in enumerate(messages):
                result += f"{i+1}. From: {message.sender} To: {message.receiver}\n"
                result += f"   Type: {message.message_type}\n"
                result += f"   Content: {message.content}\n"
                result += "\n"

            return result

        # Thought graph analysis tools
        def analyze_user_query(self, query: str) -> str:
            """Analyze a user query using thought graph analysis.

            Args:
                query: The user's query text
            """
            analysis = self.thought_graph_manager.analyze_query(query)

            result = "Thought Graph Analysis:\n\n"

            # Add concepts
            result += "Key Concepts:\n"
            for concept in analysis["concepts"][:10]:  # Limit to top 10
                result += f"- {concept}\n"
            result += "\n"

            # Add central concepts
            result += "Central Concepts (most influential):\n"
            for concept, score in analysis["central_concepts"][:5]:  # Limit to top 5
                result += f"- {concept} (score: {score:.2f})\n"
            result += "\n"

            # Add missing concepts
            if analysis["missing_concepts"]:
                result += "Potentially Missing Concepts:\n"
                for concept in analysis["missing_concepts"]:
                    result += f"- {concept}\n"
                result += "\n"

            # Add structural gaps
            if analysis["structural_gaps"]:
                result += "Structural Gaps (potential connections):\n"
                for concept1, concept2 in analysis["structural_gaps"]:
                    result += f"- {concept1} <-> {concept2}\n"
                result += "\n"

            # Add suggestions
            result += "Suggestions to Improve Query:\n"
            for suggestion in analysis["suggestions"]:
                result += f"- {suggestion}\n"

            return result

        def get_query_suggestions(self, query: str) -> str:
            """Get suggestions to improve a user query.

            Args:
                query: The user's query text
            """
            suggestions = self.thought_graph_manager.get_query_suggestions(query)

            if not suggestions:
                return "No suggestions available for this query."

            result = "Suggestions to Improve Your Query:\n\n"
            for i, suggestion in enumerate(suggestions):
                result += f"{i+1}. {suggestion}\n"

            return result

        def visualize_thought_graph(self, query: str = None, output_path: str = None) -> str:
            """Visualize the thought graph for a query.

            Args:
                query: The user's query text (optional, uses current graph if None)
                output_path: Path to save the visualization (optional)
            """
            if query:
                # Analyze the query first to build the graph
                self.thought_graph_manager.analyze_query(query)

            # Then visualize it
            graph_path = self.thought_graph_manager.visualize_graph(output_path)

            return f"Thought graph visualization saved to: {graph_path}\n\nYou can open this file to view the visualization."

        def list_graph_plugins(self) -> str:
            """List all registered graph analysis plugins."""
            plugins = self.thought_graph_manager.list_plugins()

            if not plugins:
                return "No graph analysis plugins registered"

            result = "Registered Graph Analysis Plugins:\n\n"
            for i, plugin in enumerate(plugins):
                result += f"{i+1}. {plugin['name']} ({plugin['id']})\n"
                result += f"   Description: {plugin['description']}\n\n"

            return result

        def analyze_with_graph_plugin(self, plugin_id: str, query: str) -> str:
            """Analyze a query using a specific graph analysis plugin.

            Args:
                plugin_id: Plugin ID to use
                query: The user's query text
            """
            try:
                analysis = self.thought_graph_manager.analyze_with_plugin(plugin_id, query)

                result = f"Analysis using {plugin_id}:\n\n"

                # Format the analysis results
                for key, value in analysis.items():
                    result += f"{key.replace('_', ' ').title()}: "

                    if isinstance(value, list):
                        result += "\n"
                        for item in value:
                            if isinstance(item, tuple) and len(item) == 2:
                                result += f"- {item[0]}: {item[1]}\n"
                            else:
                                result += f"- {item}\n"
                    else:
                        result += f"{value}\n"

                    result += "\n"

                return result
            except ValueError as e:
                return f"Error: {str(e)}"
            except Exception as e:
                logging.error(f"Error in analyze_with_graph_plugin: {e}")
                return f"An error occurred while analyzing with plugin {plugin_id}: {str(e)}"

        # A2A protocol tools
        def create_a2a_task(self, agent_id: str, input_text: str) -> str:
            """Create a new A2A task.

            Args:
                agent_id: ID of the A2A agent to execute the task
                input_text: Input text for the task
            """
            # Create message to send to the A2A plugin
            message = MCPMessage(
                sender="agent",
                receiver="a2a_plugin",
                message_type="create_a2a_task",
                content={
                    "agent_id": agent_id,
                    "input_text": input_text
                }
            )

            # Send the message
            if not self.mcp_server.send_message(message):
                return "Failed to send message to A2A plugin"

            # Wait for response (in a real implementation, this would be asynchronous)
            # For now, we'll just return a message indicating the task was created
            return f"A2A task creation request sent to agent {agent_id}"

        def get_a2a_task(self, task_id: str) -> str:
            """Get information about an A2A task.

            Args:
                task_id: ID of the task to get information about
            """
            # Create message to send to the A2A plugin
            message = MCPMessage(
                sender="agent",
                receiver="a2a_plugin",
                message_type="get_a2a_task",
                content={
                    "task_id": task_id
                }
            )

            # Send the message
            if not self.mcp_server.send_message(message):
                return "Failed to send message to A2A plugin"

            # Wait for response (in a real implementation, this would be asynchronous)
            # For now, we'll just return a message indicating the request was sent
            return f"A2A task query sent for task {task_id}"

        def cancel_a2a_task(self, task_id: str) -> str:
            """Cancel an A2A task.

            Args:
                task_id: ID of the task to cancel
            """
            # Create message to send to the A2A plugin
            message = MCPMessage(
                sender="agent",
                receiver="a2a_plugin",
                message_type="cancel_a2a_task",
                content={
                    "task_id": task_id
                }
            )

            # Send the message
            if not self.mcp_server.send_message(message):
                return "Failed to send message to A2A plugin"

            # Wait for response (in a real implementation, this would be asynchronous)
            # For now, we'll just return a message indicating the request was sent
            return f"A2A task cancellation request sent for task {task_id}"

        def list_a2a_agents(self) -> str:
            """List all registered A2A agents."""
            # Get all agents from the MCP server
            agents = self.mcp_server.list_agents()

            # Filter for A2A-compatible agents (those with 'a2a' capability)
            a2a_agents = [agent for agent in agents if 'a2a' in agent.capabilities]

            if not a2a_agents:
                return "No A2A-compatible agents registered"

            result = "Registered A2A Agents:\n\n"
            for i, agent in enumerate(a2a_agents):
                result += f"{i+1}. {agent.name} ({agent.agent_id})\n"
                result += f"   Capabilities: {', '.join(agent.capabilities)}\n\n"

            return result

        # Create personalized instructions if context enhancer is available
        def get_personalized_instructions(agent_name, base_prompt):
            if hasattr(self, 'context_enhancer') and hasattr(self, 'user_id'):
                return self.context_enhancer.create_agent_instructions(
                    self.user_id, agent_name, base_prompt)
            return base_prompt

        # Return early if no API key is provided
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            return

        # Define specialized agents with advanced tools
        self.code_assistant = LlmAgent(
            name="code_assistant",
            model=model_identifier,
            description="Specialized in writing and explaining code",
            instruction=get_personalized_instructions(
                "code_assistant", system_prompts.get("code_assistant", CODE_ASSISTANT_PROMPT)),
            api_key=api_key,
            tools=[
                # Basic tools
                FunctionTool(execute_python_code),
                FunctionTool(list_files),
                FunctionTool(read_file),
                # Git tools
                FunctionTool(git_status),
                FunctionTool(git_log),
                FunctionTool(git_diff)
            ]
        )

        self.research_assistant = LlmAgent(
            name="research_assistant",
            model=model_identifier,
            description="Specialized in research and information gathering",
            instruction=get_personalized_instructions(
                "research_assistant", system_prompts.get("research_assistant", RESEARCH_ASSISTANT_PROMPT)),
            api_key=api_key,
            tools=[
                # Web search
                google_search,
                # API tools
                FunctionTool(http_request),
                FunctionTool(weather_api),
                FunctionTool(news_api),
                # Image tools
                FunctionTool(save_image)
            ]
        )

        self.system_assistant = LlmAgent(
            name="system_assistant",
            model=model_identifier,
            description="Specialized in system administration tasks",
            instruction=get_personalized_instructions(
                "system_assistant", system_prompts.get("system_assistant", SYSTEM_ASSISTANT_PROMPT)),
            api_key=api_key,
            tools=[
                # File system tools
                FunctionTool(list_files),
                FunctionTool(read_file),
                # Git tools
                FunctionTool(git_status),
                FunctionTool(git_log),
                # Voice tools
                FunctionTool(text_to_speech),
                FunctionTool(speech_to_text)
            ]
        )

        self.data_assistant = LlmAgent(
            name="data_assistant",
            model=model_identifier,
            description="Specialized in data analysis and visualization",
            instruction=get_personalized_instructions(
                "data_assistant", system_prompts.get("data_assistant", DATA_ASSISTANT_PROMPT)),
            api_key=api_key,
            tools=[
                # Code execution
                FunctionTool(execute_python_code),
                FunctionTool(read_file),
                # Database tools
                FunctionTool(connect_sqlite),
                FunctionTool(execute_query),
                FunctionTool(list_tables),
                # Media tools
                FunctionTool(image_info),
                FunctionTool(ocr_image),
                FunctionTool(resize_image),
                # Chart tools
                FunctionTool(generate_bar_chart),
                FunctionTool(generate_line_chart),
                FunctionTool(generate_pie_chart),
                # Document tools
                FunctionTool(extract_text_from_pdf),
                FunctionTool(get_pdf_info),
                # Workflow tools
                FunctionTool(create_workflow),
                FunctionTool(list_workflows),
                FunctionTool(list_templates),
                FunctionTool(create_workflow_from_template),
                FunctionTool(schedule_workflow),
                FunctionTool(list_scheduled_tasks),
                # Offline tools
                FunctionTool(toggle_offline_mode),
                FunctionTool(get_offline_status),
                FunctionTool(add_to_knowledge_base),
                FunctionTool(search_knowledge_base),
                FunctionTool(list_local_models),
                # Debugging tools
                FunctionTool(toggle_debug_mode),
                FunctionTool(get_debug_status),
                FunctionTool(add_breakpoint),
                FunctionTool(list_breakpoints),
                FunctionTool(get_performance_stats),
                FunctionTool(get_error_stats),
                FunctionTool(get_logs),
                # Marketplace tools
                FunctionTool(list_agent_definitions),
                FunctionTool(search_agent_definitions),
                FunctionTool(list_plugins),
                FunctionTool(search_plugins),
                FunctionTool(list_extensions),
                # Cross-platform tools
                FunctionTool(get_platform_info),
                FunctionTool(toggle_cloud_sync),
                FunctionTool(get_sync_status),
                FunctionTool(set_accessibility_setting),
                FunctionTool(get_accessibility_settings),
                FunctionTool(toggle_mobile_optimizations),
                # MCP tools
                FunctionTool(list_mcp_agents),
                FunctionTool(list_mcp_plugins),
                FunctionTool(send_mcp_message),
                FunctionTool(get_recent_mcp_messages),
                # Thought graph analysis tools
                FunctionTool(analyze_user_query),
                FunctionTool(get_query_suggestions),
                FunctionTool(visualize_thought_graph),
                FunctionTool(list_graph_plugins),
                FunctionTool(analyze_with_graph_plugin),
                # A2A protocol tools
                FunctionTool(create_a2a_task),
                FunctionTool(get_a2a_task),
                FunctionTool(cancel_a2a_task),
                FunctionTool(list_a2a_agents)
            ]
        )

        # Root coordinator agent
        self.coordinator = Agent(
            name="coordinator",
            model=model_identifier,
            description="A terminal-based assistant that coordinates specialized agents",
            instruction=get_personalized_instructions(
                "coordinator", system_prompts.get("coordinator", COORDINATOR_PROMPT)),
            api_key=api_key,
            sub_agents=[
                self.code_assistant,
                self.research_assistant,
                self.system_assistant,
                self.data_assistant
            ]
        )

        # Create agent map for direct access
        self.agents = {
            "coordinator": self.coordinator,
            "code_assistant": self.code_assistant,
            "research_assistant": self.research_assistant,
            "system_assistant": self.system_assistant,
            "data_assistant": self.data_assistant
        }

        # Set active agent (use user's preference if available)
        default_agent = agent_prefs.get("default_agent", "coordinator")
        if default_agent in self.agents:
            self.active_agent_name = default_agent
            self.active_agent = self.agents[default_agent]
        else:
            self.active_agent_name = "coordinator"
            self.active_agent = self.coordinator

        # Initialize runner
        self.runner = Runner(
            app_name="multi_agent_console",
            agent=self.active_agent,
            artifact_service=self.artifact_service,
            session_service=self.session_service
        )

        # Create session
        self.session = self.session_service.create_session(
            app_name="multi_agent_console",
            user_id=self.user_id
        )

        logging.info(f"Agent system initialized with model: {model_identifier}")
        logging.info(f"Active agent: {self.active_agent_name}")

    @on(Select.Changed, "#agent-selector")
    def on_agent_selector_changed(self, event: Select.Changed) -> None:
        """Handle agent selector changes."""
        new_agent_name = event.value
        if new_agent_name and new_agent_name in self.agents and new_agent_name != self.active_agent_name:
            self.active_agent_name = new_agent_name
            self.active_agent = self.agents[new_agent_name]

            # Update runner with new active agent
            self.runner = Runner(
                app_name="multi_agent_console",
                agent=self.active_agent,
                artifact_service=self.artifact_service,
                session_service=self.session_service
            )

            # Check if session exists before trying to use it
            if not hasattr(self, 'session'):
                self.query_one("#chat-view").mount(Markdown(f"*Switched to {new_agent_name}, but no active session. Please check your configuration and try again.*"))
                logging.warning(f"Switched to agent {new_agent_name} but no active session exists")
            else:
                self.query_one("#chat-view").mount(Markdown(f"*Switched to {new_agent_name}*"))
                logging.info(f"Switched to agent: {new_agent_name}")

    @on(Input.Submitted, "#model-input")
    def on_model_input_submitted(self, event: Input.Submitted) -> None:
        """Handle model input submission."""
        new_model_identifier = event.value
        if new_model_identifier and new_model_identifier != self.config.get("model_identifier"):
            self.config["model_identifier"] = new_model_identifier
            self.save_config(self.config)

            # Reinitialize agent system with new model
            self.initialize_agent_system()

            self.query_one("#chat-view").mount(Markdown(f"*Model set to **{new_model_identifier}**.*"))
            logging.info(f"Model identifier changed to: {new_model_identifier}")

    @on(Button.Pressed, "#edit-config-button")
    def on_edit_config_button_pressed(self, event: Button.Pressed) -> None:
        """Open the configuration file in the default editor."""
        logging.info(f"Attempting to open config file: {CONFIG_PATH}")
        try:
            system = platform.system()
            if system == "Windows":
                # Use notepad to open the file on Windows
                subprocess.Popen(["notepad.exe", CONFIG_PATH])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", CONFIG_PATH], check=True)
            else:  # Linux and other UNIX-like
                subprocess.run(["xdg-open", CONFIG_PATH], check=True)

            logging.info(f"Opened {CONFIG_PATH} for editing.")
            self.query_one("#chat-view").mount(Markdown(f"*Opened `{CONFIG_PATH}` for editing. Press 'Reload Config' after saving.*"))
        except FileNotFoundError:
            logging.error(f"Config file {CONFIG_PATH} not found.")
            self.query_one("#chat-view").mount(Markdown(f"*Error: Config file `{CONFIG_PATH}` not found.*"))
        except Exception as e:
            logging.error(f"Failed to open config file {CONFIG_PATH}: {e}")
            self.query_one("#chat-view").mount(Markdown(f"*Error opening `{CONFIG_PATH}`: {e}*"))

    @on(Button.Pressed, "#reload-config-button")
    def on_reload_config_button_pressed(self, event: Button.Pressed) -> None:
        """Reload configuration and reinitialize the agent system."""
        self.action_reload_config()

    def action_toggle_memory_panel(self) -> None:
        """Toggle the visibility of the memory panel."""
        self.memory_panel_visible = not self.memory_panel_visible
        memory_panel = self.query_one("#memory-panel")

        if self.memory_panel_visible:
            memory_panel.remove_class("hidden")
        else:
            memory_panel.add_class("hidden")

        logging.info(f"Memory panel visibility toggled to {self.memory_panel_visible}")

    def action_save_conversation(self) -> None:
        """Save the current conversation."""
        # Check if session exists
        if not hasattr(self, 'session'):
            self.query_one("#chat-view").mount(Markdown("*Error: No active session to save. Please start a conversation first.*"))
            logging.error("Attempted to save conversation but no session exists")
            return

        # Generate a title based on the first user message
        title = None
        for event in self.session.events:
            if hasattr(event, 'role') and event.role == 'user' and event.content and event.content.parts:
                content = ''.join(part.text or '' for part in event.content.parts)
                if content:
                    # Use first 30 chars of first message as title
                    title = content[:30] + "..." if len(content) > 30 else content
                    break

        # Save the conversation
        conversation_id = self.memory_manager.save_conversation(self.session, title=title)

        # Notify the user
        self.query_one("#chat-view").mount(Markdown(f"*Conversation saved with ID: {conversation_id}*"))
        logging.info(f"Conversation saved with ID: {conversation_id}")

    def action_load_conversation(self) -> None:
        """Load a saved conversation."""
        # Check if memory_manager exists
        if not hasattr(self, 'memory_manager'):
            self.query_one("#chat-view").mount(Markdown("*Error: Memory manager not initialized. Please check your configuration and try again.*"))
            logging.error("Attempted to load conversation but memory manager doesn't exist")
            return

        # Get recent conversations
        try:
            conversations = self.memory_manager.list_conversations(self.user_id, limit=5)

            if not conversations:
                self.query_one("#chat-view").mount(Markdown("*No saved conversations found*"))
                return

            # Display the conversations
            message = "*Available conversations:*\n\n"
            for i, conv in enumerate(conversations):
                message += f"{i+1}. {conv['title']} ({datetime.fromtimestamp(conv['timestamp']).strftime('%Y-%m-%d %H:%M')})\n"

            message += "\n*Type the number of the conversation to load in your next message*"
            self.query_one("#chat-view").mount(Markdown(message))

            # Store the conversations for later reference
            self.available_conversations = conversations
            self.waiting_for_conversation_selection = True
        except Exception as e:
            self.query_one("#chat-view").mount(Markdown(f"*Error loading conversations: {e}*"))
            logging.error(f"Error loading conversations: {e}")
            return

    def action_new_session(self) -> None:
        """Create a new session."""
        self._create_new_session()

    def action_search_memory(self) -> None:
        """Search through memory."""
        # Check if memory_manager exists
        if not hasattr(self, 'memory_manager'):
            self.query_one("#chat-view").mount(Markdown("*Error: Memory manager not initialized. Please check your configuration and try again.*"))
            logging.error("Attempted to search memory but memory manager doesn't exist")
            return

        self.query_one("#chat-view").mount(Markdown("*Enter your search query in the chat input*"))
        self.waiting_for_search_query = True

    def action_edit_preferences(self) -> None:
        """Edit user preferences."""
        try:
            # Check if user_profile exists
            if not hasattr(self, 'user_profile'):
                self.query_one("#chat-view").mount(Markdown("*Error: User profile not initialized. Please check your configuration and try again.*"))
                logging.error("Attempted to edit preferences but user profile doesn't exist")
                return

            # Display current preferences
            preferences = self.user_profile.get("preferences", {})
            message = "*Current User Preferences:*\n\n"

            for key, value in preferences.items():
                message += f"**{key}**: {value}\n"

            # Display API keys (masked)
            message += "\n*API Keys:*\n"

            # Check if security_manager exists
            if not hasattr(self, 'security_manager') or not hasattr(self.security_manager, 'credential_manager'):
                message += "Security manager not initialized. API keys cannot be displayed.\n"
            else:
                services = self.security_manager.credential_manager.list_services()
                if services:
                    for service in services:
                        keys = self.security_manager.credential_manager.list_credentials(service)
                        for key in keys:
                            message += f"**{service}.{key}**: ****\n"
                else:
                    message += "No API keys set.\n"
        except Exception as e:
            self.query_one("#chat-view").mount(Markdown(f"*Error editing preferences: {e}*"))
            logging.error(f"Error editing preferences: {e}")
            return

        # Display available themes
        message += "\n*Available Themes:*\n"
        themes = self.ui_manager.theme_manager.list_themes()
        current_theme = self.ui_manager.theme_manager.current_theme
        for theme in themes:
            if theme == current_theme:
                message += f"**{theme}** (current)\n"
            else:
                message += f"**{theme}**\n"

        message += "\n*To change a preference, type 'set preference_name value' in the chat input*"
        message += "\n*To set an API key, type 'set_api_key service_name your_api_key' in the chat input*"
        message += "\n*To change the theme, type 'set_theme theme_name' in the chat input*"
        self.query_one("#chat-view").mount(Markdown(message))
        self.waiting_for_preference_edit = True

    def action_edit_config(self) -> None:
        """Open the configuration file in the default editor."""
        # Call the button press handler directly with None as the event
        # This is safe because the handler doesn't use the event parameter
        self.on_edit_config_button_pressed(None)

    def action_reload_config(self) -> None:
        """Reload configuration and reinitialize the agent system."""
        logging.info("Reloading configuration...")
        self.config = self.load_config()

        # Update the model input field
        self.query_one("#model-input").value = self.config.get("model_identifier", "gemini-2.0-pro")

        # Reinitialize the agent system
        self.initialize_agent_system()

        self.query_one("#chat-view").mount(Markdown("*Configuration reloaded*"))

    def action_cycle_theme(self) -> None:
        """Cycle through available themes."""
        themes = self.ui_manager.theme_manager.list_themes()
        current_theme = self.ui_manager.theme_manager.current_theme

        # Find the index of the current theme
        try:
            current_index = themes.index(current_theme)
            next_index = (current_index + 1) % len(themes)
            next_theme = themes[next_index]
        except ValueError:
            next_theme = themes[0] if themes else "default"

        # Set the new theme
        if self.set_theme(next_theme):
            self.query_one("#chat-view").mount(Markdown(f"*Theme changed to '{next_theme}'*"))

    async def _create_new_session(self) -> None:
        """Create a new session and reset the UI."""
        logging.info("Creating new session.")

        try:
            # Create new session
            self.session = self.session_service.create_session(
                app_name="multi_agent_console",
                user_id=self.user_id
            )
        except Exception as e:
            logging.error(f"Failed to create new session: {e}")
            chat_view = self.query_one("#chat-view")
            await chat_view.mount(Markdown(f"*Error: Failed to create new session: {e}*"))
            return

        # Clear chat view
        chat_view = self.query_one("#chat-view")
        await chat_view.remove_children()
        await chat_view.mount(Response(f"# {self.get_time_greeting()} Welcome to MultiAgentConsole\n\nYour intelligent terminal assistant powered by multiple specialized agents."))

        self.query_one("#chat-input", Input).focus()

    @on(Button.Pressed, "#new-session-button")
    async def on_new_session_button_pressed(self, event: Button.Pressed) -> None:
        """Handle 'New Session' button press."""
        await self._create_new_session()

    @on(Button.Pressed, "#save-session-button")
    def on_save_session_button_pressed(self, event: Button.Pressed) -> None:
        """Handle 'Save Current Session' button press."""
        self.action_save_conversation()

    @on(Button.Pressed, "#recent-conversations-button")
    def on_recent_conversations_button_pressed(self, event: Button.Pressed) -> None:
        """Handle 'Recent Conversations' button press."""
        self.action_load_conversation()

    @on(Button.Pressed, "#search-memory-button")
    def on_search_memory_button_pressed(self, event: Button.Pressed) -> None:
        """Handle 'Search Memory' button press."""
        self.action_search_memory()

    @on(Button.Pressed, "#edit-preferences-button")
    def on_edit_preferences_button_pressed(self, event: Button.Pressed) -> None:
        """Handle 'Edit Preferences' button press."""
        self.action_edit_preferences()

    def set_theme(self, theme_name: str) -> bool:
        """Set the UI theme.

        Args:
            theme_name: Name of the theme

        Returns:
            True if the theme was set, False otherwise
        """
        if self.ui_manager.set_theme(theme_name):
            # Update the CSS
            # Just use the default stylesheet for now
            pass
            return True
        return False

    @on(Input.Submitted, "#chat-input")
    async def on_chat_input(self, event: Input.Submitted) -> None:
        """Handle chat input submissions."""
        # Add the input to the auto-completion history
        if hasattr(self, 'ui_manager') and hasattr(self.ui_manager, 'auto_completer'):
            self.ui_manager.add_to_history(event.value)
        chat_view = self.query_one("#chat-view")
        prompt = event.value
        event.input.clear()

        if not prompt:
            return

        # Check if we're waiting for special input
        if hasattr(self, 'waiting_for_conversation_selection') and self.waiting_for_conversation_selection:
            try:
                selection = int(prompt)
                if 1 <= selection <= len(self.available_conversations):
                    conversation = self.available_conversations[selection-1]
                    conversation_id = conversation['id']

                    # Create a new session from the conversation
                    restored_session = self.memory_manager.create_session_from_conversation(
                        conversation_id, "multi_agent_console")

                    if restored_session:
                        self.session = restored_session

                        # Clear chat view and show the restored conversation
                        await chat_view.remove_children()
                        await chat_view.mount(Markdown(f"*Restored conversation: {conversation['title']}*"))

                        # Display the conversation messages
                        for event in self.session.events:
                            if event.content and event.content.parts:
                                text = ''.join(part.text or '' for part in event.content.parts)
                                if text:
                                    if event.author == self.user_id:
                                        await chat_view.mount(Prompt(f"**You:** {text}"))
                                    else:
                                        await chat_view.mount(Response(f"**[{event.author}]:** {text}"))
                else:
                    await chat_view.mount(Markdown("*Invalid selection. Please try again.*"))
            except ValueError:
                await chat_view.mount(Markdown("*Invalid input. Please enter a number.*"))

            # Reset the waiting flag
            self.waiting_for_conversation_selection = False
            return

        elif hasattr(self, 'waiting_for_search_query') and self.waiting_for_search_query:
            # Search memory with the provided query
            results = self.memory_manager.search_conversations(self.user_id, prompt)

            if results:
                message = f"*Search results for '{prompt}':*\n\n"
                for i, result in enumerate(results):
                    message += f"{i+1}. {result['title']} ({datetime.fromtimestamp(result['timestamp']).strftime('%Y-%m-%d %H:%M')})\n"

                message += "\n*Type the number of the conversation to load in your next message*"
                await chat_view.mount(Markdown(message))

                # Store the results for later reference
                self.available_conversations = results
                self.waiting_for_conversation_selection = True
            else:
                await chat_view.mount(Markdown(f"*No results found for '{prompt}'*"))

            # Reset the waiting flag
            self.waiting_for_search_query = False
            return

        elif hasattr(self, 'waiting_for_preference_edit') and self.waiting_for_preference_edit:
            # Check if the input matches the expected format for preferences
            if prompt.startswith('set '):
                parts = prompt.split(' ', 2)
                if len(parts) >= 3:
                    preference_name = parts[1]
                    preference_value = parts[2]

                    # Update the preference
                    self.memory_manager.update_user_preference(self.user_id, preference_name, preference_value)

                    # Refresh the user profile
                    self.user_profile = self.memory_manager.get_user_profile(self.user_id)

                    await chat_view.mount(Markdown(f"*Preference '{preference_name}' updated to '{preference_value}'*"))
                else:
                    await chat_view.mount(Markdown("*Invalid format. Use 'set preference_name value'*"))
            # Check if the input matches the expected format for API keys
            elif prompt.startswith('set_api_key '):
                parts = prompt.split(' ', 2)
                if len(parts) >= 3:
                    service_name = parts[1]
                    api_key = parts[2]

                    # Set the API key securely
                    self.security_manager.set_api_key(service_name, api_key)

                    await chat_view.mount(Markdown(f"*API key for '{service_name}' has been set*"))
                else:
                    await chat_view.mount(Markdown("*Invalid format. Use 'set_api_key service_name your_api_key'*"))
            # Check if the input matches the expected format for theme changes
            elif prompt.startswith('set_theme '):
                parts = prompt.split(' ', 1)
                if len(parts) >= 2:
                    theme_name = parts[1]

                    # Set the theme
                    if self.set_theme(theme_name):
                        await chat_view.mount(Markdown(f"*Theme changed to '{theme_name}'*"))
                    else:
                        await chat_view.mount(Markdown(f"*Theme '{theme_name}' not found. Available themes: {', '.join(self.ui_manager.theme_manager.list_themes())}*"))
                else:
                    await chat_view.mount(Markdown("*Invalid format. Use 'set_theme theme_name'*"))
            else:
                await chat_view.mount(Markdown("*Invalid format. Use 'set preference_name value', 'set_api_key service_name your_api_key', or 'set_theme theme_name'*"))

            # Reset the waiting flag
            self.waiting_for_preference_edit = False
            return

        # Normal chat input processing
        await chat_view.mount(Prompt(f"**You:** {prompt}"))
        await chat_view.mount(response := Response("*Thinking...*"))
        response.anchor()

        self.process_prompt(prompt, response)
        logging.info(f"Input submitted: {prompt}")

    @work(thread=True)
    @optimize_function
    async def process_prompt(self, prompt: str, response: Response) -> None:
        """Process the prompt with the active agent and update the response"""
        try:
            self.call_from_thread(response.update, "*Thinking...*")

            # Check if session exists
            if not hasattr(self, 'session'):
                self.call_from_thread(response.update, "*Error: No active session. Please check your configuration and try again.*")
                return

            # Enhance prompt with context if available
            enhanced_prompt = self.context_enhancer.enhance_prompt(self.user_id, prompt, self.session)

            # Create content from enhanced prompt
            content = types.Content(
                role="user",
                parts=[types.Part(text=enhanced_prompt)]
            )

            # Run the agent
            async for event in self.runner.run_async(
                user_id=self.session.user_id,
                session_id=self.session.id,
                new_message=content
            ):
                if event.content and event.content.parts:
                    if text := ''.join(part.text or '' for part in event.content.parts):
                        # Apply syntax highlighting to code blocks
                        if hasattr(self, 'ui_manager') and hasattr(self.ui_manager, 'syntax_highlighter'):
                            # Find code blocks in the response
                            import re
                            code_blocks = re.findall(r'```(\w*)\n([\s\S]*?)```', text)

                            for lang, code in code_blocks:
                                # Determine the language
                                language = lang.strip() if lang.strip() else None

                                # Highlight the code
                                highlighted_code = self.ui_manager.highlight_code(code, language)

                                # Replace the code block in the response
                                original_block = f'```{lang}\n{code}```'
                                new_block = f'```{lang}\n{highlighted_code}```'
                                text = text.replace(original_block, new_block)

                        response_content = f"**[{event.author}]:** {text}"
                        self.call_from_thread(response.update, response_content)

            # Update user interests based on this interaction
            self.memory_manager.update_user_interests(self.user_id)

            logging.info("Agent processing completed.")
        except Exception as e:
            logging.exception(f"Error during prompt processing: {e}")
            error_message = f"**Error:** {e}"
            self.call_from_thread(response.update, error_message)

    @optimize_function
    async def process_message(self, message: str, session_id: Optional[str] = None) -> str:
        """Process a message from the web interface.

        Args:
            message: The user's message
            session_id: Optional session ID

        Returns:
            Response from the agent
        """
        try:
            # Get the active agent name if available, otherwise use a default
            active_agent = getattr(self, 'active_agent', None)
            active_agent_name = active_agent.name if active_agent else "default agent"
            logging.info(f"Processing web message with {active_agent_name}: {message}")

            # Check if session exists
            if not hasattr(self, 'session'):
                error_message = "Error: No active session. Please check your configuration and try again."
                logging.error(error_message)
                return error_message

            # Enhance prompt with context if available
            enhanced_prompt = self.context_enhancer.enhance_prompt(self.user_id, message, self.session)

            # Create content from enhanced prompt
            content = types.Content(
                role="user",
                parts=[types.Part(text=enhanced_prompt)]
            )

            # Collect the response text
            response_text = ""

            # Run the agent
            async for event in self.runner.run_async(
                user_id=self.session.user_id,
                session_id=self.session.id,
                new_message=content
            ):
                if event.content and event.content.parts:
                    if text := ''.join(part.text or '' for part in event.content.parts):
                        # Append to the response text
                        response_text = text

            # Update user interests based on this interaction
            self.memory_manager.update_user_interests(self.user_id)

            logging.info("Web message processing completed.")
            return response_text
        except Exception as e:
            logging.exception(f"Error during web message processing: {e}")
            error_message = f"Error: {e}"
            return error_message


def main():
    """Entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MultiAgentConsole - A terminal-based multi-agent system")
    parser.add_argument("--web", action="store_true", help="Start the web interface")
    parser.add_argument("--port", type=int, default=8000, help="Port for the web interface (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for the web interface (default: 0.0.0.0)")
    parser.add_argument("--terminal", action="store_true", help="Start the terminal interface (default if no other interface is specified)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-auth", action="store_true", help="Disable authentication for web interface (deprecated, use --mode=single-user instead)")
    parser.add_argument("--mode", type=str, choices=["multi-user", "single-user"], default="multi-user",
                      help="Web interface mode: multi-user (with authentication) or single-user (no authentication)")
    parser.add_argument("--optimize", action="store_true", help="Enable performance optimizations")
    args = parser.parse_args()

    # Initialize optimization if requested
    if args.optimize:
        # The existing setup_optimization function doesn't take an 'enabled' parameter
        setup_optimization()
        logging.info("Performance optimizations enabled")

    # Initialize security
    setup_security(csrf_secret_key=secrets.token_hex(32), rate_limit=100, rate_window=60)
    logging.info("Security features initialized")

    # Initialize the console app
    app = MultiAgentConsole()

    # Start the web server if requested
    if args.web:
        # Initialize the app components without starting the UI
        app.on_mount()

        # Determine authentication mode
        auth_enabled = not args.no_auth
        if args.mode == "single-user":
            auth_enabled = False

        # Start the web server
        web_server = WebServer(
            console_app=app,
            host=args.host,
            port=args.port,
            debug=args.debug,
            auth_enabled=auth_enabled
        )
        web_server.start()

        logging.info(f"Web interface started at http://{args.host}:{args.port}")
        print(f"Web interface started at http://{args.host}:{args.port}")
        print(f"Debug mode: {'enabled' if args.debug else 'disabled'}")
        print(f"Mode: {args.mode}")
        print(f"Authentication: {'disabled' if not auth_enabled else 'enabled'}")
        print(f"Performance optimizations: {'enabled' if args.optimize else 'disabled'}")

        # Keep the main thread running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Shutting down...")
            web_server.stop()

    # Start the terminal interface if requested or if no interface is specified
    elif args.terminal or not (args.web):
        app.run()


if __name__ == "__main__":
    main()
