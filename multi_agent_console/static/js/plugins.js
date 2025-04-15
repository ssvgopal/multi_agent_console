/**
 * Plugin functionality for MultiAgentConsole Web UI
 */

// DOM Elements
const pluginsPanel = document.getElementById('plugins-panel');
const installedPluginsList = document.getElementById('installed-plugins-list');
const availablePluginsList = document.getElementById('available-plugins-list');
const pluginDetailsContainer = document.getElementById('plugin-details');
const searchInput = document.getElementById('plugin-search-input');
const searchBtn = document.getElementById('plugin-search-btn');

// Initialize plugins functionality
function initPlugins() {
    // Set up event listeners
    setupPluginsEventListeners();
    
    // Load initial content
    loadInstalledPlugins();
    loadAvailablePlugins();
    
    console.log('Plugins functionality initialized');
}

// Set up event listeners for plugins functionality
function setupPluginsEventListeners() {
    // Search button
    if (searchBtn) {
        searchBtn.addEventListener('click', searchPlugins);
    }
    
    // Search input (Enter key)
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchPlugins();
            }
        });
    }
    
    // Refresh buttons
    document.getElementById('refresh-available-plugins-btn')?.addEventListener('click', loadAvailablePlugins);
    document.getElementById('refresh-installed-plugins-btn')?.addEventListener('click', loadInstalledPlugins);
}

// Load installed plugins
function loadInstalledPlugins() {
    if (!installedPluginsList) return;
    
    // Show loading indicator
    installedPluginsList.innerHTML = '<p class="text-center py-4">Loading installed plugins...</p>';
    
    // Fetch installed plugins
    fetch('/api/plugins')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                installedPluginsList.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            const installedPlugins = data.plugins.filter(plugin => plugin.enabled);
            
            if (!installedPlugins || installedPlugins.length === 0) {
                installedPluginsList.innerHTML = '<p class="text-center py-4">No plugins installed</p>';
                return;
            }
            
            // Display plugins
            let html = '<div class="space-y-3">';
            
            installedPlugins.forEach(plugin => {
                html += `
                    <div class="bg-white p-3 rounded-lg shadow hover:shadow-md transition-shadow">
                        <div class="flex justify-between items-start">
                            <div class="flex-grow">
                                <h4 class="font-medium text-lg">${plugin.name}</h4>
                                <p class="text-gray-600 text-sm mb-1">${plugin.description}</p>
                                <div class="flex items-center text-xs text-gray-500">
                                    <span class="mr-2">v${plugin.version}</span>
                                    <span>by ${plugin.author}</span>
                                </div>
                            </div>
                            <div class="ml-4">
                                <button 
                                    class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
                                    onclick="disablePlugin('${plugin.id}')"
                                >
                                    Disable
                                </button>
                            </div>
                        </div>
                        <div class="mt-2 flex flex-wrap">
                            ${plugin.capabilities ? plugin.capabilities.map(capability => `
                                <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-1 mb-1">${capability}</span>
                            `).join('') : ''}
                        </div>
                        <div class="mt-2">
                            <button class="text-blue-600 hover:text-blue-800 text-sm" onclick="viewPluginDetails('${plugin.id}')">
                                View Details
                            </button>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            installedPluginsList.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading installed plugins:', error);
            installedPluginsList.innerHTML = `<p class="text-center py-4 text-red-500">Error loading installed plugins: ${error.message}</p>`;
        });
}

// Load available plugins
function loadAvailablePlugins() {
    if (!availablePluginsList) return;
    
    // Show loading indicator
    availablePluginsList.innerHTML = '<p class="text-center py-4">Loading available plugins...</p>';
    
    // Fetch available plugins
    fetch('/api/plugins/registry')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                availablePluginsList.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            if (!data.plugins || data.plugins.length === 0) {
                availablePluginsList.innerHTML = '<p class="text-center py-4">No available plugins found</p>';
                return;
            }
            
            // Display plugins
            let html = '<div class="space-y-3">';
            
            data.plugins.forEach(plugin => {
                const isInstalled = plugin.installed;
                const buttonClass = isInstalled ? 'bg-gray-500 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700';
                const buttonText = isInstalled ? 'Installed' : 'Install';
                
                html += `
                    <div class="bg-white p-3 rounded-lg shadow hover:shadow-md transition-shadow">
                        <div class="flex justify-between items-start">
                            <div class="flex-grow">
                                <h4 class="font-medium text-lg">${plugin.name}</h4>
                                <p class="text-gray-600 text-sm mb-1">${plugin.description}</p>
                                <div class="flex items-center text-xs text-gray-500">
                                    <span class="mr-2">v${plugin.version}</span>
                                    <span>by ${plugin.author}</span>
                                </div>
                            </div>
                            <div class="ml-4 flex flex-col items-end">
                                <div class="flex items-center mb-2">
                                    <span class="text-yellow-500 mr-1">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                        </svg>
                                    </span>
                                    <span>${plugin.rating ? plugin.rating.toFixed(1) : '0.0'}</span>
                                    <span class="ml-2">${plugin.downloads || 0} downloads</span>
                                </div>
                                <button 
                                    class="${buttonClass} text-white px-3 py-1 rounded text-sm" 
                                    ${isInstalled ? 'disabled' : `onclick="installPlugin('${plugin.plugin_id}')`}
                                >
                                    ${buttonText}
                                </button>
                            </div>
                        </div>
                        <div class="mt-2 flex flex-wrap">
                            ${plugin.tags ? plugin.tags.map(tag => `
                                <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-1 mb-1">${tag}</span>
                            `).join('') : ''}
                        </div>
                        <div class="mt-2">
                            <button class="text-blue-600 hover:text-blue-800 text-sm" onclick="viewPluginDetails('${plugin.plugin_id}')">
                                View Details
                            </button>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            availablePluginsList.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading available plugins:', error);
            availablePluginsList.innerHTML = `<p class="text-center py-4 text-red-500">Error loading available plugins: ${error.message}</p>`;
        });
}

