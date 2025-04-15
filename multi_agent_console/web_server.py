"""
Web Server for MultiAgentConsole.

This module provides a web server for the MultiAgentConsole:
- Serves a browser-based UI
- Provides API endpoints for chat and graph visualization
- Enables interactive features not possible in the terminal

Author: Sai Sunkara
Copyright 2025 Sai Sunkara
License: MIT
"""

import json
import logging
import os
import threading
import secrets
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException, File, UploadFile, Form, Cookie, Header
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn
from pydantic import BaseModel, validator

from .plugin import PluginManager, PluginRegistry
from .security_enhancements import InputValidator, OutputSanitizer, AuthenticationManager, CSRFProtection, RateLimiter, setup_security

class ChatMessage(BaseModel):
    """Chat message model."""
    role: str
    content: str

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None

class GraphRequest(BaseModel):
    """Graph analysis request model."""
    query: str
    plugin_id: Optional[str] = None

class ToolExecuteRequest(BaseModel):
    """Tool execution request model."""
    tool_id: str
    parameters: Dict[str, Any] = {}

class ImageRequest(BaseModel):
    """Image processing request model."""
    width: Optional[int] = None
    height: Optional[int] = None

class TextToSpeechRequest(BaseModel):
    """Text to speech request model."""
    text: str
    voice: Optional[str] = "default"

class ChartRequest(BaseModel):
    """Chart generation request model."""
    chart_type: str
    data: Dict[str, Any]

class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str

class RegisterRequest(BaseModel):
    """Registration request model."""
    username: str
    password: str
    email: str
    confirm_password: str

class WorkflowTemplateRequest(BaseModel):
    """Workflow template request model."""
    template_name: str

class OfflineModeRequest(BaseModel):
    """Offline mode request model."""
    enabled: bool

class KnowledgeBaseAddRequest(BaseModel):
    """Knowledge base add request model."""
    topic: str
    content: str

class AgentRatingRequest(BaseModel):
    """Agent rating request model."""
    rating: float

class WorkflowRequest(BaseModel):
    """Workflow request model."""
    workflow_id: str
    inputs: Dict[str, Any] = {}

