# Creating Plugins for MultiAgentConsole

This guide will walk you through the process of creating plugins for MultiAgentConsole, from setting up your development environment to publishing your plugin to the registry.

## Overview

Plugins allow you to extend MultiAgentConsole with new features, tools, UI components, and integrations. By creating plugins, you can:

- Add new tools for chat and workflows
- Create custom UI components
- Integrate with external services
- Add support for new AI models
- Extend the application in countless other ways

## Prerequisites

Before you start developing plugins, you should have:

- Basic knowledge of Python programming
- Familiarity with MultiAgentConsole as a user
- Understanding of the plugin system (see [Plugin System](../features/plugins.md))
- Python 3.8 or higher installed
- Git for version control

## Setting Up Your Development Environment

### 1. Clone the MultiAgentConsole Repository

```bash
git clone https://github.com/ssvgopal/multi_agent_console.git
cd multi_agent_console
```

### 2. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### 3. Create a Plugin Directory

Create a directory for your plugin in the `plugins` directory:

```bash
mkdir -p plugins/my_plugin
cd plugins/my_plugin
```

## Plugin Structure

A basic plugin consists of the following files:

```
my_plugin/
├── plugin.json         # Plugin metadata
├── __init__.py         # Package initialization
├── plugin.py           # Main plugin code
├── resources/          # Additional resources (optional)
│   ├── images/         # Images used by the plugin
│   └── templates/      # HTML templates
└── README.md           # Documentation
```

### Creating the Plugin Metadata

Create a `plugin.json` file with the following content:

```json
{
  "id": "my_plugin",
  "name": "My Plugin",
  "description": "A simple example plugin for MultiAgentConsole",
  "version": "1.0.0",
  "author": "Your Name",
  "tags": ["example", "demo"],
  "requirements": [],
  "repository_url": null,
  "homepage_url": null,
  "icon_url": null
}
```

### Creating the Plugin Package

Create an `__init__.py` file:

```python
"""
My Plugin - A simple example plugin for MultiAgentConsole

Author: Your Name
Version: 1.0.0
"""
```

### Implementing the Plugin

Create a `plugin.py` file with your plugin implementation:

```python
"""
My Plugin - A simple example plugin for MultiAgentConsole

Author: Your Name
Version: 1.0.0
"""

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
    
    @property
    def author(self) -> str:
        """Get the plugin author."""
        return "Your Name"
    
    def initialize(self, context):
        """Initialize the plugin."""
        print(f"My Plugin initialized with context: {context}")
        return True
    
    def shutdown(self):
        """Shutdown the plugin."""
        print("My Plugin shutdown")
        return True
    
    def get_capabilities(self):
        """Get the plugin capabilities."""
        return ["greeting"]
    
    def handle_event(self, event_type, event_data):
        """Handle an event."""
        if event_type == "greeting":
            name = event_data.get("name", "World")
            return {"message": f"Hello, {name}!"}
        return None
```

### Creating Documentation

Create a `README.md` file with documentation for your plugin:

```markdown
# My Plugin

A simple example plugin for MultiAgentConsole.

## Features

- Adds a greeting tool
- Demonstrates basic plugin functionality

## Installation

1. Install the plugin from the Plugin Registry
2. Enable the plugin in the Plugins tab

## Usage

Use the greeting tool in chat or workflows:

```
/greeting John
```

## Configuration

No configuration options available.

## License

MIT
```

## Plugin Development

### The Plugin Base Class

All plugins must inherit from the `Plugin` base class and implement its abstract methods:

```python
from multi_agent_console.plugin.base import Plugin

class MyPlugin(Plugin):
    @property
    def id(self) -> str:
        """Get the plugin ID."""
        # Must return a unique identifier
        pass
    
    @property
    def name(self) -> str:
        """Get the plugin name."""
        # Must return a display name
        pass
    
    @property
    def version(self) -> str:
        """Get the plugin version."""
        # Must return a version string
        pass
    
    @property
    def description(self) -> str:
        """Get the plugin description."""
        # Must return a description
        pass
```

### Optional Methods

The following methods are optional but useful for many plugins:

```python
def initialize(self, context):
    """Initialize the plugin."""
    # Called when the plugin is loaded
    # Return True if initialization was successful, False otherwise
    return True

def shutdown(self):
    """Shutdown the plugin."""
    # Called when the plugin is unloaded
    # Return True if shutdown was successful, False otherwise
    return True

def get_capabilities(self):
    """Get the plugin capabilities."""
    # Return a list of capability strings
    return ["capability1", "capability2"]

def handle_event(self, event_type, event_data):
    """Handle an event."""
    # Called when an event is sent to the plugin
    # Return a response or None
    if event_type == "capability1":
        return {"result": "Success"}
    return None

@property
def dependencies(self):
    """Get the plugin dependencies."""
    # Return a list of plugin IDs that this plugin depends on
    return ["other_plugin"]

@property
def settings_schema(self):
    """Get the plugin settings schema."""
    # Return a JSON schema for plugin settings
    return {
        "api_key": {
            "type": "string",
            "title": "API Key",
            "description": "Your API key for the service"
        }
    }

def get_settings(self):
    """Get the plugin settings."""
    # Return the current settings
    return {"api_key": "my_api_key"}

def update_settings(self, settings):
    """Update the plugin settings."""
    # Update the settings
    # Return True if successful, False otherwise
    return True

def get_ui_components(self):
    """Get UI components provided by the plugin."""
    # Return a dictionary of UI components
    return {
        "sidebar": {
            "title": "My Plugin",
            "content": "<div>My Plugin Sidebar</div>"
        }
    }
```

## Plugin Types

### Tool Plugins

Tool plugins add new tools that can be used in chat or workflows:

```python
def get_capabilities(self):
    """Get the plugin capabilities."""
    return ["calculator"]

def handle_event(self, event_type, event_data):
    """Handle an event."""
    if event_type == "calculator":
        expression = event_data.get("expression", "")
        try:
            result = eval(expression)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}
    return None
```

### UI Plugins

UI plugins add new components to the interface:

```python
def get_ui_components(self):
    """Get UI components provided by the plugin."""
    return {
        "sidebar": {
            "title": "Calculator",
            "icon": "🧮",
            "content": """
            <div class="p-4">
                <h3 class="text-lg font-medium mb-2">Calculator</h3>
                <div class="mb-4">
                    <input type="text" id="calc-input" class="w-full border rounded px-3 py-2" placeholder="Enter expression">
                </div>
                <button id="calc-btn" class="bg-blue-600 text-white px-4 py-2 rounded">
                    Calculate
                </button>
                <div id="calc-result" class="mt-4 p-3 bg-gray-100 rounded hidden"></div>
            </div>
            <script>
                document.getElementById('calc-btn').addEventListener('click', function() {
                    const expression = document.getElementById('calc-input').value;
                    fetch('/api/plugin/calculator_plugin/calculator', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ expression: expression })
                    })
                    .then(response => response.json())
                    .then(data => {
                        const resultEl = document.getElementById('calc-result');
                        if (data.error) {
                            resultEl.textContent = 'Error: ' + data.error;
                        } else {
                            resultEl.textContent = 'Result: ' + data.result;
                        }
                        resultEl.classList.remove('hidden');
                    });
                });
            </script>
            """
        }
    }
```

### Integration Plugins

Integration plugins connect MultiAgentConsole to external services:

```python
import requests

class NotionIntegrationPlugin(Plugin):
    @property
    def id(self) -> str:
        return "notion_integration"
    
    @property
    def name(self) -> str:
        return "Notion Integration"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Integrates MultiAgentConsole with Notion"
    
    @property
    def settings_schema(self):
        return {
            "api_key": {
                "type": "string",
                "title": "Notion API Key",
                "description": "Your Notion API key"
            }
        }
    
    def get_capabilities(self):
        return ["notion_search", "notion_create_page"]
    
    def handle_event(self, event_type, event_data):
        if event_type == "notion_search":
            query = event_data.get("query", "")
            return self._search_notion(query)
        elif event_type == "notion_create_page":
            title = event_data.get("title", "")
            content = event_data.get("content", "")
            parent_id = event_data.get("parent_id")
            return self._create_notion_page(title, content, parent_id)
        return None
    
    def _search_notion(self, query):
        # Implementation details...
        pass
    
    def _create_notion_page(self, title, content, parent_id):
        # Implementation details...
        pass
```

## Testing Your Plugin

### Manual Testing

1. Start MultiAgentConsole with your plugin directory:

```bash
python -m multi_agent_console --web --port 8007
```

2. Go to the Plugins tab in the web interface
3. Your plugin should appear in the list of installed plugins
4. Enable your plugin
5. Test its functionality

### Automated Testing

Create a `tests` directory in your plugin directory:

```bash
mkdir tests
```

Create a test file, e.g., `test_plugin.py`:

```python
import unittest
from my_plugin.plugin import MyPlugin

class TestMyPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = MyPlugin()
    
    def test_plugin_id(self):
        self.assertEqual(self.plugin.id, "my_plugin")
    
    def test_plugin_name(self):
        self.assertEqual(self.plugin.name, "My Plugin")
    
    def test_greeting_capability(self):
        self.assertIn("greeting", self.plugin.get_capabilities())
    
    def test_handle_greeting_event(self):
        response = self.plugin.handle_event("greeting", {"name": "John"})
        self.assertIsNotNone(response)
        self.assertEqual(response["message"], "Hello, John!")

if __name__ == "__main__":
    unittest.main()
```

