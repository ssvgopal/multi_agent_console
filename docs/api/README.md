# MultiAgentConsole API Reference

The MultiAgentConsole provides a comprehensive RESTful API that allows you to interact with the system programmatically. This document provides an overview of the available endpoints, authentication methods, and usage examples.

## Table of Contents

1. [Authentication](#authentication)
2. [API Endpoints](#api-endpoints)
3. [Error Handling](#error-handling)
4. [Rate Limiting](#rate-limiting)
5. [Versioning](#versioning)
6. [Examples](#examples)

## Authentication

The API supports several authentication methods:

### API Key Authentication

Most API endpoints require an API key for authentication. You can obtain an API key from the Settings page in the MultiAgentConsole web interface.

Include your API key in the request header:

```
Authorization: Bearer YOUR_API_KEY
```

### Session Cookie Authentication

For web applications, you can use session cookies for authentication. First, authenticate using the login endpoint, then include the session cookie in subsequent requests.

### Basic Authentication

Some endpoints support HTTP Basic Authentication:

```
Authorization: Basic base64(username:password)
```

## API Endpoints

The API is organized into the following categories:

### Authentication API

- `POST /api/auth/login`: Authenticate a user and get a session token
- `POST /api/auth/logout`: Invalidate the current session token
- `POST /api/auth/register`: Register a new user
- `GET /api/auth/user`: Get information about the current user
- `POST /api/auth/reset-password`: Request a password reset
- `POST /api/auth/change-password`: Change the user's password

### Chat API

- `POST /api/chat/message`: Send a message to an AI agent
- `GET /api/chat/history`: Get conversation history
- `POST /api/chat/clear`: Clear the current conversation
- `GET /api/chat/models`: Get available AI models
- `POST /api/chat/system-prompt`: Set the system prompt

### Workflow API

- `GET /api/workflows`: List available workflows
- `GET /api/workflows/{id}`: Get workflow details
- `POST /api/workflows`: Create a new workflow
- `PUT /api/workflows/{id}`: Update a workflow
- `DELETE /api/workflows/{id}`: Delete a workflow
- `POST /api/workflows/execute/{id}`: Execute a workflow
- `GET /api/workflows/executions/{id}`: Get workflow execution status
- `GET /api/workflows/templates`: List available workflow templates

### Tools API

- `GET /api/tools`: List available tools
- `POST /api/tools/{tool_name}`: Execute a tool
- `GET /api/tools/{tool_name}/schema`: Get tool parameter schema

### Multimodal API

- `POST /api/multimodal/image`: Process an image
- `POST /api/multimodal/audio`: Process audio
- `POST /api/multimodal/text-to-speech`: Convert text to speech
- `POST /api/multimodal/speech-to-text`: Convert speech to text
- `POST /api/multimodal/ocr`: Extract text from an image

### Marketplace API

- `GET /api/marketplace/available`: List available agents
- `GET /api/marketplace/installed`: List installed agents
- `GET /api/marketplace/agent/{agent_id}`: Get agent details
- `POST /api/marketplace/install/{agent_id}`: Install an agent
- `POST /api/marketplace/uninstall/{agent_id}`: Uninstall an agent
- `POST /api/marketplace/rate/{agent_id}`: Rate an agent
- `GET /api/marketplace/search`: Search for agents

### Plugin API

- `GET /api/plugins`: List installed plugins
- `GET /api/plugins/{plugin_id}`: Get plugin details
- `POST /api/plugins/{plugin_id}/enable`: Enable a plugin
- `POST /api/plugins/{plugin_id}/disable`: Disable a plugin
- `POST /api/plugins/{plugin_id}/reload`: Reload a plugin
- `POST /api/plugins/{plugin_id}/event`: Send an event to a plugin
- `GET /api/plugins/registry`: List available plugins from the registry
- `POST /api/plugins/registry/install/{plugin_id}`: Install a plugin from the registry
- `GET /api/plugins/registry/search`: Search for plugins in the registry

### Offline API

- `GET /api/offline/status`: Get offline mode status
- `POST /api/offline/toggle`: Toggle offline mode
- `GET /api/offline/cache/stats`: Get cache statistics
- `POST /api/offline/cache/clear`: Clear the cache
- `GET /api/offline/knowledge`: List knowledge base entries
- `POST /api/offline/knowledge`: Add to the knowledge base
- `DELETE /api/offline/knowledge/{id}`: Remove from the knowledge base

### System API

- `GET /api/status`: Get system status
- `GET /api/version`: Get system version
- `GET /api/stats`: Get system statistics
- `POST /api/logs`: Get system logs

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request:

- `200 OK`: The request was successful
- `201 Created`: The resource was successfully created
- `400 Bad Request`: The request was invalid
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: The authenticated user doesn't have permission
- `404 Not Found`: The requested resource was not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: An error occurred on the server

Error responses include a JSON body with details:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Missing required parameter: message",
    "details": {
      "parameter": "message"
    }
  }
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Rate limits are applied per API key or IP address.

Rate limit headers are included in all API responses:

- `X-RateLimit-Limit`: The maximum number of requests allowed in the current period
- `X-RateLimit-Remaining`: The number of requests remaining in the current period
- `X-RateLimit-Reset`: The time at which the current rate limit window resets (Unix timestamp)

If you exceed the rate limit, you'll receive a `429 Too Many Requests` response.

## Versioning

The API uses versioning to ensure compatibility as it evolves. The current version is v1.

You can specify the API version in the URL:

```
https://your-instance.com/api/v1/chat/message
```

Or in the request header:

```
Accept: application/json; version=1
```

## Examples

### Python Example

```python
import requests

# Configuration
API_URL = "http://localhost:8007/api"
API_KEY = "your_api_key"

# Headers
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Send a message to an AI agent
def send_message(message, model="gpt-4"):
    response = requests.post(
        f"{API_URL}/chat/message",
        headers=headers,
        json={
            "message": message,
            "model": model
        }
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        return None

# Execute a workflow
def execute_workflow(workflow_id, inputs=None):
    response = requests.post(
        f"{API_URL}/workflows/execute/{workflow_id}",
        headers=headers,
        json=inputs or {}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        return None

# Example usage
message_response = send_message("What is the capital of France?")
print(message_response)

workflow_response = execute_workflow("data_analysis", {
    "data_url": "https://example.com/data.csv",
    "analysis_type": "summary"
})
print(workflow_response)
```

### JavaScript Example

```javascript
// Configuration
const API_URL = "http://localhost:8007/api";
const API_KEY = "your_api_key";

// Headers
const headers = {
    "Authorization": `Bearer ${API_KEY}`,
    "Content-Type": "application/json"
};

// Send a message to an AI agent
async function sendMessage(message, model = "gpt-4") {
    try {
        const response = await fetch(`${API_URL}/chat/message`, {
            method: "POST",
            headers: headers,
            body: JSON.stringify({
                message: message,
                model: model
            })
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            console.error(`Error: ${response.status}`);
            console.error(await response.json());
            return null;
        }
    } catch (error) {
        console.error("Request failed:", error);
        return null;
    }
}

// Execute a workflow
async function executeWorkflow(workflowId, inputs = {}) {
    try {
        const response = await fetch(`${API_URL}/workflows/execute/${workflowId}`, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(inputs)
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            console.error(`Error: ${response.status}`);
            console.error(await response.json());
            return null;
        }
    } catch (error) {
        console.error("Request failed:", error);
        return null;
    }
}

// Example usage
sendMessage("What is the capital of France?")
    .then(response => console.log(response));

executeWorkflow("data_analysis", {
    data_url: "https://example.com/data.csv",
    analysis_type: "summary"
})
    .then(response => console.log(response));
```

### cURL Example

```bash
# Send a message to an AI agent
curl -X POST "http://localhost:8007/api/chat/message" \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the capital of France?",
    "model": "gpt-4"
  }'

# Execute a workflow
curl -X POST "http://localhost:8007/api/workflows/execute/data_analysis" \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "data_url": "https://example.com/data.csv",
    "analysis_type": "summary"
  }'
```

For more detailed information about specific endpoints, please refer to the individual API documentation pages:

- [Authentication API](authentication.md)
- [Chat API](chat.md)
- [Workflow API](workflows.md)
- [Tools API](tools.md)
- [Multimodal API](multimodal.md)
- [Marketplace API](marketplace.md)
- [Plugin API](plugins.md)
- [Offline API](offline.md)
