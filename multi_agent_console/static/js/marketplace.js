/**
 * Agent Marketplace functionality for MultiAgentConsole Web UI
 */

// DOM Elements
const marketplacePanel = document.getElementById('marketplace-panel');
const availableAgentsList = document.getElementById('available-agents-list');
const installedAgentsList = document.getElementById('installed-agents-list');
const agentDetailsContainer = document.getElementById('agent-details');
const searchInput = document.getElementById('agent-search-input');
const searchBtn = document.getElementById('agent-search-btn');

// Initialize marketplace functionality
function initMarketplace() {
    // Set up event listeners
    setupMarketplaceEventListeners();
    
    // Load initial content
    loadInstalledAgents();
    loadAvailableAgents();
    
    console.log('Marketplace functionality initialized');
}

// Set up event listeners for marketplace functionality
function setupMarketplaceEventListeners() {
    // Search button
    if (searchBtn) {
        searchBtn.addEventListener('click', searchAgents);
    }
    
    // Search input (Enter key)
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchAgents();
            }
        });
    }
    
    // Refresh buttons
    document.getElementById('refresh-available-btn')?.addEventListener('click', loadAvailableAgents);
    document.getElementById('refresh-installed-btn')?.addEventListener('click', loadInstalledAgents);
}

// Load available agents
function loadAvailableAgents() {
    if (!availableAgentsList) return;
    
    // Show loading indicator
    availableAgentsList.innerHTML = '<p class="text-center py-4">Loading available agents...</p>';
    
    // Fetch available agents
    fetch('/api/marketplace/available')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                availableAgentsList.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            if (!data.agents || data.agents.length === 0) {
                availableAgentsList.innerHTML = '<p class="text-center py-4">No available agents found</p>';
                return;
            }
            
            // Display agents
            let html = '<div class="space-y-3">';
            
            data.agents.forEach(agent => {
                const isInstalled = agent.installed;
                const buttonClass = isInstalled ? 'bg-gray-500 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700';
                const buttonText = isInstalled ? 'Installed' : 'Install';
                
                html += `
                    <div class="bg-white p-3 rounded-lg shadow hover:shadow-md transition-shadow">
                        <div class="flex justify-between items-start">
                            <div class="flex-grow">
                                <h4 class="font-medium text-lg">${agent.name}</h4>
                                <p class="text-gray-600 text-sm mb-1">${agent.description}</p>
                                <div class="flex items-center text-xs text-gray-500">
                                    <span class="mr-2">v${agent.version}</span>
                                    <span>by ${agent.author}</span>
                                </div>
                            </div>
                            <div class="ml-4 flex flex-col items-end">
                                <div class="flex items-center mb-2">
                                    <span class="text-yellow-500 mr-1">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                        </svg>
                                    </span>
                                    <span>${agent.rating.toFixed(1)}</span>
                                    <span class="ml-2">${agent.downloads} downloads</span>
                                </div>
                                <button 
                                    class="${buttonClass} text-white px-3 py-1 rounded text-sm" 
                                    ${isInstalled ? 'disabled' : `onclick="installAgent('${agent.agent_id}')"`}
                                >
                                    ${buttonText}
                                </button>
                            </div>
                        </div>
                        <div class="mt-2 flex flex-wrap">
                            ${agent.tags.map(tag => `
                                <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-1 mb-1">${tag}</span>
                            `).join('')}
                        </div>
                        <div class="mt-2">
                            <button class="text-blue-600 hover:text-blue-800 text-sm" onclick="viewAgentDetails('${agent.agent_id}')">
                                View Details
                            </button>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            availableAgentsList.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading available agents:', error);
            availableAgentsList.innerHTML = `<p class="text-center py-4 text-red-500">Error loading available agents: ${error.message}</p>`;
        });
}

// Load installed agents
function loadInstalledAgents() {
    if (!installedAgentsList) return;
    
    // Show loading indicator
    installedAgentsList.innerHTML = '<p class="text-center py-4">Loading installed agents...</p>';
    
    // Fetch installed agents
    fetch('/api/marketplace/installed')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                installedAgentsList.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            if (!data.agents || data.agents.length === 0) {
                installedAgentsList.innerHTML = '<p class="text-center py-4">No agents installed</p>';
                return;
            }
            
            // Display agents
            let html = '<div class="space-y-3">';
            
            data.agents.forEach(agent => {
                html += `
                    <div class="bg-white p-3 rounded-lg shadow hover:shadow-md transition-shadow">
                        <div class="flex justify-between items-start">
                            <div class="flex-grow">
                                <h4 class="font-medium text-lg">${agent.name}</h4>
                                <p class="text-gray-600 text-sm mb-1">${agent.description}</p>
                                <div class="flex items-center text-xs text-gray-500">
                                    <span class="mr-2">v${agent.version}</span>
                                    <span>by ${agent.author}</span>
                                </div>
                            </div>
                            <div class="ml-4">
                                <button 
                                    class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
                                    onclick="uninstallAgent('${agent.agent_id}')"
                                >
                                    Uninstall
                                </button>
                            </div>
                        </div>
                        <div class="mt-2 flex flex-wrap">
                            ${agent.tags.map(tag => `
                                <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-1 mb-1">${tag}</span>
                            `).join('')}
                        </div>
                        <div class="mt-2 flex justify-between">
                            <button class="text-blue-600 hover:text-blue-800 text-sm" onclick="viewAgentDetails('${agent.agent_id}')">
                                View Details
                            </button>
                            <div class="flex items-center">
                                <span class="text-sm text-gray-600 mr-2">Rate:</span>
                                <div class="flex">
                                    ${[1, 2, 3, 4, 5].map(star => `
                                        <button class="text-yellow-500 hover:text-yellow-600" onclick="rateAgent('${agent.agent_id}', ${star})">
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                            </svg>
                                        </button>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            installedAgentsList.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading installed agents:', error);
            installedAgentsList.innerHTML = `<p class="text-center py-4 text-red-500">Error loading installed agents: ${error.message}</p>`;
        });
}

// View agent details
function viewAgentDetails(agentId) {
    if (!agentDetailsContainer) return;
    
    // Show loading indicator
    agentDetailsContainer.innerHTML = '<p class="text-center py-4">Loading agent details...</p>';
    
    // Fetch agent details
    fetch(`/api/marketplace/agent/${agentId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                agentDetailsContainer.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            const agent = data.agent;
            if (!agent) {
                agentDetailsContainer.innerHTML = `<p class="text-center py-4 text-red-500">Agent not found</p>`;
                return;
            }
            
            // Display agent details
            let html = `
                <div class="bg-white p-4 rounded-lg shadow">
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="text-xl font-medium">${agent.name}</h3>
                        <button class="text-gray-500 hover:text-gray-700" onclick="closeAgentDetails()">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    
                    <div class="mb-4">
                        <p class="text-gray-600 mb-2">${agent.description}</p>
                        <div class="flex items-center text-sm text-gray-500 mb-2">
                            <span class="mr-3">Version: ${agent.version}</span>
                            <span>Author: ${agent.author}</span>
                        </div>
                        <div class="flex items-center">
                            <span class="text-yellow-500 mr-1">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                </svg>
                            </span>
                            <span class="mr-3">${agent.rating.toFixed(1)}</span>
                            <span>${agent.downloads} downloads</span>
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <h4 class="font-medium mb-2">Tags</h4>
                        <div class="flex flex-wrap">
                            ${agent.tags.map(tag => `
                                <span class="bg-blue-100 text-blue-800 text-sm px-2 py-1 rounded mr-2 mb-2">${tag}</span>
                            `).join('')}
                        </div>
                    </div>
                    
                    ${agent.requirements && agent.requirements.length > 0 ? `
                        <div class="mb-4">
                            <h4 class="font-medium mb-2">Requirements</h4>
                            <ul class="list-disc list-inside text-gray-600">
                                ${agent.requirements.map(req => `<li>${req}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    <div class="flex flex-wrap mb-4">
                        ${agent.repository_url ? `
                            <a href="${agent.repository_url}" target="_blank" class="text-blue-600 hover:text-blue-800 mr-4">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                                </svg>
                                Repository
                            </a>
                        ` : ''}
                        
                        ${agent.homepage_url ? `
                            <a href="${agent.homepage_url}" target="_blank" class="text-blue-600 hover:text-blue-800">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                Homepage
                            </a>
                        ` : ''}
                    </div>
                    
                    <div class="flex justify-end">
                        ${agent.installed ? `
                            <button 
                                class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded"
                                onclick="uninstallAgent('${agent.agent_id}')"
                            >
                                Uninstall
                            </button>
                        ` : `
                            <button 
                                class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
                                onclick="installAgent('${agent.agent_id}')"
                            >
                                Install
                            </button>
                        `}
                    </div>
                </div>
            `;
            
            agentDetailsContainer.innerHTML = html;
            agentDetailsContainer.classList.remove('hidden');
        })
        .catch(error => {
            console.error('Error loading agent details:', error);
            agentDetailsContainer.innerHTML = `<p class="text-center py-4 text-red-500">Error loading agent details: ${error.message}</p>`;
        });
}

// Close agent details
function closeAgentDetails() {
    if (agentDetailsContainer) {
        agentDetailsContainer.innerHTML = '';
        agentDetailsContainer.classList.add('hidden');
    }
}

// Install agent
function installAgent(agentId) {
    // Show confirmation dialog
    if (!confirm(`Are you sure you want to install this agent?`)) {
        return;
    }
    
    // Install agent
    fetch(`/api/marketplace/install/${agentId}`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error installing agent: ${data.error}`);
                return;
            }
            
            alert('Agent installed successfully');
            
            // Reload agents
            loadInstalledAgents();
            loadAvailableAgents();
            
            // Reload agent details if open
            if (agentDetailsContainer && !agentDetailsContainer.classList.contains('hidden')) {
                viewAgentDetails(agentId);
            }
        })
        .catch(error => {
            console.error('Error installing agent:', error);
            alert(`Error installing agent: ${error.message}`);
        });
}

// Uninstall agent
function uninstallAgent(agentId) {
    // Show confirmation dialog
    if (!confirm(`Are you sure you want to uninstall this agent?`)) {
        return;
    }
    
    // Uninstall agent
    fetch(`/api/marketplace/uninstall/${agentId}`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error uninstalling agent: ${data.error}`);
                return;
            }
            
            alert('Agent uninstalled successfully');
            
            // Reload agents
            loadInstalledAgents();
            loadAvailableAgents();
            
            // Close agent details if open
            closeAgentDetails();
        })
        .catch(error => {
            console.error('Error uninstalling agent:', error);
            alert(`Error uninstalling agent: ${error.message}`);
        });
}

// Rate agent
function rateAgent(agentId, rating) {
    // Rate agent
    fetch(`/api/marketplace/rate/${agentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ rating })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error rating agent: ${data.error}`);
                return;
            }
            
            alert(`Thank you for rating this agent!`);
            
            // Reload agents
            loadInstalledAgents();
            loadAvailableAgents();
            
            // Reload agent details if open
            if (agentDetailsContainer && !agentDetailsContainer.classList.contains('hidden')) {
                viewAgentDetails(agentId);
            }
        })
        .catch(error => {
            console.error('Error rating agent:', error);
            alert(`Error rating agent: ${error.message}`);
        });
}

