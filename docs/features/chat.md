# Chat System

The chat system in MultiAgentConsole provides a powerful interface for interacting with AI agents through text-based conversations.

## Overview

The chat interface allows you to:

- Communicate with AI agents using natural language
- Switch between different AI models
- Save and load conversation history
- Use system prompts to guide agent behavior
- Integrate with tools and workflows
- Process multi-modal inputs and outputs

## Getting Started

### Accessing the Chat Interface

The chat interface is the default tab when you open MultiAgentConsole. You can also access it by clicking the "Chat" tab in the navigation bar.

### Starting a Conversation

1. Type your message in the input box at the bottom of the screen
2. Press Enter or click the Send button to send your message
3. The AI agent will respond in the chat window

### Selecting an AI Model

You can select different AI models using the dropdown menu in the top-right corner of the chat interface. Available models depend on your configuration and API keys.

## Features

### Message History

All messages in the conversation are saved and displayed in the chat window. You can:

- Scroll through the conversation history
- Copy messages to the clipboard
- Edit your previous messages
- Delete messages

### System Prompts

System prompts allow you to set the context and behavior of the AI agent. To use a system prompt:

1. Click the "System Prompt" button above the chat window
2. Enter your system prompt in the text area
3. Click "Save" to apply the prompt

Example system prompts:

```
You are a helpful assistant that specializes in programming.
```

```
You are a creative writing assistant. Help the user brainstorm ideas and provide feedback on their writing.
```

### File Attachments

You can attach files to your messages to provide additional context or data:

1. Click the paperclip icon in the input box
2. Select a file from your computer
3. The file will be processed and included in your message

Supported file types:

- Text files (.txt, .md, .csv, etc.)
- Images (.jpg, .png, .gif, etc.)
- Audio files (.mp3, .wav, etc.)
- Code files (.py, .js, .html, etc.)

### Code Blocks

The chat interface supports code blocks with syntax highlighting:

```python
def hello_world():
    print("Hello, world!")
```

To create a code block:

1. Type three backticks (```) followed by the language name
2. Enter your code
3. End with three backticks

### Multi-Modal Inputs

The chat system supports various types of inputs:

- **Text**: Regular text messages
- **Images**: Upload or paste images for analysis
- **Audio**: Record or upload audio for transcription
- **Video**: Upload video for processing

To use multi-modal inputs:

1. Click the appropriate icon in the input box (microphone for audio, camera for images, etc.)
2. Record or select the file
3. The content will be processed and included in your message

### Tool Integration

You can use tools directly from the chat interface:

1. Type "/" to see a list of available tools
2. Select a tool from the list
3. Provide the required parameters
4. The tool will execute and display the results in the chat

Example tool commands:

```
/search How does photosynthesis work?
```

```
/calculate 15 * 24 + 7
```

### Workflow Integration

You can trigger workflows from the chat:

1. Type "/workflow" followed by the workflow name
2. The workflow will execute and display the results in the chat

Example:

```
/workflow analyze_sentiment
```

## Advanced Features

### Chat Settings

You can customize the chat experience through the settings panel:

1. Click the gear icon in the top-right corner of the chat interface
2. Adjust settings such as:
   - Message display format
   - Code block styling
   - Auto-scroll behavior
   - Message timestamps

### Conversation Management

MultiAgentConsole provides tools for managing conversations:

- **Save Conversation**: Save the current conversation to your account
- **Load Conversation**: Load a previously saved conversation
- **Export Conversation**: Export the conversation as a text or HTML file
- **Clear Conversation**: Clear the current conversation history

### Offline Mode

The chat system can operate in offline mode using cached responses:

1. Enable offline mode in the settings
2. The system will use cached responses when possible
3. If a response is not available in the cache, you'll be notified

## API Integration

You can interact with the chat system programmatically using the Chat API:

```python
import requests

# Send a message
response = requests.post(
    "http://localhost:8007/api/chat/message",
    json={
        "message": "Hello, how are you?",
        "model": "gpt-4"
    },
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)

# Get the response
print(response.json())
```

See the [Chat API documentation](../api/chat.md) for more details.

## Troubleshooting

### Common Issues

- **Slow Responses**: This may be due to high server load or complex queries. Try using a different model or simplifying your request.
- **Error Messages**: If you receive an error message, check your API keys and internet connection.
- **Missing Features**: Some features may require specific plugins or configurations. Check your settings and installed plugins.

### Getting Help

If you encounter issues with the chat system:

1. Check the [FAQ](../faq/features.md) for common questions
2. Visit the [Troubleshooting](../troubleshooting/connection.md) section
3. Contact support or open an issue on GitHub
