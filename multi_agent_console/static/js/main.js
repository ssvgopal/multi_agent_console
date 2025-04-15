/**
 * Main JavaScript for MultiAgentConsole Web UI
 */

// DOM Elements
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const chatMessages = document.getElementById('chat-messages');
const agentSelector = document.getElementById('agent-selector');
const newChatButton = document.getElementById('new-chat-button');
const saveChatButton = document.getElementById('save-chat-button');
const settingsButton = document.getElementById('settings-button');
const settingsModal = document.getElementById('settings-modal');
const closeSettingsButton = document.getElementById('close-settings');
const saveSettingsButton = document.getElementById('save-settings');
const apiKeyInput = document.getElementById('api-key-input');
const modelSelector = document.getElementById('model-selector');
const themeSelector = document.getElementById('theme-selector');

// Tab Navigation Elements
const tabNavigation = document.getElementById('tab-navigation');
const tabPanes = document.querySelectorAll('.tab-pane');

// State
let currentSessionId = null;
let webSocket = null;
let selectedAgent = 'coordinator';
let isConnected = false;
let messageHistory = [];

// Initialize the application
function init() {
    // Load settings from localStorage
    loadSettings();

    // Connect to WebSocket
    connectWebSocket();

    // Load available agents
    loadAgents();

    // Set up event listeners
    setupEventListeners();

    // Initialize graph visualization
    if (typeof initGraph === 'function') {
        initGraph();
    }

    // Initialize tools
    if (typeof initTools === 'function') {
        initTools();
    }

    // Initialize multi-modal functionality
    if (typeof initMultiModal === 'function') {
        initMultiModal();
    }

    // Initialize workflow functionality
    if (typeof initWorkflow === 'function') {
        initWorkflow();
    }

    // Initialize offline functionality
    if (typeof initOffline === 'function') {
        initOffline();
    }

    // Initialize marketplace functionality
    if (typeof initMarketplace === 'function') {
        initMarketplace();
    }

    // Initialize plugins functionality
    if (typeof initPlugins === 'function') {
        initPlugins();
    }

    // Initialize WebSocket test client
    if (typeof initWebSocketTest === 'function') {
        initWebSocketTest();
    }

    console.log('MultiAgentConsole Web UI initialized');
}

// Connect to WebSocket
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    webSocket = new WebSocket(wsUrl);

    webSocket.onopen = () => {
        console.log('WebSocket connected');
        isConnected = true;
    };

    webSocket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };

    webSocket.onclose = () => {
        console.log('WebSocket disconnected');
        isConnected = false;
        // Try to reconnect after a delay
        setTimeout(connectWebSocket, 3000);
    };

    webSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        isConnected = false;
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(message) {
    switch (message.type) {
        case 'chat_response':
            addAssistantMessage(message.content);
            break;
        case 'graph_data':
            updateGraph(message.data);
            updateInsights(message.data);
            break;
        case 'tool_response':
            handleToolResponse(message.tool_id, message.result);
            break;
        case 'tool_error':
            handleToolError(message.tool_id, message.error);
            break;
        case 'thinking':
            showThinkingIndicator(message.content);
            break;
        case 'multi_modal_response':
            handleMultiModalResponse(message.data);
            break;
        default:
            console.log('Unknown message type:', message.type);
    }
}

// Handle tool response
function handleToolResponse(toolId, result) {
    // Find the tool result container
    const resultContainer = document.getElementById(`result-${toolId}`);
    if (resultContainer) {
        const resultPre = resultContainer.querySelector('pre');
        resultContainer.classList.remove('hidden');
        resultPre.textContent = JSON.stringify(result, null, 2);
        resultPre.classList.remove('text-red-600');
    }

    // Also add to chat as a system message
    const resultStr = typeof result === 'object' ? JSON.stringify(result, null, 2) : result;
    addSystemMessage(`Tool result for ${toolId}:\n${resultStr}`);
}

