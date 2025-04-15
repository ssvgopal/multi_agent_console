# MultiAgentConsole Documentation

Welcome to the MultiAgentConsole documentation. This guide provides comprehensive information about the features, installation, configuration, and usage of MultiAgentConsole.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Features](#features)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Extending MultiAgentConsole](#extending-multiagentconsole)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)
10. [Contributing](#contributing)

## Introduction

MultiAgentConsole is a powerful platform for interacting with AI agents, managing workflows, and extending functionality through plugins. It provides a web interface, desktop application, and various tools for working with AI models.

### Key Features

- **Multi-Agent Support**: Interact with multiple AI agents simultaneously
- **Workflow Management**: Create, save, and execute complex workflows
- **Plugin System**: Extend functionality with custom plugins
- **Agent Marketplace**: Discover and install new agents
- **Offline Capabilities**: Work without an internet connection
- **Multi-Modal Support**: Process text, images, audio, and more
- **Advanced Debugging**: Monitor and debug your interactions
- **Cross-Platform**: Run on web, desktop, and mobile devices

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher (for desktop application)
- Modern web browser

### Web Application

```bash
# Clone the repository
git clone https://github.com/ssvgopal/multi_agent_console.git
cd multi_agent_console

# Install dependencies
pip install -r requirements.txt

# Run the web server
python -m multi_agent_console --web --port 8007
```

### Desktop Application

```bash
# Navigate to the desktop directory
cd desktop

# Install dependencies
npm install

# Run the desktop application
npm start

# Build the desktop application
npm run build
```

## Getting Started

### First Steps

1. **Register an Account**: Create a new account or log in if you already have one
2. **Configure AI Providers**: Set up your API keys for different AI providers
3. **Explore the Interface**: Familiarize yourself with the tabs and features
4. **Try a Simple Chat**: Start a conversation with an AI agent
5. **Create a Workflow**: Build a simple workflow to automate tasks

### Basic Usage

The main interface consists of several tabs:

- **Chat**: Interact with AI agents through text
- **Workflows**: Create and manage automated workflows
- **Tools**: Access various tools for specific tasks
- **Multimodal**: Work with images, audio, and other media
- **Marketplace**: Discover and install new agents
- **Plugins**: Manage and configure plugins
- **Offline**: Access offline capabilities and knowledge base
- **Settings**: Configure application settings

## Features

Detailed documentation for each feature is available in the following sections:

- [Chat System](features/chat.md)
- [Workflow Management](features/workflows.md)
- [Tools](features/tools.md)
- [Multi-Modal Support](features/multimodal.md)
- [Agent Marketplace](features/marketplace.md)
- [Plugin System](features/plugins.md)
- [Offline Capabilities](features/offline.md)
- [Debugging and Monitoring](features/debugging.md)
- [Desktop Application](features/desktop.md)

## Configuration

MultiAgentConsole can be configured through command-line arguments, configuration files, or the settings interface.

### Command-Line Arguments

```bash
python -m multi_agent_console --help
```

Common arguments:

- `--web`: Start the web interface
- `--port PORT`: Specify the port for the web interface (default: 8000)
- `--host HOST`: Specify the host for the web interface (default: 0.0.0.0)
- `--offline`: Start in offline mode
- `--debug`: Enable debug mode
- `--config CONFIG`: Specify a configuration file

### Configuration File

Create a `config.json` file in the root directory:

```json
{
  "web": {
    "port": 8007,
    "host": "0.0.0.0",
    "debug": false
  },
  "agents": {
    "default_model": "gpt-4"
  },
  "plugins": {
    "enabled": ["hello_world"]
  }
}
```

## API Reference

MultiAgentConsole provides a RESTful API for interacting with the system programmatically.

- [Authentication API](api/authentication.md)
- [Chat API](api/chat.md)
- [Workflow API](api/workflows.md)
- [Tools API](api/tools.md)
- [Multimodal API](api/multimodal.md)
- [Marketplace API](api/marketplace.md)
- [Plugin API](api/plugins.md)
- [Offline API](api/offline.md)

## Extending MultiAgentConsole

MultiAgentConsole can be extended in several ways:

- [Creating Plugins](extending/plugins.md)
- [Developing Agents](extending/agents.md)
- [Adding Tools](extending/tools.md)
- [Custom Workflows](extending/workflows.md)

## Troubleshooting

Common issues and their solutions:

- [Installation Issues](troubleshooting/installation.md)
- [Connection Problems](troubleshooting/connection.md)
- [Plugin Errors](troubleshooting/plugins.md)
- [Performance Issues](troubleshooting/performance.md)

## FAQ

Frequently asked questions about MultiAgentConsole:

- [General Questions](faq/general.md)
- [Feature Questions](faq/features.md)
- [Technical Questions](faq/technical.md)

## Contributing

We welcome contributions to MultiAgentConsole! Please see our [Contributing Guide](CONTRIBUTING.md) for more information.

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Development Setup](DEVELOPMENT.md)
- [Pull Request Process](PULL_REQUEST_TEMPLATE.md)