// View plugin details
function viewPluginDetails(pluginId) {
    if (!pluginDetailsContainer) return;
    
    // Show loading indicator
    pluginDetailsContainer.innerHTML = '<p class="text-center py-4">Loading plugin details...</p>';
    
    // Fetch plugin details
    fetch(`/api/plugins/${pluginId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                pluginDetailsContainer.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            const plugin = data.plugin;
            if (!plugin) {
                pluginDetailsContainer.innerHTML = `<p class="text-center py-4 text-red-500">Plugin not found</p>`;
                return;
            }
            
            // Display plugin details
            let html = `
                <div class="bg-white p-4 rounded-lg shadow">
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="text-xl font-medium">${plugin.name}</h3>
                        <button class="text-gray-500 hover:text-gray-700" onclick="closePluginDetails()">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    
                    <div class="mb-4">
                        <p class="text-gray-600 mb-2">${plugin.description}</p>
                        <div class="flex items-center text-sm text-gray-500 mb-2">
                            <span class="mr-3">Version: ${plugin.version}</span>
                            <span>Author: ${plugin.author}</span>
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <h4 class="font-medium mb-2">Capabilities</h4>
                        <div class="flex flex-wrap">
                            ${plugin.capabilities ? plugin.capabilities.map(capability => `
                                <span class="bg-blue-100 text-blue-800 text-sm px-2 py-1 rounded mr-2 mb-2">${capability}</span>
                            `).join('') : '<span class="text-gray-500">No capabilities listed</span>'}
                        </div>
                    </div>
                    
                    ${plugin.dependencies && plugin.dependencies.length > 0 ? `
                        <div class="mb-4">
                            <h4 class="font-medium mb-2">Dependencies</h4>
                            <ul class="list-disc list-inside text-gray-600">
                                ${plugin.dependencies.map(dep => `<li>${dep}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    <div class="flex justify-end">
                        ${plugin.enabled ? `
                            <button 
                                class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded"
                                onclick="disablePlugin('${plugin.id}')"
                            >
                                Disable
                            </button>
                        ` : `
                            <button 
                                class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
                                onclick="enablePlugin('${plugin.id}')"
                            >
                                Enable
                            </button>
                        `}
                    </div>
                </div>
            `;
            
            pluginDetailsContainer.innerHTML = html;
            pluginDetailsContainer.classList.remove('hidden');
        })
        .catch(error => {
            console.error('Error loading plugin details:', error);
            pluginDetailsContainer.innerHTML = `<p class="text-center py-4 text-red-500">Error loading plugin details: ${error.message}</p>`;
        });
}

// Close plugin details
function closePluginDetails() {
    if (pluginDetailsContainer) {
        pluginDetailsContainer.innerHTML = '';
        pluginDetailsContainer.classList.add('hidden');
    }
}

// Install plugin
function installPlugin(pluginId) {
    // Show confirmation dialog
    if (!confirm(`Are you sure you want to install this plugin?`)) {
        return;
    }
    
    // Install plugin
    fetch(`/api/plugins/registry/install/${pluginId}`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error installing plugin: ${data.error}`);
                return;
            }
            
            alert('Plugin installed successfully');
            
            // Reload plugins
            loadInstalledPlugins();
            loadAvailablePlugins();
            
            // Reload plugin details if open
            if (pluginDetailsContainer && !pluginDetailsContainer.classList.contains('hidden')) {
                viewPluginDetails(pluginId);
            }
        })
        .catch(error => {
            console.error('Error installing plugin:', error);
            alert(`Error installing plugin: ${error.message}`);
        });
}