// Handle tool error
function handleToolError(toolId, error) {
    // Find the tool result container
    const resultContainer = document.getElementById(`result-${toolId}`);
    if (resultContainer) {
        const resultPre = resultContainer.querySelector('pre');
        resultContainer.classList.remove('hidden');
        resultPre.textContent = `Error: ${error}`;
        resultPre.classList.add('text-red-600');
    }

    // Also add to chat as a system message
    addSystemMessage(`Tool error for ${toolId}: ${error}`, 'error');
}

// Handle multi-modal response
function handleMultiModalResponse(data) {
    if (data.type === 'image') {
        // Display image in chat
        addImageMessage(data.url, data.caption);
    } else if (data.type === 'audio') {
        // Display audio player in chat
        addAudioMessage(data.url, data.caption);
    } else if (data.type === 'chart') {
        // Display chart in chat
        addChartMessage(data.chart_data, data.chart_type, data.caption);
    }
}

// Load available agents
async function loadAgents() {
    try {
        const response = await fetch('/api/agents');
        const data = await response.json();

        if (data.agents && data.agents.length > 0) {
            // Clear existing options except the first one (coordinator)
            while (agentSelector.options.length > 1) {
                agentSelector.remove(1);
            }

            // Add new options
            data.agents.forEach(agent => {
                if (agent !== 'coordinator') {  // Skip coordinator as it's already there
                    const option = document.createElement('option');
                    option.value = agent;
                    option.textContent = agent.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
                    agentSelector.appendChild(option);
                }
            });
        }
    } catch (error) {
        console.error('Error loading agents:', error);
    }
}

// Set up event listeners
function setupEventListeners() {
    // Send message on button click
    sendButton.addEventListener('click', sendMessage);

    // Send message on Enter key
    chatInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });

    // Change agent
    agentSelector.addEventListener('change', () => {
        selectedAgent = agentSelector.value;
    });

    // New chat
    newChatButton.addEventListener('click', startNewChat);

    // Save chat
    saveChatButton.addEventListener('click', saveChat);

    // Settings modal
    settingsButton.addEventListener('click', () => {
        settingsModal.classList.remove('hidden');
    });

    closeSettingsButton.addEventListener('click', () => {
        settingsModal.classList.add('hidden');
    });

    // Tab navigation
    tabNavigation.querySelectorAll('a').forEach(tab => {
        tab.addEventListener('click', (event) => {
            event.preventDefault();

            // Remove active class from all tabs
            tabNavigation.querySelectorAll('a').forEach(t => {
                t.classList.remove('active', 'border-blue-600');
                t.classList.add('border-transparent');
            });

            // Add active class to clicked tab
            tab.classList.add('active', 'border-blue-600');
            tab.classList.remove('border-transparent');

            // Hide all tab panes
            tabPanes.forEach(pane => {
                pane.classList.add('hidden');
                pane.classList.remove('active');
            });

            // Show the corresponding tab pane
            const tabId = tab.getAttribute('data-tab');
            const tabPane = document.getElementById(tabId);
            if (tabPane) {
                tabPane.classList.remove('hidden');
                tabPane.classList.add('active');
            }
        });
    });

    saveSettingsButton.addEventListener('click', saveSettings);

    // Close modal when clicking outside
    settingsModal.addEventListener('click', (event) => {
        if (event.target === settingsModal) {
            settingsModal.classList.add('hidden');
        }
    });
}

// Send a message
function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message to the chat
    addUserMessage(message);

    // Add thinking indicator
    const thinkingId = addThinkingIndicator();

    // Send message via WebSocket if connected
    if (isConnected) {
        webSocket.send(JSON.stringify({
            type: 'chat',
            content: message,
            agent: selectedAgent,
            session_id: currentSessionId
        }));
    } else {
        // Fallback to REST API
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove thinking indicator
            removeThinkingIndicator(thinkingId);

            // Add assistant message
            addAssistantMessage(data.response);
        })
        .catch(error => {
            console.error('Error sending message:', error);
            // Remove thinking indicator
            removeThinkingIndicator(thinkingId);

            // Add error message
            addAssistantMessage('Error: Could not get a response. Please try again.');
        });
    }

    // Clear input
    chatInput.value = '';
    chatInput.focus();
}