// Search agents
function searchAgents() {
    if (!searchInput || !availableAgentsList) return;
    
    const query = searchInput.value.trim();
    if (!query) {
        loadAvailableAgents();
        return;
    }
    
    // Show loading indicator
    availableAgentsList.innerHTML = '<p class="text-center py-4">Searching agents...</p>';
    
    // Search agents
    fetch(`/api/marketplace/search?query=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                availableAgentsList.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            if (!data.agents || data.agents.length === 0) {
                availableAgentsList.innerHTML = `<p class="text-center py-4">No agents found matching "${query}"</p>`;
                return;
            }
            
            // Display agents
            let html = `
                <div class="mb-3 flex justify-between items-center">
                    <h3 class="font-medium">Search Results for "${query}"</h3>
                    <button class="text-sm text-blue-600 hover:text-blue-800" onclick="loadAvailableAgents()">
                        Clear Search
                    </button>
                </div>
                <div class="space-y-3">
            `;
            
            data.agents.forEach(agent => {
                const isInstalled = agent.installed;
                const buttonClass = isInstalled ? 'bg-gray-500 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700';
                const buttonText = isInstalled ? 'Installed' : 'Install';
                
                html += `
                    <div class="bg-white p-3 rounded-lg shadow hover:shadow-md transition-shadow">
                        <div class="flex justify-between items-start">
                            <div class="flex-grow">
                                <h4 class="font-medium text-lg">${agent.name}</h4>
                                <p class="text-gray-600 text-sm mb-1">${agent.description}</p>
                                <div class="flex items-center text-xs text-gray-500">
                                    <span class="mr-2">v${agent.version}</span>
                                    <span>by ${agent.author}</span>
                                </div>
                            </div>
                            <div class="ml-4 flex flex-col items-end">
                                <div class="flex items-center mb-2">
                                    <span class="text-yellow-500 mr-1">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                        </svg>
                                    </span>
                                    <span>${agent.rating.toFixed(1)}</span>
                                    <span class="ml-2">${agent.downloads} downloads</span>
                                </div>
                                <button 
                                    class="${buttonClass} text-white px-3 py-1 rounded text-sm" 
                                    ${isInstalled ? 'disabled' : `onclick="installAgent('${agent.agent_id}')"`}
                                >
                                    ${buttonText}
                                </button>
                            </div>
                        </div>
                        <div class="mt-2 flex flex-wrap">
                            ${agent.tags.map(tag => `
                                <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-1 mb-1">${tag}</span>
                            `).join('')}
                        </div>
                        <div class="mt-2">
                            <button class="text-blue-600 hover:text-blue-800 text-sm" onclick="viewAgentDetails('${agent.agent_id}')">
                                View Details
                            </button>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            availableAgentsList.innerHTML = html;
        })
        .catch(error => {
            console.error('Error searching agents:', error);
            availableAgentsList.innerHTML = `<p class="text-center py-4 text-red-500">Error searching agents: ${error.message}</p>`;
        });
}

// Export functions for use in other modules
window.initMarketplace = initMarketplace;
window.installAgent = installAgent;
window.uninstallAgent = uninstallAgent;
window.rateAgent = rateAgent;
window.viewAgentDetails = viewAgentDetails;
window.closeAgentDetails = closeAgentDetails;
