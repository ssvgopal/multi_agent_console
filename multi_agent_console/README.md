# MultiAgentConsole

A powerful terminal-based multi-agent system powered by Google's Agent Development Kit (ADK).

## Features

### Core Architecture
- **Multi-Agent Architecture**: Specialized agents for different tasks (coding, research, system administration, data analysis) coordinated by a root agent.
- **Flexible Model Support**: Support for various LLM providers through Google's ADK.
- **Terminal UI**: Clean, responsive terminal interface built with Textual.
- **Dynamic Configuration**: Change models and agent settings on-the-fly.

### Memory and Context Management
- **Long-term Memory**: Store and retrieve past conversations and user preferences.
- **Context-Aware Responses**: Enhance responses with relevant context from previous interactions.
- **User Profiles**: Maintain personalized profiles with customized agent behaviors.
- **Conversation Management**: Save, load, and search through conversation history.

### Advanced Tool Integration
- **Version Control**: Git integration for repository management.
- **Database Tools**: Connect to and query SQLite, MySQL, and PostgreSQL databases.
- **API Integration**: Make HTTP requests to external services with proper authentication.
- **Media Processing**: Extract text from images and process image files.
- **Voice Capabilities**: Text-to-speech and speech-to-text functionality.

### Enhanced Security
- **Secure Sandboxing**: Run code in a secure, isolated environment.
- **Permission Management**: Control access to files, network resources, and system operations.
- **Credential Management**: Securely store and access API keys and other credentials.
- **Encryption**: Protect sensitive data with strong encryption.

### UI Enhancements
- **Themes and Color Schemes**: Customize the appearance with multiple built-in themes.
- **Keyboard Shortcuts**: Efficiently navigate and control the application with keyboard shortcuts.
- **Syntax Highlighting**: Improved code readability with syntax highlighting for various languages.
- **Progress Indicators**: Visual feedback for long-running operations.
- **Auto-completion**: Command and input suggestions based on history and available commands.

### Multi-Modal Support
- **Image Processing**: Analyze, resize, and extract information from images.
- **Text Extraction**: Extract text from images using OCR technology.
- **Audio Processing**: Convert text to speech and speech to text.
- **Chart Generation**: Create bar, line, and pie charts from data.
- **Document Processing**: Extract text and metadata from PDF documents.

### Advanced Workflow Features
- **Workflow Templates**: Create and use templates for common tasks.
- **Task Scheduling**: Schedule workflows to run at specific times.
- **Batch Processing**: Process multiple items with the same workflow.
- **Workflow Management**: Create, save, and load workflows.

### Offline Capabilities
- **Response Caching**: Store and retrieve responses for offline use.
- **Local Knowledge Base**: Maintain a searchable database of information.
- **Local Model Support**: Use locally deployed models when online services are unavailable.
- **Offline Mode**: Toggle between online and offline operation.

### Advanced Debugging and Monitoring
- **Performance Monitoring**: Track and analyze operation performance metrics.
- **Error Tracking**: Record and analyze errors for troubleshooting.
- **Enhanced Logging**: Comprehensive logging with different severity levels.
- **Debugging Tools**: Set breakpoints and watches for debugging.

### Agent Marketplace and Extensibility
- **Agent Marketplace**: Browse and install pre-configured agent definitions.
- **Plugin System**: Extend functionality with installable plugins.
- **Custom Agent Creation**: Create and share custom agent definitions.
- **Extension Registry**: Register and manage extensions.
- **MCP Server**: Multi-Agent Communication Protocol server for standardized agent communication.
- **MCP Plugins**: Extend the MCP server with custom plugins.

### Cross-Platform Enhancements
- **Mobile Device Support**: Optimized interface and functionality for mobile devices.
- **Cloud Synchronization**: Sync data across devices via cloud services.
- **Platform-Specific Optimizations**: Tailored experience based on the operating platform.
- **Accessibility Features**: Enhanced accessibility options for diverse user needs.

### MCP Server and Plugin Support
- **Multi-Agent Communication Protocol**: Standardized communication between agents.
- **Agent Registration**: Register and manage agents in the MCP system.
- **Message Routing**: Route messages between agents efficiently.
- **Plugin Architecture**: Extend the MCP server with custom plugins.
- **A2A Protocol Support**: Compatible with Google's Agent-to-Agent (A2A) protocol for standardized agent communication.

### Thought Graph Analysis
- **Query Analysis**: Analyze user queries as thought graphs to identify key concepts and relationships.
- **Gap Detection**: Identify gaps in thinking and suggest improvements.
- **Visualization**: Visualize thought graphs to better understand query structure.
- **Plugin Interface**: Connect to external graph analysis tools like InfraNodus.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/multi-agent-console.git
cd multi-agent-console

