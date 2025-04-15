/**
 * WebSocket Test Client for MultiAgentConsole
 * This file provides utilities for testing WebSocket connections
 */

// WebSocket connection
let testSocket = null;
let messageLog = [];
let isConnected = false;

// DOM Elements
const wsTestPanel = document.getElementById('ws-test-panel');
const connectBtn = document.getElementById('ws-connect-btn');
const disconnectBtn = document.getElementById('ws-disconnect-btn');
const statusIndicator = document.getElementById('ws-status');
const messageInput = document.getElementById('ws-message-input');
const sendBtn = document.getElementById('ws-send-btn');
const messageLogContainer = document.getElementById('ws-message-log');
const clearLogBtn = document.getElementById('ws-clear-log');
const messageTypeSelect = document.getElementById('ws-message-type');

// Initialize WebSocket test client
function initWebSocketTest() {
    setupWebSocketTestEventListeners();
    updateConnectionStatus(false);
    console.log('WebSocket Test Client initialized');
}

// Set up event listeners for WebSocket test client
function setupWebSocketTestEventListeners() {
    if (connectBtn) {
        connectBtn.addEventListener('click', connectWebSocketTest);
    }
    
    if (disconnectBtn) {
        disconnectBtn.addEventListener('click', disconnectWebSocketTest);
    }
    
    if (sendBtn) {
        sendBtn.addEventListener('click', sendTestMessage);
    }
    
    if (clearLogBtn) {
        clearLogBtn.addEventListener('click', clearMessageLog);
    }
}

// Connect to WebSocket
function connectWebSocketTest() {
    if (isConnected) {
        logMessage('Already connected', 'system');
        return;
    }
    
    try {
        // Get the current host and protocol
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/ws`;
        
        logMessage(`Connecting to ${wsUrl}...`, 'system');
        
        // Create WebSocket connection
        testSocket = new WebSocket(wsUrl);
        
        // Connection opened
        testSocket.addEventListener('open', (event) => {
            isConnected = true;
            updateConnectionStatus(true);
            logMessage('Connection established', 'success');
        });
        
        // Listen for messages
        testSocket.addEventListener('message', (event) => {
            try {
                const data = JSON.parse(event.data);
                logMessage(`Received: ${JSON.stringify(data, null, 2)}`, 'received');
            } catch (e) {
                logMessage(`Received (raw): ${event.data}`, 'received');
            }
        });
        
        // Connection closed
        testSocket.addEventListener('close', (event) => {
            isConnected = false;
            updateConnectionStatus(false);
            logMessage(`Connection closed. Code: ${event.code}, Reason: ${event.reason}`, 'system');
        });
        
        // Connection error
        testSocket.addEventListener('error', (event) => {
            isConnected = false;
            updateConnectionStatus(false);
            logMessage('Connection error', 'error');
        });
    } catch (error) {
        logMessage(`Error: ${error.message}`, 'error');
    }
}

// Disconnect from WebSocket
function disconnectWebSocketTest() {
    if (!isConnected || !testSocket) {
        logMessage('Not connected', 'system');
        return;
    }
    
    try {
        testSocket.close();
        logMessage('Disconnected', 'system');
    } catch (error) {
        logMessage(`Error: ${error.message}`, 'error');
    }
}

// Send a test message
function sendTestMessage() {
    if (!isConnected || !testSocket) {
        logMessage('Not connected', 'error');
        return;
    }
    
    const messageType = messageTypeSelect.value;
    const messageContent = messageInput.value.trim();
    
    if (!messageContent) {
        logMessage('Please enter a message', 'error');
        return;
    }
    
    try {
        let message = {};
        
        switch (messageType) {
            case 'chat':
                message = {
                    type: 'chat_message',
                    content: messageContent
                };
                break;
                
            case 'graph':
                message = {
                    type: 'graph_request',
                    query: messageContent
                };
                break;
                
            case 'tool':
                try {
                    // Try to parse as JSON
                    const toolData = JSON.parse(messageContent);
                    message = {
                        type: 'tool_request',
                        ...toolData
                    };
                } catch (e) {
                    // If not valid JSON, use as tool_id
                    message = {
                        type: 'tool_request',
                        tool_id: messageContent,
                        parameters: {}
                    };
                }
                break;
                
            case 'custom':
                try {
                    message = JSON.parse(messageContent);
                } catch (e) {
                    logMessage('Invalid JSON for custom message', 'error');
                    return;
                }
                break;
                
            default:
                message = {
                    type: messageType,
                    content: messageContent
                };
        }
        
        testSocket.send(JSON.stringify(message));
        logMessage(`Sent: ${JSON.stringify(message, null, 2)}`, 'sent');
        
        // Clear input
        messageInput.value = '';
    } catch (error) {
        logMessage(`Error: ${error.message}`, 'error');
    }
}

// Log a message
function logMessage(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = {
        timestamp,
        message,
        type
    };
    
    messageLog.push(logEntry);
    updateMessageLog();
}

// Update the message log display
function updateMessageLog() {
    if (!messageLogContainer) return;
    
    let html = '';
    
    messageLog.forEach(entry => {
        let className = 'text-gray-700';
        
        switch (entry.type) {
            case 'success':
                className = 'text-green-600';
                break;
            case 'error':
                className = 'text-red-600';
                break;
            case 'sent':
                className = 'text-blue-600';
                break;
            case 'received':
                className = 'text-purple-600';
                break;
            case 'system':
                className = 'text-gray-500 italic';
                break;
        }
        
        html += `
            <div class="mb-2">
                <span class="text-xs text-gray-500">${entry.timestamp}</span>
                <pre class="${className} text-sm whitespace-pre-wrap">${entry.message}</pre>
            </div>
        `;
    });
    
    messageLogContainer.innerHTML = html;
    
    // Scroll to bottom
    messageLogContainer.scrollTop = messageLogContainer.scrollHeight;
}

// Clear the message log
function clearMessageLog() {
    messageLog = [];
    updateMessageLog();
    logMessage('Log cleared', 'system');
}

// Update connection status display
function updateConnectionStatus(connected) {
    if (statusIndicator) {
        if (connected) {
            statusIndicator.textContent = 'Connected';
            statusIndicator.className = 'text-green-600 font-medium';
        } else {
            statusIndicator.textContent = 'Disconnected';
            statusIndicator.className = 'text-red-600 font-medium';
        }
    }
    
    if (connectBtn) {
        connectBtn.disabled = connected;
    }
    
    if (disconnectBtn) {
        disconnectBtn.disabled = !connected;
    }
    
    if (sendBtn) {
        sendBtn.disabled = !connected;
    }
    
    if (messageInput) {
        messageInput.disabled = !connected;
    }
    
    if (messageTypeSelect) {
        messageTypeSelect.disabled = !connected;
    }
}

// Export functions for use in other modules
window.initWebSocketTest = initWebSocketTest;