// Enable plugin
function enablePlugin(pluginId) {
    // Enable plugin
    fetch(`/api/plugins/${pluginId}/enable`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error enabling plugin: ${data.error}`);
                return;
            }
            
            alert('Plugin enabled successfully');
            
            // Reload plugins
            loadInstalledPlugins();
            
            // Reload plugin details if open
            if (pluginDetailsContainer && !pluginDetailsContainer.classList.contains('hidden')) {
                viewPluginDetails(pluginId);
            }
        })
        .catch(error => {
            console.error('Error enabling plugin:', error);
            alert(`Error enabling plugin: ${error.message}`);
        });
}

// Disable plugin
function disablePlugin(pluginId) {
    // Show confirmation dialog
    if (!confirm(`Are you sure you want to disable this plugin?`)) {
        return;
    }
    
    // Disable plugin
    fetch(`/api/plugins/${pluginId}/disable`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error disabling plugin: ${data.error}`);
                return;
            }
            
            alert('Plugin disabled successfully');
            
            // Reload plugins
            loadInstalledPlugins();
            
            // Reload plugin details if open
            if (pluginDetailsContainer && !pluginDetailsContainer.classList.contains('hidden')) {
                viewPluginDetails(pluginId);
            }
        })
        .catch(error => {
            console.error('Error disabling plugin:', error);
            alert(`Error disabling plugin: ${error.message}`);
        });
}

// Search plugins
function searchPlugins() {
    if (!searchInput || !availablePluginsList) return;
    
    const query = searchInput.value.trim();
    if (!query) {
        loadAvailablePlugins();
        return;
    }
    
    // Show loading indicator
    availablePluginsList.innerHTML = '<p class="text-center py-4">Searching plugins...</p>';
    
    // Search plugins
    fetch(`/api/plugins/registry/search?query=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                availablePluginsList.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            if (!data.plugins || data.plugins.length === 0) {
                availablePluginsList.innerHTML = `<p class="text-center py-4">No plugins found matching "${query}"</p>`;
                return;
            }
            
            // Display plugins
            let html = `
                <div class="mb-3 flex justify-between items-center">
                    <h3 class="font-medium">Search Results for "${query}"</h3>
                    <button class="text-sm text-blue-600 hover:text-blue-800" onclick="loadAvailablePlugins()">
                        Clear Search
                    </button>
                </div>
                <div class="space-y-3">
            `;
            
            data.plugins.forEach(plugin => {
                const isInstalled = plugin.installed;
                const buttonClass = isInstalled ? 'bg-gray-500 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700';
                const buttonText = isInstalled ? 'Installed' : 'Install';
                
                html += `
                    <div class="bg-white p-3 rounded-lg shadow hover:shadow-md transition-shadow">
                        <div class="flex justify-between items-start">
                            <div class="flex-grow">
                                <h4 class="font-medium text-lg">${plugin.name}</h4>
                                <p class="text-gray-600 text-sm mb-1">${plugin.description}</p>
                                <div class="flex items-center text-xs text-gray-500">
                                    <span class="mr-2">v${plugin.version}</span>
                                    <span>by ${plugin.author}</span>
                                </div>
                            </div>
                            <div class="ml-4 flex flex-col items-end">
                                <div class="flex items-center mb-2">
                                    <span class="text-yellow-500 mr-1">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                        </svg>
                                    </span>
                                    <span>${plugin.rating ? plugin.rating.toFixed(1) : '0.0'}</span>
                                    <span class="ml-2">${plugin.downloads || 0} downloads</span>
                                </div>
                                <button 
                                    class="${buttonClass} text-white px-3 py-1 rounded text-sm" 
                                    ${isInstalled ? 'disabled' : `onclick="installPlugin('${plugin.plugin_id}')`}
                                >
                                    ${buttonText}
                                </button>
                            </div>
                        </div>
                        <div class="mt-2 flex flex-wrap">
                            ${plugin.tags ? plugin.tags.map(tag => `
                                <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-1 mb-1">${tag}</span>
                            `).join('') : ''}
                        </div>
                        <div class="mt-2">
                            <button class="text-blue-600 hover:text-blue-800 text-sm" onclick="viewPluginDetails('${plugin.plugin_id}')">
                                View Details
                            </button>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            availablePluginsList.innerHTML = html;
        })
        .catch(error => {
            console.error('Error searching plugins:', error);
            availablePluginsList.innerHTML = `<p class="text-center py-4 text-red-500">Error searching plugins: ${error.message}</p>`;
        });
}

// Export functions for use in other modules
window.initPlugins = initPlugins;
window.installPlugin = installPlugin;
window.enablePlugin = enablePlugin;
window.disablePlugin = disablePlugin;
window.viewPluginDetails = viewPluginDetails;
window.closePluginDetails = closePluginDetails;