# Install the package
pip install -e .
```

## Usage

```bash
# Run the console
multi-agent-console
```

### Configuration

The application uses `config.json` to define settings. You can edit this file directly via the "Edit Config" button within the app and reload it using the "Reload Config" button.

Default configuration:

```json
{
  "model_identifier": "gemini-2.0-pro",
  "active_agents": [
    "coordinator",
    "code_assistant",
    "research_assistant",
    "system_assistant",
    "data_assistant"
  ],
  "system_prompts": {
    "coordinator": "You are the coordinator for MultiAgentConsole...",
    "code_assistant": "You are a coding expert specialized in...",
    "research_assistant": "You are a research assistant specialized in...",
    "system_assistant": "You are a system administration expert...",
    "data_assistant": "You are a data analysis expert..."
  }
}
```

### Environment Variables

To use Google's Gemini models, set the following environment variable:

```bash
export GOOGLE_API_KEY=your_api_key
```

### Memory and Context Features

- **Save Conversations**: Press `Ctrl+S` or click "Save Current Session" to save the current conversation.
- **Load Conversations**: Press `Ctrl+O` or click "Recent Conversations" to load a saved conversation.
- **Search Memory**: Press `Ctrl+F` or click "Search Memory" to search through your conversation history.
- **Edit Preferences**: Press `Ctrl+E` or click "Edit Preferences" to view and modify your user preferences and API keys.

### Security Features

- **API Key Management**: Securely store API keys using `set_api_key service_name your_api_key`.
- **Permission Control**: Control which files, domains, and commands can be accessed.
- **Secure Code Execution**: Run code in a sandboxed environment to prevent security issues.

### UI Features

- **Themes**: Change themes with `Ctrl+T` or use `set_theme theme_name` in the preferences panel.
- **Keyboard Shortcuts**: Use keyboard shortcuts for common actions (see table below).
- **Syntax Highlighting**: Code blocks are automatically syntax-highlighted for better readability.
- **Auto-completion**: Command history is saved for auto-completion suggestions.

#### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New Session |
| `Ctrl+S` | Save Conversation |
| `Ctrl+O` | Load Conversation |
| `Ctrl+F` | Search Memory |
| `Ctrl+E` | Edit Preferences |
| `Ctrl+T` | Cycle Theme |
| `Ctrl+P` | Toggle Memory Panel |
| `Ctrl+R` | Reload Config |
| `Ctrl+Q` | Quit |

### Advanced Tools

- **Git Integration**: Use git commands like `git_status()`, `git_log()`, and `git_diff()`.
- **Database Access**: Connect to databases with `connect_sqlite()` and execute queries with `execute_query()`.
- **API Access**: Make HTTP requests with `http_request()` and access weather and news APIs.

### Multi-Modal Tools

- **Image Processing**: Analyze images with `image_info()`, extract text with `ocr_image()`, and resize with `resize_image()`.
- **Audio Processing**: Convert text to speech with `text_to_speech()` and speech to text with `speech_to_text()`.
- **Chart Generation**: Create visualizations with `generate_bar_chart()`, `generate_line_chart()`, and `generate_pie_chart()`.
- **Document Processing**: Extract text from PDFs with `extract_text_from_pdf()` and get PDF info with `get_pdf_info()`.

### Workflow Tools

- **Workflow Management**: Create workflows with `create_workflow()` and list them with `list_workflows()`.
- **Template Management**: List templates with `list_templates()` and create workflows from templates with `create_workflow_from_template()`.
- **Task Scheduling**: Schedule workflows with `schedule_workflow()` and list scheduled tasks with `list_scheduled_tasks()`.

### Offline Tools

- **Offline Mode**: Toggle offline mode with `toggle_offline_mode()` and check status with `get_offline_status()`.
- **Knowledge Base**: Add documents with `add_to_knowledge_base()` and search with `search_knowledge_base()`.
- **Local Models**: List available local models with `list_local_models()`.

### Debugging Tools

- **Debug Mode**: Toggle debug mode with `toggle_debug_mode()` and check status with `get_debug_status()`.
- **Breakpoints**: Add breakpoints with `add_breakpoint()` and list them with `list_breakpoints()`.
- **Performance**: Get performance statistics with `get_performance_stats()`.
- **Error Analysis**: Get error statistics with `get_error_stats()`.
- **Logging**: View logs with `get_logs()`.

### Marketplace Tools

- **Agent Definitions**: List agent definitions with `list_agent_definitions()` and search with `search_agent_definitions()`.
- **Plugins**: List plugins with `list_plugins()` and search with `search_plugins()`.
- **Extensions**: List registered extensions with `list_extensions()`.

### Cross-Platform Tools

- **Platform Information**: Get platform details with `get_platform_info()`.
- **Cloud Sync**: Toggle cloud sync with `toggle_cloud_sync()` and check status with `get_sync_status()`.
- **Accessibility**: Set accessibility options with `set_accessibility_setting()` and view with `get_accessibility_settings()`.
- **Mobile Optimization**: Toggle mobile optimizations with `toggle_mobile_optimizations()`.

### MCP Tools

- **Agent Management**: List registered MCP agents with `list_mcp_agents()`.
- **Plugin Management**: List registered MCP plugins with `list_mcp_plugins()`.
- **Messaging**: Send messages between agents with `send_mcp_message()` and view recent messages with `get_recent_mcp_messages()`.

### Thought Graph Analysis Tools

- **Query Analysis**: Analyze user queries with `analyze_user_query()` to identify key concepts and relationships.
- **Query Improvement**: Get suggestions to improve queries with `get_query_suggestions()`.
- **Visualization**: Visualize thought graphs with `visualize_thought_graph()`.
- **Plugin Management**: List graph analysis plugins with `list_graph_plugins()` and analyze with specific plugins using `analyze_with_graph_plugin()`.

### A2A Protocol Tools

- **Task Management**: Create A2A tasks with `create_a2a_task()`, get task information with `get_a2a_task()`, and cancel tasks with `cancel_a2a_task()`.
- **Agent Discovery**: List A2A-compatible agents with `list_a2a_agents()`.

## Specialized Agents

1. **Coordinator**: Understands user requests and delegates to specialized agents.
2. **Code Assistant**: Helps with writing, debugging, and understanding code. Has access to code execution and Git tools.
3. **Research Assistant**: Finds and synthesizes information using search tools and external APIs.
4. **System Assistant**: Helps with system administration tasks and file operations.
5. **Data Assistant**: Specializes in data analysis, visualization, and database operations.

## License

MIT