// Add a user message to the chat
function addUserMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message user-message';
    messageElement.innerHTML = `<p>${escapeHtml(message)}</p>`;
    chatMessages.appendChild(messageElement);

    // Save to history
    messageHistory.push({
        role: 'user',
        content: message
    });

    // Scroll to bottom
    scrollToBottom();
}

// Add an assistant message to the chat
function addAssistantMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message assistant-message';

    // Convert markdown-like syntax to HTML
    const formattedMessage = formatMessage(message);
    messageElement.innerHTML = `<p>${formattedMessage}</p>`;

    chatMessages.appendChild(messageElement);

    // Save to history
    messageHistory.push({
        role: 'assistant',
        content: message
    });

    // Scroll to bottom
    scrollToBottom();
}

// Add a system message to the chat
function addSystemMessage(message, type = 'info') {
    const messageElement = document.createElement('div');
    messageElement.className = `message system-message ${type}`;

    // Style based on type
    let bgColor = 'bg-gray-100';
    if (type === 'error') bgColor = 'bg-red-100';
    else if (type === 'success') bgColor = 'bg-green-100';
    else if (type === 'warning') bgColor = 'bg-yellow-100';

    // Convert markdown-like syntax to HTML
    const formattedMessage = formatMessage(message);
    messageElement.innerHTML = `<div class="${bgColor} p-2 rounded text-sm">${formattedMessage}</div>`;

    chatMessages.appendChild(messageElement);

    // Save to history
    messageHistory.push({
        role: 'system',
        content: message
    });

    // Scroll to bottom
    scrollToBottom();
}

// Add an image message to the chat
function addImageMessage(imageUrl, caption = '') {
    const messageElement = document.createElement('div');
    messageElement.className = 'message assistant-message';

    let html = `<div class="mb-2"><img src="${imageUrl}" alt="${caption}" class="max-w-full rounded"></div>`;
    if (caption) {
        html += `<p class="text-sm text-gray-600 italic">${caption}</p>`;
    }

    messageElement.innerHTML = html;
    chatMessages.appendChild(messageElement);

    // Save to history
    messageHistory.push({
        role: 'assistant',
        content: caption || 'Image',
        image_url: imageUrl
    });

    // Scroll to bottom
    scrollToBottom();
}

// Add an audio message to the chat
function addAudioMessage(audioUrl, caption = '') {
    const messageElement = document.createElement('div');
    messageElement.className = 'message assistant-message';

    let html = `<div class="mb-2"><audio controls src="${audioUrl}" class="w-full"></audio></div>`;
    if (caption) {
        html += `<p class="text-sm text-gray-600 italic">${caption}</p>`;
    }

    messageElement.innerHTML = html;
    chatMessages.appendChild(messageElement);

    // Save to history
    messageHistory.push({
        role: 'assistant',
        content: caption || 'Audio',
        audio_url: audioUrl
    });

    // Scroll to bottom
    scrollToBottom();
}

