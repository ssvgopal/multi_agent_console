# Plugin System

The Plugin System in MultiAgentConsole provides a powerful way to extend functionality and customize the application to your specific needs.

## Overview

Plugins enable you to:

- Add new features to MultiAgentConsole
- Integrate with external services and APIs
- Create custom tools for workflows
- Add new UI components
- Modify existing functionality
- Share extensions with others

## Getting Started

### Accessing the Plugin Manager

1. Click the "Plugins" tab in the navigation bar
2. The plugin interface has three main sections:
   - Available Plugins: Shows plugins available for installation
   - Installed Plugins: Shows your currently installed plugins
   - Plugin Details: Shows detailed information about selected plugins

### Installing a Plugin

1. Browse the Available Plugins section
2. Click on a plugin to view its details
3. Click the "Install" button to install the plugin
4. The plugin will be downloaded, installed, and activated

### Managing Plugins

From the Installed Plugins section, you can:

- **Enable/Disable**: Toggle plugins on or off
- **Configure**: Adjust plugin settings
- **Update**: Update plugins to newer versions
- **Uninstall**: Remove plugins from your system

## Plugin Components

### Plugin Structure

A typical plugin consists of:

- **Metadata**: Information about the plugin (name, version, author, etc.)
- **Code**: The actual implementation of the plugin
- **Resources**: Additional files needed by the plugin
- **Dependencies**: Other plugins or packages required
- **Settings**: Configurable options for the plugin

### Plugin Types

MultiAgentConsole supports various types of plugins:

- **Tool Plugins**: Add new tools for chat and workflows
- **UI Plugins**: Add new UI components or modify existing ones
- **Integration Plugins**: Connect to external services
- **Model Plugins**: Add support for new AI models
- **Workflow Plugins**: Add new workflow step types
- **Theme Plugins**: Customize the appearance of the application

## Using Plugins

### Tool Plugins

Tool plugins add new tools that can be used in chat or workflows:

1. Install a tool plugin
2. In chat, type "/" to see available tools
3. Select the tool provided by the plugin
4. Provide the required parameters
5. The tool will execute and display the results

Example:

```
/weather New York
```

### UI Plugins

UI plugins can add new components to the interface:

- New tabs in the navigation bar
- Sidebars with additional functionality
- Custom visualizations
- Enhanced input methods
- Context menu options

### Integration Plugins

Integration plugins connect MultiAgentConsole to external services:

1. Install an integration plugin
2. Configure the plugin with your API keys or credentials
3. Use the integration through tools, workflows, or the UI

Examples:

- Connect to Notion, Jira, or GitHub
- Integrate with cloud storage services
- Connect to databases or data sources
- Integrate with communication platforms

### Model Plugins

Model plugins add support for new AI models:

1. Install a model plugin
2. The new model will appear in the model selection dropdown
3. Configure the model with your API keys if required
4. Use the model in chat or workflows

## Plugin Registry

The Plugin Registry is a central repository of available plugins:

1. Browse plugins by category, popularity, or search
2. View plugin details, ratings, and reviews
3. Install plugins directly from the registry
4. Submit your own plugins to the registry

### Searching for Plugins

To find specific plugins:

1. Use the search box in the Available Plugins section
2. Enter keywords related to the functionality you need
3. Browse the search results
4. Click on plugins to view details

## Creating Plugins

### Plugin Development

To create your own plugins:

1. Familiarize yourself with the plugin API
2. Set up a development environment
3. Create a new plugin project
4. Implement your plugin functionality
5. Test your plugin
6. Package and distribute your plugin

See the [Plugin Development Guide](../extending/plugins.md) for detailed instructions.

### Plugin Structure

A basic plugin directory structure:

```
my_plugin/
├── plugin.json         # Plugin metadata
├── __init__.py         # Package initialization
├── plugin.py           # Main plugin code
├── resources/          # Additional resources
│   ├── images/         # Images used by the plugin
│   └── templates/      # HTML templates
└── README.md           # Documentation
```

### Plugin Metadata

The `plugin.json` file contains essential information about your plugin:

```json
{
  "id": "my_plugin",
  "name": "My Plugin",
  "description": "A simple example plugin for MultiAgentConsole",
  "version": "1.0.0",
  "author": "Your Name",
  "tags": ["example", "demo"],
  "requirements": ["requests>=2.25.0"],
  "repository_url": "https://github.com/yourusername/my_plugin",
  "homepage_url": "https://yourusername.github.io/my_plugin",
  "icon_url": "https://example.com/my_plugin_icon.png"
}
```

### Plugin Implementation

A simple plugin implementation in `plugin.py`:

```python
from multi_agent_console.plugin.base import Plugin

class MyPlugin(Plugin):
    """My Plugin implementation."""
    
    @property
    def id(self) -> str:
        """Get the plugin ID."""
        return "my_plugin"
    
    @property
    def name(self) -> str:
        """Get the plugin name."""
        return "My Plugin"
    
    @property
    def version(self) -> str:
        """Get the plugin version."""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Get the plugin description."""
        return "A simple example plugin for MultiAgentConsole"
    
    def initialize(self, context):
        """Initialize the plugin."""
        print(f"My Plugin initialized with context: {context}")
        return True
    
    def get_capabilities(self):
        """Get the plugin capabilities."""
        return ["example_tool"]
    
    def handle_event(self, event_type, event_data):
        """Handle an event."""
        if event_type == "example_tool":
            name = event_data.get("name", "World")
            return {"message": f"Hello, {name}!"}
        return None
```

## Advanced Features

### Plugin Settings

Plugins can provide configurable settings:

1. Define a settings schema in your plugin
2. Users can adjust these settings through the UI
3. Your plugin can access and use these settings

Example settings schema:

```python
@property
def settings_schema(self) -> Dict[str, Any]:
    """Get the plugin settings schema."""
    return {
        "api_key": {
            "type": "string",
            "title": "API Key",
            "description": "Your API key for the service",
            "format": "password"
        },
        "max_results": {
            "type": "integer",
            "title": "Maximum Results",
            "description": "Maximum number of results to return",
            "default": 10,
            "minimum": 1,
            "maximum": 100
        },
        "enable_feature": {
            "type": "boolean",
            "title": "Enable Feature",
            "description": "Whether to enable the advanced feature",
            "default": False
        }
    }
```

### Plugin Dependencies

Plugins can depend on other plugins:

```python
@property
def dependencies(self) -> List[str]:
    """Get the plugin dependencies."""
    return ["base_plugin", "utility_plugin"]
```

The plugin manager ensures that dependencies are installed and loaded in the correct order.

### Plugin UI Components

Plugins can provide custom UI components:

```python
def get_ui_components(self):
    """Get UI components provided by the plugin."""
    return {
        "sidebar": {
            "title": "My Plugin",
            "icon": "📊",
            "content": """
            <div class="p-4">
                <h3 class="text-lg font-medium mb-2">My Plugin</h3>
                <p class="text-gray-600 mb-4">This is a custom sidebar component.</p>
                <button id="my-plugin-btn" class="bg-blue-600 text-white px-4 py-2 rounded">
                    Click Me
                </button>
                <div id="my-plugin-result" class="mt-4 p-3 bg-gray-100 rounded hidden"></div>
            </div>
            <script>
                document.getElementById('my-plugin-btn').addEventListener('click', function() {
                    fetch('/api/plugin/my_plugin/example_tool', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ name: 'User' })
                    })
                    .then(response => response.json())
                    .then(data => {
                        const resultEl = document.getElementById('my-plugin-result');
                        resultEl.textContent = data.message;
                        resultEl.classList.remove('hidden');
                    });
                });
            </script>
            """
        }
    }
```

## Integration with Other Features

### Workflow Integration

Plugins can provide custom step types for workflows:

1. Create a plugin that implements the workflow step interface
2. The step will appear in the workflow editor toolbox
3. Users can add and configure the step in their workflows

### Chat Integration

Plugins can add new capabilities to the chat interface:

1. Create a plugin that handles chat events
2. Register chat commands or tools
3. Users can access these commands in the chat interface

### API Integration

Plugins can extend the API:

1. Create a plugin that registers API endpoints
2. The endpoints will be available through the API
3. Other applications can use these endpoints

## Best Practices

### Plugin Development

- **Follow Conventions**: Adhere to the plugin API and naming conventions
- **Minimize Dependencies**: Only require what you need
- **Handle Errors**: Gracefully handle errors and edge cases
- **Document Thoroughly**: Provide clear documentation for your plugin
- **Test Extensively**: Test your plugin in various scenarios

### Plugin Usage

- **Review Permissions**: Understand what access plugins require
- **Check Reviews**: Look at ratings and reviews before installing
- **Start Simple**: Begin with essential plugins and add more as needed
- **Keep Updated**: Regularly update plugins for security and features
- **Report Issues**: Report bugs or security concerns to plugin authors

## Troubleshooting

### Common Issues

- **Installation Failures**: Check for dependency conflicts or missing requirements
- **Plugin Conflicts**: Some plugins may conflict with each other
- **Performance Issues**: Plugins can impact application performance
- **Security Concerns**: Be cautious with plugins that request sensitive permissions

### Getting Help

If you encounter issues with plugins:

1. Check the plugin documentation
2. Visit the plugin's homepage or repository
3. Contact the plugin author
4. Check the [Troubleshooting](../troubleshooting/plugins.md) section
5. Ask for help in the community forums