Run the tests:

```bash
python -m unittest discover -s plugins/my_plugin/tests
```

## Packaging Your Plugin

### Creating a Distribution Package

1. Create a `setup.py` file in your plugin directory:

```python
from setuptools import setup, find_packages

setup(
    name="my_plugin",
    version="1.0.0",
    description="A simple example plugin for MultiAgentConsole",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
)
```

2. Create a `MANIFEST.in` file to include non-Python files:

```
include plugin.json
include README.md
recursive-include resources *
```

3. Build the package:

```bash
python setup.py sdist bdist_wheel
```

### Publishing to the Plugin Registry

1. Create an account on the Plugin Registry
2. Package your plugin as described above
3. Upload your plugin package to the registry
4. Provide metadata, documentation, and screenshots
5. Submit your plugin for review

## Best Practices

### Code Quality

- Follow PEP 8 style guidelines
- Write clear, concise code
- Add comments and docstrings
- Use type hints
- Handle errors gracefully

### Documentation

- Provide clear, comprehensive documentation
- Include installation instructions
- Explain configuration options
- Show usage examples
- Document any limitations or requirements

### Security

- Validate all inputs
- Handle sensitive data securely
- Use secure communication methods
- Implement proper error handling
- Request only the permissions you need

### Performance

- Optimize resource usage
- Avoid blocking operations
- Use asynchronous code where appropriate
- Cache results when possible
- Clean up resources in the shutdown method

### Compatibility

- Test with different versions of MultiAgentConsole
- Specify version requirements
- Handle backward compatibility
- Document breaking changes

## Advanced Topics

### Plugin Settings Persistence

To save and load plugin settings:

```python
def initialize(self, context):
    # Load settings from context
    self.settings = context.get("settings", {})
    return True

def get_settings(self):
    return self.settings

def update_settings(self, settings):
    # Validate settings
    if "api_key" in settings and not settings["api_key"]:
        return False
    
    # Update settings
    self.settings = settings
    
    # Save settings to context
    self.context.update_plugin_settings(self.id, settings)
    
    return True
```

### Plugin Dependencies

To specify dependencies on other plugins:

```python
@property
def dependencies(self):
    return ["base_plugin", "utility_plugin"]
```

The plugin manager will ensure that dependencies are loaded in the correct order.

### Custom API Endpoints

To add custom API endpoints:

```python
def initialize(self, context):
    # Register API endpoints
    api = context.get("api")
    if api:
        api.register_endpoint(
            "GET",
            f"/api/plugin/{self.id}/data",
            self._handle_get_data
        )
        api.register_endpoint(
            "POST",
            f"/api/plugin/{self.id}/data",
            self._handle_post_data
        )
    return True

def _handle_get_data(self, request):
    # Handle GET request
    return {"data": "example"}

def _handle_post_data(self, request):
    # Handle POST request
    data = request.json()
    return {"success": True}
```

### Plugin Events

To listen for system events:

```python
def initialize(self, context):
    # Register event listeners
    events = context.get("events")
    if events:
        events.register_listener("chat_message", self._on_chat_message)
        events.register_listener("workflow_executed", self._on_workflow_executed)
    return True

def _on_chat_message(self, event_data):
    # Handle chat message event
    pass

def _on_workflow_executed(self, event_data):
    # Handle workflow executed event
    pass
```

## Troubleshooting

### Common Issues

#### Plugin Not Loading

- Check that your plugin directory is in the correct location
- Ensure that `plugin.json` is properly formatted
- Verify that your plugin class inherits from `Plugin`
- Check for errors in the console output

#### Plugin Initialization Fails

- Check the error message in the console
- Verify that all dependencies are installed
- Ensure that your `initialize` method returns `True`
- Check for exceptions in your initialization code

#### Plugin Not Working as Expected

- Enable debug logging to see more details
- Check that your event handlers are registered correctly
- Verify that your plugin is enabled
- Test your plugin in isolation

### Getting Help

If you encounter issues:

1. Check the documentation
2. Look for similar issues in the community forums
3. Ask for help in the plugin development channel
4. Open an issue on GitHub

## Conclusion

Creating plugins for MultiAgentConsole allows you to extend its functionality in countless ways. By following this guide, you should be able to create, test, and publish your own plugins.

Remember to:

- Start simple and build up complexity
- Test thoroughly
- Document your plugin
- Follow best practices
- Share your plugin with the community

Happy plugin development!