// Add a chart message to the chat
function addChartMessage(chartData, chartType, caption = '') {
    const messageElement = document.createElement('div');
    messageElement.className = 'message assistant-message';

    // Create a canvas for the chart
    const canvasId = 'chart-' + Date.now();
    let html = `<div class="mb-2"><canvas id="${canvasId}" width="400" height="200"></canvas></div>`;
    if (caption) {
        html += `<p class="text-sm text-gray-600 italic">${caption}</p>`;
    }

    messageElement.innerHTML = html;
    chatMessages.appendChild(messageElement);

    // Create the chart
    const ctx = document.getElementById(canvasId).getContext('2d');
    new Chart(ctx, {
        type: chartType,
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    // Save to history
    messageHistory.push({
        role: 'assistant',
        content: caption || 'Chart',
        chart_data: chartData,
        chart_type: chartType
    });

    // Scroll to bottom
    scrollToBottom();
}

// Add a thinking indicator
function addThinkingIndicator() {
    const id = 'thinking-' + Date.now();
    const messageElement = document.createElement('div');
    messageElement.className = 'message assistant-message thinking';
    messageElement.id = id;
    messageElement.innerHTML = '<p>Thinking...</p>';
    chatMessages.appendChild(messageElement);

    // Scroll to bottom
    scrollToBottom();

    return id;
}

// Show thinking indicator with custom message
function showThinkingIndicator(message) {
    // Check if there's already a thinking indicator
    const existingIndicator = document.querySelector('.thinking');
    if (existingIndicator) {
        existingIndicator.innerHTML = `<p>${message || 'Thinking...'}</p>`;
        return existingIndicator.id;
    } else {
        const id = 'thinking-' + Date.now();
        const messageElement = document.createElement('div');
        messageElement.className = 'message assistant-message thinking';
        messageElement.id = id;
        messageElement.innerHTML = `<p>${message || 'Thinking...'}</p>`;
        chatMessages.appendChild(messageElement);

        // Scroll to bottom
        scrollToBottom();

        return id;
    }
}

// Remove a thinking indicator
function removeThinkingIndicator(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

// Format message (simple markdown-like syntax)
function formatMessage(message) {
    // Replace code blocks
    message = message.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

    // Replace inline code
    message = message.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Replace bold text
    message = message.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Replace italic text
    message = message.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Replace newlines with <br>
    message = message.replace(/\n/g, '<br>');

    return message;
}

// Escape HTML to prevent XSS
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Scroll chat to bottom
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Start a new chat
function startNewChat() {
    // Clear chat messages except the welcome message
    while (chatMessages.children.length > 1) {
        chatMessages.removeChild(chatMessages.lastChild);
    }

    // Reset message history
    messageHistory = [];

    // Generate a new session ID
    currentSessionId = generateSessionId();

    // Focus on input
    chatInput.focus();
}

// Save the current chat
function saveChat() {
    if (messageHistory.length === 0) {
        alert('No messages to save');
        return;
    }

    const chatData = {
        id: currentSessionId || generateSessionId(),
        timestamp: new Date().toISOString(),
        messages: messageHistory
    };

    // Save to localStorage
    const savedChats = JSON.parse(localStorage.getItem('savedChats') || '[]');
    savedChats.push(chatData);
    localStorage.setItem('savedChats', JSON.stringify(savedChats));

    alert('Chat saved successfully');
}

// Load settings from localStorage
function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('settings') || '{}');

    if (settings.apiKey) {
        apiKeyInput.value = settings.apiKey;
    }

    if (settings.model) {
        modelSelector.value = settings.model;
    }

    if (settings.theme) {
        themeSelector.value = settings.theme;
        applyTheme(settings.theme);
    }
}

// Save settings to localStorage
function saveSettings() {
    const settings = {
        apiKey: apiKeyInput.value,
        model: modelSelector.value,
        theme: themeSelector.value
    };

    localStorage.setItem('settings', JSON.stringify(settings));

    // Apply theme
    applyTheme(settings.theme);

    // Close modal
    settingsModal.classList.add('hidden');

    // Send settings to server
    if (isConnected) {
        webSocket.send(JSON.stringify({
            type: 'settings',
            settings: {
                api_key: settings.apiKey,
                model: settings.model
            }
        }));
    }

    alert('Settings saved successfully');
}

// Apply theme
function applyTheme(theme) {
    // This is a placeholder - in a real implementation, you would
    // add/remove CSS classes or change CSS variables
    if (theme === 'dark') {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
}

// Generate a session ID
function generateSessionId() {
    return 'session-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