class WebServer:
    """Web server for MultiAgentConsole."""

    def __init__(self, console_app=None, host: str = "0.0.0.0", port: int = 8000, debug: bool = False, auth_enabled: bool = True):
        """Initialize the web server.

        Args:
            console_app: Reference to the MultiAgentConsole app
            host: Host to bind the server to
            port: Port to bind the server to
            debug: Whether to enable debug mode
            auth_enabled: Whether to enable authentication
        """
        self.console_app = console_app
        self.host = host
        self.port = port
        self.debug = debug
        self.auth_enabled = auth_enabled
        self.app = FastAPI(title="MultiAgentConsole Web UI")
        self.active_connections: List[WebSocket] = []
        self.server_thread = None

        # Initialize templates
        self.templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

        # Set up static files directory
        self.static_dir = str(Path(__file__).parent / "static")
        self.static_files = StaticFiles(directory=self.static_dir)

        # Initialize security components
        self.auth_manager = None
        self.csrf_protection = None
        self.rate_limiter = None
        self.input_validator = None
        self.output_sanitizer = None
        self.permission_manager = None

        # Initialize auth manager if available and enabled
        if auth_enabled:
            if console_app and hasattr(console_app, "auth_manager"):
                self.auth_manager = console_app.auth_manager
                logging.info("Using auth manager from console app")
            else:
                # Create a local auth manager
                try:
                    self.auth_manager = AuthenticationManager()
                    logging.info("Created local auth manager")
                except Exception as e:
                    logging.warning(f"Could not create auth manager: {e}")
                    logging.warning("Authentication will not be available")
                    self.auth_manager = None

            # Initialize CSRF protection
            self.csrf_protection = CSRFProtection()

            # Initialize rate limiter
            self.rate_limiter = RateLimiter(limit=100, window=60)  # 100 requests per minute

            # Initialize input validator and output sanitizer
            self.input_validator = InputValidator()
            self.output_sanitizer = OutputSanitizer()

            # Set up security
            setup_security(csrf_secret_key=secrets.token_hex(32), rate_limit=100, rate_window=60)

        # Initialize workflow manager if available
        self.workflow_manager = None

        if console_app and hasattr(console_app, "workflow_manager"):
            self.workflow_manager = console_app.workflow_manager
            logging.info("Using workflow manager from console app")
        else:
            # Create a local workflow manager
            try:
                from .workflow import WorkflowManager
                self.workflow_manager = WorkflowManager()
                logging.info("Created local workflow manager")
            except ImportError as e:
                logging.warning(f"Could not import workflow module: {e}")
                logging.warning("Workflow functionality will not be available")
                self.workflow_manager = None

        # Initialize offline manager if available
        self.offline_manager = None

        if console_app and hasattr(console_app, "offline_manager"):
            self.offline_manager = console_app.offline_manager
            logging.info("Using offline manager from console app")
        else:
            # Create a local offline manager
            try:
                from .cache import OfflineManager
                self.offline_manager = OfflineManager()
                logging.info("Created local offline manager")
            except ImportError as e:
                logging.warning(f"Could not import cache module: {e}")
                logging.warning("Offline functionality will not be available")
                self.offline_manager = None

        # Initialize agent marketplace if available
        self.agent_marketplace = None

        if console_app and hasattr(console_app, "agent_marketplace"):
            self.agent_marketplace = console_app.agent_marketplace
            logging.info("Using agent marketplace from console app")
        else:
            # Create a local agent marketplace
            try:
                from .agent_marketplace import AgentMarketplace
                self.agent_marketplace = AgentMarketplace()
                logging.info("Created local agent marketplace")
            except ImportError as e:
                logging.warning(f"Could not import agent_marketplace module: {e}")
                logging.warning("Agent marketplace functionality will not be available")
                self.agent_marketplace = None

        # Initialize plugin manager and registry
        self.plugin_manager = None
        self.plugin_registry = None

        plugins_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
        if os.path.exists(plugins_dir):
            self.plugin_manager = PluginManager([plugins_dir])
            self.plugin_registry = PluginRegistry(plugins_dir, plugin_manager=self.plugin_manager)
            logging.info(f"Plugin manager initialized with directory: {plugins_dir}")

            # Load plugins
            self.plugin_manager.load_plugins()
            logging.info(f"Loaded {len(self.plugin_manager.plugins)} plugins")
        else:
            logging.warning(f"Plugins directory not found: {plugins_dir}")
            logging.warning("Plugin functionality will not be available")

        # Create static directories if they don't exist
        self.static_dir = Path(__file__).parent / "static"
        self.static_dir.mkdir(exist_ok=True)

        # Create templates directory if it doesn't exist
        self.templates_dir = Path(__file__).parent / "templates"
        self.templates_dir.mkdir(exist_ok=True)

        # Set up middleware and routes
        self.setup_middleware()
        self.setup_routes()

        logging.info(f"Web server initialized at http://{host}:{port}")

    def setup_middleware(self):
        """Set up middleware for the FastAPI app."""
        # Set up CORS with more restrictive settings for security
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost", "http://localhost:8007", "https://localhost", "https://localhost:8007"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
        )

        # Add rate limiting middleware
        @self.app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            if self.rate_limiter:
                # Use client IP as the rate limit key
                client_ip = request.client.host if request.client else "unknown"

                # Check if rate limit is exceeded
                if not self.rate_limiter.check_limit(client_ip):
                    return Response(
                        content=json.dumps({"error": "Rate limit exceeded"}),
                        status_code=429,
                        media_type="application/json"
                    )

                # Add rate limit headers
                response = await call_next(request)
                response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.limit)
                response.headers["X-RateLimit-Remaining"] = str(self.rate_limiter.get_remaining(client_ip))
                response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.rate_limiter.window)

                return response
            else:
                return await call_next(request)

        # Add CSRF protection middleware for non-GET requests
        @self.app.middleware("http")
        async def csrf_middleware(request: Request, call_next):
            if self.csrf_protection and request.method not in ["GET", "HEAD", "OPTIONS"]:
                # Get session ID from cookie
                session_id = request.cookies.get("session_id")

                # Get CSRF token from header
                csrf_token = request.headers.get("X-CSRF-Token")

                # Validate CSRF token if session exists
                if session_id and not csrf_token:
                    return Response(
                        content=json.dumps({"error": "CSRF token missing"}),
                        status_code=403,
                        media_type="application/json"
                    )

                if session_id and csrf_token and not self.csrf_protection.validate_token(session_id, csrf_token):
                    return Response(
                        content=json.dumps({"error": "Invalid CSRF token"}),
                        status_code=403,
                        media_type="application/json"
                    )

            return await call_next(request)

    def setup_routes(self):
        """Set up routes for the FastAPI app."""
        # Set up workflow routes if workflow manager is available
        if self.workflow_manager:
            self.setup_workflow_routes()

        # Set up offline routes if offline manager is available
        if self.offline_manager:
            self.setup_offline_routes()

        # Set up marketplace routes if agent marketplace is available
        if self.agent_marketplace:
            self.setup_marketplace_routes()

        # Set up plugin routes if plugin manager is available
        if self.plugin_manager:
            self.setup_plugin_routes()
        # Authentication routes
        @self.app.get("/login", response_class=HTMLResponse)
        async def get_login(request: Request):
            """Serve the login page."""
            return self.templates.TemplateResponse("login.html", {"request": request, "error": None})

        @self.app.post("/login")
        async def post_login(request: Request, username: str = Form(...), password: str = Form(...)):
            """Process login form submission."""
            if not self.auth_manager:
                return self.templates.TemplateResponse("login.html", {
                    "request": request,
                    "error": "Authentication is not available"
                })

            # Authenticate user
            session_id = self.auth_manager.authenticate(username, password)
            if not session_id:
                return self.templates.TemplateResponse("login.html", {
                    "request": request,
                    "error": "Invalid username or password"
                })

            # Create response with redirect
            response = RedirectResponse(url="/", status_code=303)

            # Set session cookie
            response.set_cookie(key="session_id", value=session_id, httponly=True)

            return response

        @self.app.get("/register", response_class=HTMLResponse)
        async def get_register(request: Request):
            """Serve the registration page."""
            return self.templates.TemplateResponse("register.html", {"request": request, "error": None})

        @self.app.post("/register")
        async def post_register(
            request: Request,
            username: str = Form(...),
            password: str = Form(...),
            confirm_password: str = Form(...),
            email: str = Form(...)
        ):
            """Process registration form submission."""
            if not self.auth_manager:
                return self.templates.TemplateResponse("register.html", {
                    "request": request,
                    "error": "Authentication is not available"
                })

            # Check if passwords match
            if password != confirm_password:
                return self.templates.TemplateResponse("register.html", {
                    "request": request,
                    "error": "Passwords do not match"
                })

            # Register user
            success = self.auth_manager.register_user(username, password, email)
            if not success:
                return self.templates.TemplateResponse("register.html", {
                    "request": request,
                    "error": "Username already exists"
                })

            # Redirect to login page
            return RedirectResponse(url="/login", status_code=303)

        @self.app.get("/logout")
        async def get_logout(session_id: Optional[str] = Cookie(None)):
            """Log out the user."""
            if self.auth_manager and session_id:
                self.auth_manager.logout(session_id)

            # Create response with redirect
            response = RedirectResponse(url="/login", status_code=303)

            # Clear session cookie
            response.delete_cookie(key="session_id")

            return response

        # Main routes
        @self.app.get("/", response_class=HTMLResponse)
        async def get_index(request: Request, session_id: Optional[str] = Cookie(None)):
            """Serve the main index page."""
            # Check if authentication is required
            if self.auth_manager and not session_id:
                return RedirectResponse(url="/login", status_code=303)

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    # Invalid session, redirect to login
                    response = RedirectResponse(url="/login", status_code=303)
                    response.delete_cookie(key="session_id")
                    return response

            # Serve the index page
            index_path = Path(__file__).parent / "templates" / "index.html"
            if index_path.exists():
                with open(index_path, "r") as f:
                    return f.read()
            else:
                # Return a basic HTML page if the template doesn't exist
                return """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>MultiAgentConsole</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <script src="https://cdn.tailwindcss.com"></script>
                    <script src="https://unpkg.com/htmx.org@1.9.6"></script>
                    <script src="https://d3js.org/d3.v7.min.js"></script>
                </head>
                <body class="bg-gray-100">
                    <div class="container mx-auto p-4">
                        <h1 class="text-2xl font-bold mb-4">MultiAgentConsole Web UI</h1>
                        <p>The template files are not yet created. Please run the setup script to create them.</p>
                    </div>
                </body>
                </html>
                """

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication."""
            # Get cookies from the connection
            cookies = websocket.cookies
            session_id = cookies.get("session_id")

            # Check authentication if enabled
            if self.auth_manager and not session_id:
                await websocket.close(code=1008, reason="Authentication required")
                return

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    await websocket.close(code=1008, reason="Invalid session")
                    return

            # Accept the connection
            await websocket.accept()
            self.active_connections.append(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    # Process the message based on its type
                    if message.get("type") == "chat":
                        response = await self.process_chat_message(message.get("content", ""))
                        await websocket.send_json({
                            "type": "chat_response",
                            "content": response
                        })
                    elif message.get("type") == "graph_analysis":
                        graph_data = await self.process_graph_analysis(
                            message.get("query", ""),
                            message.get("plugin_id")
                        )
                        await websocket.send_json({
                            "type": "graph_data",
                            "data": graph_data
                        })
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
            except Exception as e:
                logging.error(f"WebSocket error: {e}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)

        @self.app.post("/api/chat")
        async def chat_endpoint(request: ChatRequest, session_id: Optional[str] = Cookie(None)):
            """REST API endpoint for chat."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            response = await self.process_chat_message(request.message, request.session_id or session_id)
            return {"response": response}

        @self.app.post("/api/graph")
        async def graph_endpoint(request: GraphRequest):
            """REST API endpoint for graph analysis."""
            graph_data = await self.process_graph_analysis(request.query, request.plugin_id)
            return {"data": graph_data}

        @self.app.get("/api/plugins/graph")
        async def list_graph_plugins():
            """List available graph analysis plugins."""
            if self.console_app and hasattr(self.console_app, "thought_graph_manager"):
                plugins = list(self.console_app.thought_graph_manager.plugins.keys())
                return {"plugins": plugins}
            return {"plugins": []}

        @self.app.get("/api/agents")
        async def list_agents():
            """List available agents."""
            if self.console_app:
                agents = self.console_app.config.get("active_agents", [])
                return {"agents": agents}
            return {"agents": []}

        # Tool-related endpoints
        @self.app.get("/api/tools")
        async def list_tools():
            """List available tools."""
            if not self.console_app or not hasattr(self.console_app, "tool_manager"):
                return {"tools": []}

            tools = []

            # Git tools
            if hasattr(self.console_app.tool_manager, "git_tools"):
                git_tools = [
                    {"id": "git_status", "name": "Git Status", "description": "Get the status of a Git repository", "category": "git", "parameters": [
                        {"name": "repo_path", "type": "string", "description": "Path to the Git repository", "required": True}
                    ]},
                    {"id": "git_log", "name": "Git Log", "description": "Get the commit history of a Git repository", "category": "git", "parameters": [
                        {"name": "repo_path", "type": "string", "description": "Path to the Git repository", "required": True},
                        {"name": "max_count", "type": "number", "description": "Maximum number of commits to return", "required": False}
                    ]},
                    {"id": "git_diff", "name": "Git Diff", "description": "Get the diff between commits or working directory", "category": "git", "parameters": [
                        {"name": "repo_path", "type": "string", "description": "Path to the Git repository", "required": True},
                        {"name": "commit_a", "type": "string", "description": "First commit to compare", "required": False},
                        {"name": "commit_b", "type": "string", "description": "Second commit to compare", "required": False}
                    ]}
                ]
                tools.extend(git_tools)

            # Database tools
            if hasattr(self.console_app.tool_manager, "database_tools"):
                db_tools = [
                    {"id": "connect_sqlite", "name": "Connect to SQLite", "description": "Connect to a SQLite database", "category": "database", "parameters": [
                        {"name": "db_path", "type": "string", "description": "Path to the SQLite database file", "required": True}
                    ]},
                    {"id": "execute_query", "name": "Execute SQL Query", "description": "Execute a SQL query on a connected database", "category": "database", "parameters": [
                        {"name": "query", "type": "textarea", "description": "SQL query to execute", "required": True}
                    ]},
                    {"id": "list_tables", "name": "List Tables", "description": "List all tables in a connected database", "category": "database", "parameters": []}
                ]
                tools.extend(db_tools)

            # API tools
            if hasattr(self.console_app.tool_manager, "api_tools"):
                api_tools = [
                    {"id": "http_request", "name": "HTTP Request", "description": "Make an HTTP request to a URL", "category": "api", "parameters": [
                        {"name": "url", "type": "string", "description": "URL to request", "required": True},
                        {"name": "method", "type": "select", "description": "HTTP method", "required": True, "options": [
                            {"value": "GET", "label": "GET"},
                            {"value": "POST", "label": "POST"},
                            {"value": "PUT", "label": "PUT"},
                            {"value": "DELETE", "label": "DELETE"}
                        ]},
                        {"name": "headers", "type": "textarea", "description": "HTTP headers as JSON", "required": False},
                        {"name": "body", "type": "textarea", "description": "Request body", "required": False}
                    ]},
                    {"id": "weather_api", "name": "Weather API", "description": "Get weather information for a location", "category": "api", "parameters": [
                        {"name": "location", "type": "string", "description": "Location (city, country)", "required": True}
                    ]},
                    {"id": "news_api", "name": "News API", "description": "Get news articles on a topic", "category": "api", "parameters": [
                        {"name": "topic", "type": "string", "description": "News topic", "required": True},
                        {"name": "count", "type": "number", "description": "Number of articles to return", "required": False}
                    ]}
                ]
                tools.extend(api_tools)

            # MCP tools
            if hasattr(self.console_app, "mcp_server"):
                mcp_tools = [
                    {"id": "list_mcp_agents", "name": "List MCP Agents", "description": "List all registered MCP agents", "category": "mcp", "parameters": []},
                    {"id": "list_mcp_plugins", "name": "List MCP Plugins", "description": "List all registered MCP plugins", "category": "mcp", "parameters": []},
                    {"id": "send_mcp_message", "name": "Send MCP Message", "description": "Send a message to an MCP agent", "category": "mcp", "parameters": [
                        {"name": "agent_id", "type": "string", "description": "ID of the agent to send the message to", "required": True},
                        {"name": "content", "type": "textarea", "description": "Message content", "required": True}
                    ]},
                    {"id": "get_recent_mcp_messages", "name": "Get Recent MCP Messages", "description": "Get recent MCP messages", "category": "mcp", "parameters": [
                        {"name": "count", "type": "number", "description": "Number of messages to return", "required": False}
                    ]}
                ]
                tools.extend(mcp_tools)

            # Graph tools
            if hasattr(self.console_app, "thought_graph_manager"):
                graph_tools = [
                    {"id": "analyze_user_query", "name": "Analyze User Query", "description": "Analyze a user query to identify key concepts and relationships", "category": "graph", "parameters": [
                        {"name": "query", "type": "textarea", "description": "User query to analyze", "required": True}
                    ]},
                    {"id": "get_query_suggestions", "name": "Get Query Suggestions", "description": "Get suggestions to improve a query", "category": "graph", "parameters": [
                        {"name": "query", "type": "textarea", "description": "User query to get suggestions for", "required": True}
                    ]},
                    {"id": "visualize_thought_graph", "name": "Visualize Thought Graph", "description": "Visualize a thought graph for a query", "category": "graph", "parameters": [
                        {"name": "query", "type": "textarea", "description": "User query to visualize", "required": True}
                    ]},
                    {"id": "list_graph_plugins", "name": "List Graph Plugins", "description": "List available graph analysis plugins", "category": "graph", "parameters": []},
                    {"id": "analyze_with_graph_plugin", "name": "Analyze with Graph Plugin", "description": "Analyze a query with a specific graph plugin", "category": "graph", "parameters": [
                        {"name": "query", "type": "textarea", "description": "User query to analyze", "required": True},
                        {"name": "plugin_id", "type": "string", "description": "ID of the graph plugin to use", "required": True}
                    ]}
                ]
                tools.extend(graph_tools)

            # A2A tools
            if hasattr(self.console_app, "a2a_adapter"):
                a2a_tools = [
                    {"id": "create_a2a_task", "name": "Create A2A Task", "description": "Create a new A2A task", "category": "a2a", "parameters": [
                        {"name": "task_description", "type": "textarea", "description": "Description of the task", "required": True},
                        {"name": "agent_id", "type": "string", "description": "ID of the agent to assign the task to", "required": True}
                    ]},
                    {"id": "get_a2a_task", "name": "Get A2A Task", "description": "Get information about an A2A task", "category": "a2a", "parameters": [
                        {"name": "task_id", "type": "string", "description": "ID of the task to get information about", "required": True}
                    ]},
                    {"id": "cancel_a2a_task", "name": "Cancel A2A Task", "description": "Cancel an A2A task", "category": "a2a", "parameters": [
                        {"name": "task_id", "type": "string", "description": "ID of the task to cancel", "required": True}
                    ]},
                    {"id": "list_a2a_agents", "name": "List A2A Agents", "description": "List all A2A-compatible agents", "category": "a2a", "parameters": []}
                ]
                tools.extend(a2a_tools)

            return {"tools": tools}

        @self.app.post("/api/execute-tool")
        async def execute_tool(request: ToolExecuteRequest):
            """Execute a tool with parameters."""
            if not self.console_app:
                return {"error": "Console app not available"}

            try:
                # Execute the tool based on its ID
                tool_id = request.tool_id
                params = request.parameters

                # Git tools
                if tool_id == "git_status":
                    result = self.console_app.tool_manager.git_tools.git_status(params.get("repo_path", "."))
                elif tool_id == "git_log":
                    result = self.console_app.tool_manager.git_tools.git_log(
                        params.get("repo_path", "."),
                        max_count=params.get("max_count", 10)
                    )
                elif tool_id == "git_diff":
                    result = self.console_app.tool_manager.git_tools.git_diff(
                        params.get("repo_path", "."),
                        commit_a=params.get("commit_a"),
                        commit_b=params.get("commit_b")
                    )

                # Database tools
                elif tool_id == "connect_sqlite":
                    result = self.console_app.tool_manager.database_tools.connect_sqlite(params.get("db_path", ""))
                elif tool_id == "execute_query":
                    result = self.console_app.tool_manager.database_tools.execute_query(params.get("query", ""))
                elif tool_id == "list_tables":
                    result = self.console_app.tool_manager.database_tools.list_tables()

                # API tools
                elif tool_id == "http_request":
                    headers = {}
                    if params.get("headers"):
                        try:
                            headers = json.loads(params.get("headers", "{}"))
                        except json.JSONDecodeError:
                            return {"error": "Invalid JSON in headers"}

                    result = self.console_app.tool_manager.api_tools.http_request(
                        params.get("url", ""),
                        method=params.get("method", "GET"),
                        headers=headers,
                        body=params.get("body")
                    )
                elif tool_id == "weather_api":
                    result = self.console_app.tool_manager.api_tools.weather_api(params.get("location", ""))
                elif tool_id == "news_api":
                    result = self.console_app.tool_manager.api_tools.news_api(
                        params.get("topic", ""),
                        count=params.get("count", 5)
                    )

                # MCP tools
                elif tool_id == "list_mcp_agents":
                    result = self.console_app.mcp_server.list_agents()
                elif tool_id == "list_mcp_plugins":
                    result = self.console_app.mcp_plugin_manager.list_plugins()
                elif tool_id == "send_mcp_message":
                    result = self.console_app.mcp_server.send_message(
                        params.get("agent_id", ""),
                        params.get("content", "")
                    )
                elif tool_id == "get_recent_mcp_messages":
                    result = self.console_app.mcp_server.get_recent_messages(
                        count=params.get("count", 10)
                    )

                # Graph tools
                elif tool_id == "analyze_user_query":
                    result = self.console_app.thought_graph_manager.analyze_query(params.get("query", ""))
                elif tool_id == "get_query_suggestions":
                    result = self.console_app.thought_graph_manager.get_query_suggestions(params.get("query", ""))
                elif tool_id == "visualize_thought_graph":
                    result = self.console_app.thought_graph_manager.visualize_graph(params.get("query", ""))
                elif tool_id == "list_graph_plugins":
                    result = list(self.console_app.thought_graph_manager.plugins.keys())
                elif tool_id == "analyze_with_graph_plugin":
                    result = self.console_app.thought_graph_manager.analyze_with_plugin(
                        params.get("query", ""),
                        params.get("plugin_id", "")
                    )

                # A2A tools
                elif tool_id == "create_a2a_task":
                    result = self.console_app.a2a_adapter.create_task(
                        params.get("task_description", ""),
                        params.get("agent_id", "")
                    )
                elif tool_id == "get_a2a_task":
                    result = self.console_app.a2a_adapter.get_task(params.get("task_id", ""))
                elif tool_id == "cancel_a2a_task":
                    result = self.console_app.a2a_adapter.cancel_task(params.get("task_id", ""))
                elif tool_id == "list_a2a_agents":
                    result = self.console_app.a2a_adapter.list_agents()

                else:
                    return {"error": f"Unknown tool: {tool_id}"}

                return {"result": result}
            except Exception as e:
                logging.error(f"Error executing tool {request.tool_id}: {e}")
                return {"error": str(e)}

        # Multi-modal endpoints
        @self.app.post("/api/image-info")
        async def image_info(image: UploadFile = File(...)):
            """Get information about an image."""
            if not self.console_app or not hasattr(self.console_app, "multi_modal_manager"):
                return {"error": "Multi-modal manager not available"}

            try:
                # Save the uploaded file temporarily
                temp_file_path = f"temp_{image.filename}"
                with open(temp_file_path, "wb") as f:
                    f.write(await image.read())

                # Get image info
                result = self.console_app.multi_modal_manager.image_processor.get_image_info(temp_file_path)

                # Clean up
                os.remove(temp_file_path)

                return result
            except Exception as e:
                logging.error(f"Error getting image info: {e}")
                return {"error": str(e)}

        @self.app.post("/api/ocr-image")
        async def ocr_image(image: UploadFile = File(...)):
            """Extract text from an image using OCR."""
            if not self.console_app or not hasattr(self.console_app, "multi_modal_manager"):
                return {"error": "Multi-modal manager not available"}

            try:
                # Save the uploaded file temporarily
                temp_file_path = f"temp_{image.filename}"
                with open(temp_file_path, "wb") as f:
                    f.write(await image.read())

                # Extract text
                text = self.console_app.multi_modal_manager.image_processor.extract_text_from_image(temp_file_path)

                # Clean up
                os.remove(temp_file_path)

                return {"text": text}
            except Exception as e:
                logging.error(f"Error extracting text from image: {e}")
                return {"error": str(e)}

        @self.app.post("/api/resize-image")
        async def resize_image(image: UploadFile = File(...), request: ImageRequest = Depends()):
            """Resize an image."""
            if not self.console_app or not hasattr(self.console_app, "multi_modal_manager"):
                return {"error": "Multi-modal manager not available"}

            try:
                # Save the uploaded file temporarily
                temp_file_path = f"temp_{image.filename}"
                with open(temp_file_path, "wb") as f:
                    f.write(await image.read())

                # Resize image
                output_path = f"resized_{image.filename}"
                self.console_app.multi_modal_manager.image_processor.resize_image(
                    temp_file_path,
                    output_path,
                    width=request.width,
                    height=request.height
                )

                # Return the resized image
                with open(output_path, "rb") as f:
                    content = f.read()

                # Clean up
                os.remove(temp_file_path)
                os.remove(output_path)

                return Response(content=content, media_type="image/jpeg")
            except Exception as e:
                logging.error(f"Error resizing image: {e}")
                return {"error": str(e)}

        @self.app.post("/api/text-to-speech")
        async def text_to_speech(request: TextToSpeechRequest):
            """Convert text to speech."""
            if not self.console_app or not hasattr(self.console_app, "multi_modal_manager"):
                return {"error": "Multi-modal manager not available"}

            try:
                # Convert text to speech
                output_path = "tts_output.wav"

                # Pass voice parameter if available
                if hasattr(self.console_app.multi_modal_manager.audio_processor, "text_to_speech_with_voice"):
                    self.console_app.multi_modal_manager.audio_processor.text_to_speech_with_voice(
                        request.text, output_path, request.voice
                    )
                else:
                    # Fallback to standard method
                    self.console_app.multi_modal_manager.audio_processor.text_to_speech(request.text, output_path)

                # Return the audio file
                with open(output_path, "rb") as f:
                    content = f.read()

                # Clean up
                os.remove(output_path)

                return Response(content=content, media_type="audio/wav")
            except Exception as e:
                logging.error(f"Error converting text to speech: {e}")
                return {"error": str(e)}

        @self.app.post("/api/speech-to-text")
        async def speech_to_text(audio: UploadFile = File(...)):
            """Convert speech to text."""
            if not self.console_app or not hasattr(self.console_app, "multi_modal_manager"):
                return {"error": "Multi-modal manager not available"}

            try:
                # Save the uploaded file temporarily
                temp_file_path = f"temp_{audio.filename}"
                with open(temp_file_path, "wb") as f:
                    f.write(await audio.read())

                # Convert speech to text
                text = self.console_app.multi_modal_manager.audio_processor.speech_to_text(audio_file=temp_file_path)

                # Clean up
                os.remove(temp_file_path)

                return {"text": text}
            except Exception as e:
                logging.error(f"Error converting speech to text: {e}")
                return {"error": str(e)}

        @self.app.post("/api/generate-chart")
        async def generate_chart(request: ChartRequest):
            """Generate a chart."""
            if not self.console_app or not hasattr(self.console_app, "multi_modal_manager"):
                return {"error": "Multi-modal manager not available"}

            try:
                # Generate chart
                output_path = "chart_output.png"

                if request.chart_type == "bar":
                    self.console_app.multi_modal_manager.chart_generator.generate_bar_chart(
                        request.data.get("labels", []),
                        request.data.get("values", []),
                        title=request.data.get("title", ""),
                        output_path=output_path
                    )
                elif request.chart_type == "line":
                    self.console_app.multi_modal_manager.chart_generator.generate_line_chart(
                        request.data.get("labels", []),
                        request.data.get("values", []),
                        title=request.data.get("title", ""),
                        output_path=output_path
                    )
                elif request.chart_type == "pie":
                    self.console_app.multi_modal_manager.chart_generator.generate_pie_chart(
                        request.data.get("labels", []),
                        request.data.get("values", []),
                        title=request.data.get("title", ""),
                        output_path=output_path
                    )
                else:
                    return {"error": f"Unknown chart type: {request.chart_type}"}

                # Return the chart image
                with open(output_path, "rb") as f:
                    content = f.read()

                # Clean up
                os.remove(output_path)

                return Response(content=content, media_type="image/png")
            except Exception as e:
                logging.error(f"Error generating chart: {e}")
                return {"error": str(e)}

        @self.app.post("/api/extract-text-from-document")
        async def extract_text_from_document(document: UploadFile = File(...)):
            """Extract text from a document."""
            if not self.console_app or not hasattr(self.console_app, "multi_modal_manager"):
                return {"error": "Multi-modal manager not available"}

            try:
                # Save the uploaded file temporarily
                temp_file_path = f"temp_{document.filename}"
                with open(temp_file_path, "wb") as f:
                    f.write(await document.read())

                # Extract text
                text = self.console_app.multi_modal_manager.document_processor.extract_text_from_pdf(temp_file_path)

                # Clean up
                os.remove(temp_file_path)

                return {"text": text}
            except Exception as e:
                logging.error(f"Error extracting text from document: {e}")
                return {"error": str(e)}

        @self.app.post("/api/document-info")
        async def document_info(document: UploadFile = File(...)):
            """Get information about a document."""
            if not self.console_app or not hasattr(self.console_app, "multi_modal_manager"):
                return {"error": "Multi-modal manager not available"}

            try:
                # Save the uploaded file temporarily
                temp_file_path = f"temp_{document.filename}"
                with open(temp_file_path, "wb") as f:
                    f.write(await document.read())

                # Get document info
                info = self.console_app.multi_modal_manager.document_processor.get_pdf_info(temp_file_path)

                # Clean up
                os.remove(temp_file_path)

                return info
            except Exception as e:
                logging.error(f"Error getting document info: {e}")
                return {"error": str(e)}

        # Mount static files
        self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")

    async def process_chat_message(self, message: str, session_id: Optional[str] = None) -> str:
        """Process a chat message.

        Args:
            message: The user's message
            session_id: Optional session ID

        Returns:
            Response from the agent
        """
        if self.console_app:
            # Use the console app's agent system to process the message
            # This is a placeholder - the actual implementation will depend on how
            # the console app processes messages
            if hasattr(self.console_app, "process_message"):
                return await self.console_app.process_message(message, session_id)
            else:
                # Fallback if process_message doesn't exist
                return "The console app doesn't have a process_message method."
        return "Console app not available."

    async def process_graph_analysis(self, query: str, plugin_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a graph analysis request.

        Args:
            query: The query to analyze
            plugin_id: Optional plugin ID to use for analysis

        Returns:
            Graph data as a dictionary
        """
        if self.console_app and hasattr(self.console_app, "thought_graph_manager"):
            try:
                if plugin_id and plugin_id in self.console_app.thought_graph_manager.plugins:
                    # Use the specified plugin
                    analysis = self.console_app.thought_graph_manager.analyze_with_plugin(plugin_id, query)
                else:
                    # Use the default analyzer
                    analysis = self.console_app.thought_graph_manager.analyze_query(query)

                # Convert the graph to a format suitable for visualization
                graph_data = self.convert_graph_to_d3_format(analysis)
                return graph_data
            except Exception as e:
                logging.error(f"Error analyzing query: {e}")
                return {"error": str(e)}
        return {"error": "Thought graph manager not available."}

    def convert_graph_to_d3_format(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Convert the graph analysis to D3.js format.

        Args:
            analysis: The graph analysis from the thought graph analyzer

        Returns:
            Graph data in D3.js format
        """
        # This is a placeholder - the actual implementation will depend on
        # the format of the analysis data and the requirements of D3.js
        nodes = []
        links = []

        # Extract concepts as nodes
        if "concepts" in analysis:
            for concept in analysis["concepts"]:
                nodes.append({
                    "id": concept,
                    "group": 1,
                    "size": 10  # Default size
                })

        # Extract relationships as links
        if "relationships" in analysis:
            for rel in analysis["relationships"]:
                if isinstance(rel, tuple) and len(rel) >= 2:
                    source, target = rel[0], rel[1]
                    weight = rel[2] if len(rel) > 2 else 1
                    links.append({
                        "source": source,
                        "target": target,
                        "value": weight
                    })

        # Adjust node sizes based on centrality
        if "central_concepts" in analysis:
            for concept in analysis["central_concepts"]:
                for node in nodes:
                    if node["id"] == concept:
                        node["size"] = 20  # Larger size for central concepts
                        node["group"] = 2  # Different group for central concepts

        return {
            "nodes": nodes,
            "links": links,
            "suggestions": analysis.get("suggestions", []),
            "missing_concepts": analysis.get("missing_concepts", []),
            "structural_gaps": analysis.get("structural_gaps", []),
            "summary": analysis.get("summary", "")
        }

    def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast a message to all connected WebSocket clients.

        Args:
            message: The message to broadcast
        """
        for connection in self.active_connections:
            try:
                # Use _background to avoid blocking
                connection._background.send_json(message)
            except Exception as e:
                logging.error(f"Error broadcasting message: {e}")

    def start(self):
        """Start the web server in a background thread."""
        def run_server():
            uvicorn.run(self.app, host=self.host, port=self.port)

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        logging.info(f"Web server started at http://{self.host}:{self.port}")

    def stop(self):
        """Stop the web server."""
        # There's no clean way to stop uvicorn from a thread
        # The daemon=True flag ensures the thread will be terminated when the main program exits
        logging.info("Web server stopping...")

    # Plugin API endpoints
    def setup_plugin_routes(self):
        """Set up plugin API routes."""
        @self.app.get("/api/plugins")
        async def list_plugins(session_id: Optional[str] = Cookie(None)):
            """List available plugins."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.plugin_manager:
                return {"error": "Plugin manager not available"}

            plugins = self.plugin_manager.get_all_plugin_info()
            return {"plugins": plugins}

        @self.app.get("/api/plugins/{plugin_id}")
        async def get_plugin_info(plugin_id: str, session_id: Optional[str] = Cookie(None)):
            """Get information about a plugin."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.plugin_manager:
                return {"error": "Plugin manager not available"}

            plugin_info = self.plugin_manager.get_plugin_info(plugin_id)
            if not plugin_info:
                return {"error": f"Plugin {plugin_id} not found"}

            return {"plugin": plugin_info}

        @self.app.post("/api/plugins/{plugin_id}/enable")
        async def enable_plugin(plugin_id: str, session_id: Optional[str] = Cookie(None)):
            """Enable a plugin."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.plugin_manager:
                return {"error": "Plugin manager not available"}

            success = self.plugin_manager.enable_plugin(plugin_id)
            if not success:
                return {"error": f"Failed to enable plugin {plugin_id}"}

            return {"success": True}

        @self.app.post("/api/plugins/{plugin_id}/disable")
        async def disable_plugin(plugin_id: str, session_id: Optional[str] = Cookie(None)):
            """Disable a plugin."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.plugin_manager:
                return {"error": "Plugin manager not available"}

            success = self.plugin_manager.disable_plugin(plugin_id)
            if not success:
                return {"error": f"Failed to disable plugin {plugin_id}"}

            return {"success": True}

        @self.app.post("/api/plugins/{plugin_id}/reload")
        async def reload_plugin(plugin_id: str, session_id: Optional[str] = Cookie(None)):
            """Reload a plugin."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.plugin_manager:
                return {"error": "Plugin manager not available"}

            success = self.plugin_manager.reload_plugin(plugin_id)
            if not success:
                return {"error": f"Failed to reload plugin {plugin_id}"}

            return {"success": True}

        @self.app.post("/api/plugins/{plugin_id}/event")
        async def send_plugin_event(plugin_id: str, request: dict, session_id: Optional[str] = Cookie(None)):
            """Send an event to a plugin."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.plugin_manager:
                return {"error": "Plugin manager not available"}

            plugin = self.plugin_manager.get_plugin(plugin_id)
            if not plugin:
                return {"error": f"Plugin {plugin_id} not found"}

            if plugin_id in self.plugin_manager.disabled_plugins:
                return {"error": f"Plugin {plugin_id} is disabled"}

            event_type = request.get("event_type")
            event_data = request.get("event_data", {})

            if not event_type:
                return {"error": "Missing event_type parameter"}

            try:
                response = plugin.handle_event(event_type, event_data)
                return {"response": response}
            except Exception as e:
                return {"error": f"Error handling event: {str(e)}"}

        @self.app.get("/api/plugins/registry")
        async def list_available_plugins(session_id: Optional[str] = Cookie(None)):
            """List available plugins from the registry."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.plugin_registry:
                return {"error": "Plugin registry not available"}

            # Refresh registry to get latest plugins
            self.plugin_registry.refresh_registry()

            plugins = self.plugin_registry.get_available_plugins()
            return {"plugins": plugins}

        @self.app.post("/api/plugins/registry/install/{plugin_id}")
        async def install_plugin_from_registry(plugin_id: str, session_id: Optional[str] = Cookie(None)):
            """Install a plugin from the registry."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.plugin_registry:
                return {"error": "Plugin registry not available"}

            success = self.plugin_registry.install_plugin(plugin_id)
            if not success:
                return {"error": f"Failed to install plugin {plugin_id}"}

            return {"success": True}

        @self.app.get("/api/plugins/registry/search")
        async def search_plugins(query: str, session_id: Optional[str] = Cookie(None)):
            """Search for plugins in the registry."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.plugin_registry:
                return {"error": "Plugin registry not available"}

            plugins = self.plugin_registry.search_plugins(query)
            return {"plugins": plugins}

    # Marketplace API endpoints
    def setup_marketplace_routes(self):
        """Set up marketplace API routes."""
        @self.app.get("/api/marketplace/available")
        async def list_available_agents(session_id: Optional[str] = Cookie(None)):
            """List available agents."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.agent_marketplace:
                return {"error": "Agent marketplace not available"}

            # Refresh registry to get latest agents
            self.agent_marketplace.refresh_registry()

            agents = self.agent_marketplace.get_available_agents()
            return {"agents": agents}

        @self.app.get("/api/marketplace/installed")
        async def list_installed_agents(session_id: Optional[str] = Cookie(None)):
            """List installed agents."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.agent_marketplace:
                return {"error": "Agent marketplace not available"}

            agents = self.agent_marketplace.get_installed_agents()
            return {"agents": agents}

        @self.app.get("/api/marketplace/agent/{agent_id}")
        async def get_agent_info(agent_id: str, session_id: Optional[str] = Cookie(None)):
            """Get information about an agent."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.agent_marketplace:
                return {"error": "Agent marketplace not available"}

            agent = self.agent_marketplace.get_agent_info(agent_id)
            if not agent:
                return {"error": f"Agent {agent_id} not found"}

            return {"agent": agent}

        @self.app.post("/api/marketplace/install/{agent_id}")
        async def install_agent(agent_id: str, session_id: Optional[str] = Cookie(None)):
            """Install an agent."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.agent_marketplace:
                return {"error": "Agent marketplace not available"}

            success = self.agent_marketplace.install_agent(agent_id)
            if not success:
                return {"error": f"Failed to install agent {agent_id}"}

            return {"success": True}

        @self.app.post("/api/marketplace/uninstall/{agent_id}")
        async def uninstall_agent(agent_id: str, session_id: Optional[str] = Cookie(None)):
            """Uninstall an agent."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.agent_marketplace:
                return {"error": "Agent marketplace not available"}

            success = self.agent_marketplace.uninstall_agent(agent_id)
            if not success:
                return {"error": f"Failed to uninstall agent {agent_id}"}

            return {"success": True}

        @self.app.post("/api/marketplace/rate/{agent_id}")
        async def rate_agent(agent_id: str, request: AgentRatingRequest, session_id: Optional[str] = Cookie(None)):
            """Rate an agent."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.agent_marketplace:
                return {"error": "Agent marketplace not available"}

            success = self.agent_marketplace.rate_agent(agent_id, request.rating)
            if not success:
                return {"error": f"Failed to rate agent {agent_id}"}

            return {"success": True}

        @self.app.get("/api/marketplace/search")
        async def search_agents(query: str, session_id: Optional[str] = Cookie(None)):
            """Search for agents."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.agent_marketplace:
                return {"error": "Agent marketplace not available"}

            agents = self.agent_marketplace.search_agents(query)
            return {"agents": agents}

    # Offline API endpoints
    def setup_offline_routes(self):
        """Set up offline API routes."""
        @self.app.get("/api/offline/status")
        async def get_offline_status(session_id: Optional[str] = Cookie(None)):
            """Get offline mode status."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.offline_manager:
                return {"error": "Offline functionality not available"}

            return {"offline_mode": self.offline_manager.is_offline_mode()}

        @self.app.post("/api/offline/mode")
        async def set_offline_mode(request: OfflineModeRequest, session_id: Optional[str] = Cookie(None)):
            """Set offline mode."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.offline_manager:
                return {"error": "Offline functionality not available"}

            self.offline_manager.set_offline_mode(request.enabled)
            return {"success": True, "offline_mode": request.enabled}

        @self.app.get("/api/offline/cache/stats")
        async def get_cache_stats(session_id: Optional[str] = Cookie(None)):
            """Get cache statistics."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.offline_manager:
                return {"error": "Offline functionality not available"}

            return self.offline_manager.cache_manager.get_stats()

        @self.app.post("/api/offline/cache/clear")
        async def clear_cache(session_id: Optional[str] = Cookie(None)):
            """Clear the cache."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.offline_manager:
                return {"error": "Offline functionality not available"}

            self.offline_manager.cache_manager.clear()
            return {"success": True}

        @self.app.get("/api/offline/kb/topics")
        async def get_kb_topics(session_id: Optional[str] = Cookie(None)):
            """Get knowledge base topics."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.offline_manager:
                return {"error": "Offline functionality not available"}

            topics = self.offline_manager.get_knowledge_base_topics()
            return {"topics": topics}

        @self.app.get("/api/offline/kb/topics/{topic}")
        async def get_kb_topic_entries(topic: str, session_id: Optional[str] = Cookie(None)):
            """Get knowledge base topic entries."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.offline_manager:
                return {"error": "Offline functionality not available"}

            entries = self.offline_manager.get_topic_entries(topic)
            return {"entries": entries}

        @self.app.get("/api/offline/kb/topics/{topic}/{filename}")
        async def get_kb_entry_content(topic: str, filename: str, session_id: Optional[str] = Cookie(None)):
            """Get knowledge base entry content."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.offline_manager:
                return {"error": "Offline functionality not available"}

            content = self.offline_manager.get_entry_content(topic, filename)
            if content is None:
                return {"error": f"Entry {filename} not found in topic {topic}"}

            return {"content": content}

        @self.app.delete("/api/offline/kb/topics/{topic}/{filename}")
        async def delete_kb_entry(topic: str, filename: str, session_id: Optional[str] = Cookie(None)):
            """Delete knowledge base entry."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.offline_manager:
                return {"error": "Offline functionality not available"}

            success = self.offline_manager.delete_entry(topic, filename)
            if not success:
                return {"error": f"Failed to delete entry {filename} from topic {topic}"}

            return {"success": True}

        @self.app.delete("/api/offline/kb/topics/{topic}")
        async def delete_kb_topic(topic: str, session_id: Optional[str] = Cookie(None)):
            """Delete knowledge base topic."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.offline_manager:
                return {"error": "Offline functionality not available"}

            success = self.offline_manager.delete_topic(topic)
            if not success:
                return {"error": f"Failed to delete topic {topic}"}

            return {"success": True}

        @self.app.get("/api/offline/kb/search")
        async def search_kb(query: str, session_id: Optional[str] = Cookie(None)):
            """Search knowledge base."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.offline_manager:
                return {"error": "Offline functionality not available"}

            results = self.offline_manager.search_knowledge_base(query)
            return {"results": results}

        @self.app.post("/api/offline/kb/add")
        async def add_to_kb(request: KnowledgeBaseAddRequest, session_id: Optional[str] = Cookie(None)):
            """Add to knowledge base."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.offline_manager:
                return {"error": "Offline functionality not available"}

            self.offline_manager.add_to_knowledge_base(request.topic, request.content)
            return {"success": True}

    # Workflow API endpoints
    def setup_workflow_routes(self):
        """Set up workflow API routes."""
        @self.app.get("/api/workflows/templates")
        async def list_workflow_templates(session_id: Optional[str] = Cookie(None)):
            """List available workflow templates."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.workflow_manager:
                return {"error": "Workflow functionality not available"}

            templates = self.workflow_manager.list_templates()
            return {"templates": templates}

        @self.app.get("/api/workflows")
        async def list_workflows(session_id: Optional[str] = Cookie(None)):
            """List active workflows."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.workflow_manager:
                return {"error": "Workflow functionality not available"}

            workflows = self.workflow_manager.list_workflows()
            return {"workflows": workflows}

        @self.app.post("/api/workflows/create")
        async def create_workflow(request: WorkflowTemplateRequest, session_id: Optional[str] = Cookie(None)):
            """Create a new workflow from a template."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.workflow_manager:
                return {"error": "Workflow functionality not available"}

            workflow_id = self.workflow_manager.create_workflow(request.template_name)
            if not workflow_id:
                return {"error": f"Template '{request.template_name}' not found"}

            return {"workflow_id": workflow_id}

        @self.app.get("/api/workflows/{workflow_id}")
        async def get_workflow(workflow_id: str, session_id: Optional[str] = Cookie(None)):
            """Get a workflow by ID."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.workflow_manager:
                return {"error": "Workflow functionality not available"}

            workflow = self.workflow_manager.get_workflow(workflow_id)
            if not workflow:
                return {"error": f"Workflow '{workflow_id}' not found"}

            return workflow.to_dict()

        @self.app.post("/api/workflows/{workflow_id}/execute")
        async def execute_workflow_step(workflow_id: str, session_id: Optional[str] = Cookie(None)):
            """Execute the current step of a workflow."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.workflow_manager:
                return {"error": "Workflow functionality not available"}

            result = self.workflow_manager.execute_step(workflow_id, self.console_app)
            return result

        @self.app.post("/api/workflows/{workflow_id}/advance")
        async def advance_workflow(workflow_id: str, session_id: Optional[str] = Cookie(None)):
            """Advance a workflow to the next step."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.workflow_manager:
                return {"error": "Workflow functionality not available"}

            result = self.workflow_manager.advance_workflow(workflow_id)
            return result

        @self.app.delete("/api/workflows/{workflow_id}")
        async def delete_workflow(workflow_id: str, session_id: Optional[str] = Cookie(None)):
            """Delete a workflow."""
            # Check authentication if enabled
            if self.auth_manager and not session_id:
                return {"error": "Authentication required"}

            # Validate session if authentication is enabled
            if self.auth_manager and session_id:
                user_data = self.auth_manager.validate_session(session_id)
                if not user_data:
                    return {"error": "Invalid session"}

            if not self.workflow_manager:
                return {"error": "Workflow functionality not available"}

            success = self.workflow_manager.delete_workflow(workflow_id)
            if not success:
                return {"error": f"Failed to delete workflow '{workflow_id}'"}

            return {"success": True}

    def handle_chat_request(self, request: ChatRequest) -> Dict[str, Any]:
        """Handle a chat request.

        Args:
            request: Chat request

        Returns:
            Response data
        """
        if not self.console_app or not hasattr(self.console_app, "chat_manager"):
            return {"error": "Chat functionality not available"}

        response = self.console_app.chat_manager.send_message(
            request.message,
            model=getattr(request, "model", None),
            system_prompt=getattr(request, "system_prompt", None),
            temperature=getattr(request, "temperature", 0.7),
            max_tokens=getattr(request, "max_tokens", None)
        )

        return {"response": response}

    def handle_workflow_request(self, request: WorkflowRequest) -> Dict[str, Any]:
        """Handle a workflow request.

        Args:
            request: Workflow request

        Returns:
            Response data
        """
        if not self.console_app or not hasattr(self.console_app, "workflow_manager"):
            return {"error": "Workflow functionality not available"}

        result = self.console_app.workflow_manager.execute_workflow(
            request.workflow_id,
            request.inputs
        )

        return result