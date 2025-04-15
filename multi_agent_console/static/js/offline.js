/**
 * Offline functionality for MultiAgentConsole Web UI
 */

// DOM Elements
const offlinePanel = document.getElementById('offline-panel');
const offlineModeToggle = document.getElementById('offline-mode-toggle');
const cacheStatsContainer = document.getElementById('cache-stats');
const knowledgeBaseContainer = document.getElementById('knowledge-base-container');
const knowledgeBaseTopicsList = document.getElementById('knowledge-base-topics');
const knowledgeBaseContent = document.getElementById('knowledge-base-content');
const knowledgeBaseSearch = document.getElementById('kb-search-input');
const knowledgeBaseSearchBtn = document.getElementById('kb-search-btn');

// Initialize offline functionality
function initOffline() {
    // Set up event listeners
    setupOfflineEventListeners();
    
    // Check offline status
    checkOfflineStatus();
    
    // Load initial content
    loadCacheStats();
    loadKnowledgeBaseTopics();
    
    console.log('Offline functionality initialized');
}

// Set up event listeners for offline functionality
function setupOfflineEventListeners() {
    // Offline mode toggle
    if (offlineModeToggle) {
        offlineModeToggle.addEventListener('change', toggleOfflineMode);
    }
    
    // Knowledge base search
    if (knowledgeBaseSearchBtn) {
        knowledgeBaseSearchBtn.addEventListener('click', searchKnowledgeBase);
    }
    
    if (knowledgeBaseSearch) {
        knowledgeBaseSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchKnowledgeBase();
            }
        });
    }
    
    // Refresh buttons
    document.getElementById('refresh-cache-btn')?.addEventListener('click', loadCacheStats);
    document.getElementById('refresh-kb-btn')?.addEventListener('click', loadKnowledgeBaseTopics);
    
    // Clear cache button
    document.getElementById('clear-cache-btn')?.addEventListener('click', clearCache);
}

// Check offline status
function checkOfflineStatus() {
    fetch('/api/offline/status')
        .then(response => response.json())
        .then(data => {
            if (offlineModeToggle) {
                offlineModeToggle.checked = data.offline_mode;
                updateOfflineModeDisplay(data.offline_mode);
            }
        })
        .catch(error => {
            console.error('Error checking offline status:', error);
        });
}

// Toggle offline mode
function toggleOfflineMode() {
    const enabled = offlineModeToggle.checked;
    
    fetch('/api/offline/mode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ enabled })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error toggling offline mode: ${data.error}`);
                // Revert toggle
                offlineModeToggle.checked = !enabled;
                return;
            }
            
            updateOfflineModeDisplay(enabled);
        })
        .catch(error => {
            console.error('Error toggling offline mode:', error);
            // Revert toggle
            offlineModeToggle.checked = !enabled;
        });
}

// Update offline mode display
function updateOfflineModeDisplay(enabled) {
    const statusText = document.getElementById('offline-status-text');
    if (statusText) {
        statusText.textContent = enabled ? 'Enabled' : 'Disabled';
        statusText.className = enabled ? 'text-green-600 font-medium' : 'text-gray-600';
    }
    
    // Update UI elements that should be disabled in offline mode
    const offlineSensitiveElements = document.querySelectorAll('.offline-sensitive');
    offlineSensitiveElements.forEach(element => {
        if (enabled) {
            element.classList.add('opacity-50', 'pointer-events-none');
        } else {
            element.classList.remove('opacity-50', 'pointer-events-none');
        }
    });
}

// Load cache statistics
function loadCacheStats() {
    if (!cacheStatsContainer) return;
    
    // Show loading indicator
    cacheStatsContainer.innerHTML = '<p class="text-center py-4">Loading cache statistics...</p>';
    
    // Fetch cache statistics
    fetch('/api/offline/cache/stats')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                cacheStatsContainer.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            // Format dates
            const oldestEntry = data.oldest_entry ? new Date(data.oldest_entry * 1000).toLocaleString() : 'N/A';
            const newestEntry = data.newest_entry ? new Date(data.newest_entry * 1000).toLocaleString() : 'N/A';
            
            // Format size
            const totalSizeFormatted = formatBytes(data.total_size_bytes);
            
            // Display statistics
            cacheStatsContainer.innerHTML = `
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div class="bg-white p-3 rounded-lg shadow">
                        <div class="text-sm text-gray-500">Total Entries</div>
                        <div class="text-xl font-semibold">${data.total_entries}</div>
                    </div>
                    <div class="bg-white p-3 rounded-lg shadow">
                        <div class="text-sm text-gray-500">Usage</div>
                        <div class="text-xl font-semibold">${data.usage_percentage.toFixed(1)}%</div>
                        <div class="text-xs text-gray-500">${data.total_entries} / ${data.max_size}</div>
                    </div>
                    <div class="bg-white p-3 rounded-lg shadow">
                        <div class="text-sm text-gray-500">Total Size</div>
                        <div class="text-xl font-semibold">${totalSizeFormatted}</div>
                    </div>
                    <div class="bg-white p-3 rounded-lg shadow">
                        <div class="text-sm text-gray-500">Expired Entries</div>
                        <div class="text-xl font-semibold">${data.expired_entries}</div>
                    </div>
                    <div class="bg-white p-3 rounded-lg shadow">
                        <div class="text-sm text-gray-500">Oldest Entry</div>
                        <div class="text-xl font-semibold">${oldestEntry}</div>
                    </div>
                    <div class="bg-white p-3 rounded-lg shadow">
                        <div class="text-sm text-gray-500">Newest Entry</div>
                        <div class="text-xl font-semibold">${newestEntry}</div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <div class="bg-white p-3 rounded-lg shadow">
                        <div class="text-sm text-gray-500">Most Accessed Entry</div>
                        <div class="text-lg font-semibold">${data.most_accessed_key || 'N/A'}</div>
                        <div class="text-xs text-gray-500">Accessed ${data.most_accessed_count} times</div>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            console.error('Error loading cache statistics:', error);
            cacheStatsContainer.innerHTML = `<p class="text-center py-4 text-red-500">Error loading cache statistics: ${error.message}</p>`;
        });
}

// Clear cache
function clearCache() {
    if (!confirm('Are you sure you want to clear the cache? This action cannot be undone.')) {
        return;
    }
    
    fetch('/api/offline/cache/clear', {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error clearing cache: ${data.error}`);
                return;
            }
            
            alert('Cache cleared successfully');
            loadCacheStats();
        })
        .catch(error => {
            console.error('Error clearing cache:', error);
            alert(`Error clearing cache: ${error.message}`);
        });
}

// Load knowledge base topics
function loadKnowledgeBaseTopics() {
    if (!knowledgeBaseTopicsList) return;
    
    // Show loading indicator
    knowledgeBaseTopicsList.innerHTML = '<p class="text-center py-4">Loading topics...</p>';
    
    // Fetch topics
    fetch('/api/offline/kb/topics')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                knowledgeBaseTopicsList.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            if (!data.topics || data.topics.length === 0) {
                knowledgeBaseTopicsList.innerHTML = '<p class="text-center py-4">No topics available</p>';
                return;
            }
            
            // Display topics
            let html = '<div class="space-y-2">';
            
            data.topics.forEach(topic => {
                const latestDate = topic.latest_date ? new Date(topic.latest_date).toLocaleDateString() : 'N/A';
                
                html += `
                    <div class="bg-white p-3 rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer" onclick="loadTopicEntries('${topic.name}')">
                        <div class="font-medium">${topic.name}</div>
                        <div class="flex justify-between text-sm text-gray-500">
                            <div>${topic.file_count} entries</div>
                            <div>Latest: ${latestDate}</div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            knowledgeBaseTopicsList.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading knowledge base topics:', error);
            knowledgeBaseTopicsList.innerHTML = `<p class="text-center py-4 text-red-500">Error loading topics: ${error.message}</p>`;
        });
}

// Load topic entries
function loadTopicEntries(topic) {
    if (!knowledgeBaseContent) return;
    
    // Show loading indicator
    knowledgeBaseContent.innerHTML = '<p class="text-center py-4">Loading entries...</p>';
    
    // Fetch entries
    fetch(`/api/offline/kb/topics/${encodeURIComponent(topic)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                knowledgeBaseContent.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            if (!data.entries || data.entries.length === 0) {
                knowledgeBaseContent.innerHTML = '<p class="text-center py-4">No entries available</p>';
                return;
            }
            
            // Display entries
            let html = `
                <div class="mb-4 flex justify-between items-center">
                    <h3 class="text-lg font-medium">Topic: ${topic}</h3>
                    <button class="text-sm text-blue-600 hover:text-blue-800" onclick="loadKnowledgeBaseTopics()">
                        ← Back to Topics
                    </button>
                </div>
                <div class="space-y-3">
            `;
            
            data.entries.forEach(entry => {
                const date = entry.date ? new Date(entry.date).toLocaleString() : 'N/A';
                const sizeFormatted = formatBytes(entry.size_bytes);
                
                html += `
                    <div class="bg-white p-3 rounded-lg shadow">
                        <div class="flex justify-between items-start">
                            <div class="font-medium">${entry.filename}</div>
                            <button class="text-sm text-red-600 hover:text-red-800" onclick="deleteEntry('${topic}', '${entry.filename}')">
                                Delete
                            </button>
                        </div>
                        <div class="text-sm text-gray-500 mb-2">
                            ${date} • ${sizeFormatted}
                        </div>
                        <button class="text-sm text-blue-600 hover:text-blue-800" onclick="viewEntry('${topic}', '${entry.filename}')">
                            View Content
                        </button>
                    </div>
                `;
            });
            
            html += '</div>';
            knowledgeBaseContent.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading topic entries:', error);
            knowledgeBaseContent.innerHTML = `<p class="text-center py-4 text-red-500">Error loading entries: ${error.message}</p>`;
        });
}

// View entry content
function viewEntry(topic, filename) {
    if (!knowledgeBaseContent) return;
    
    // Show loading indicator
    knowledgeBaseContent.innerHTML = '<p class="text-center py-4">Loading entry content...</p>';
    
    // Fetch entry content
    fetch(`/api/offline/kb/topics/${encodeURIComponent(topic)}/${encodeURIComponent(filename)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                knowledgeBaseContent.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            // Display entry content
            let html = `
                <div class="mb-4 flex justify-between items-center">
                    <h3 class="text-lg font-medium">${filename}</h3>
                    <button class="text-sm text-blue-600 hover:text-blue-800" onclick="loadTopicEntries('${topic}')">
                        ← Back to Entries
                    </button>
                </div>
                <div class="bg-white p-4 rounded-lg shadow">
                    <pre class="whitespace-pre-wrap text-sm">${data.content}</pre>
                </div>
                <div class="mt-4 flex justify-end">
                    <button class="text-sm text-red-600 hover:text-red-800" onclick="deleteEntry('${topic}', '${filename}')">
                        Delete Entry
                    </button>
                </div>
            `;
            
            knowledgeBaseContent.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading entry content:', error);
            knowledgeBaseContent.innerHTML = `<p class="text-center py-4 text-red-500">Error loading entry content: ${error.message}</p>`;
        });
}

// Delete entry
function deleteEntry(topic, filename) {
    if (!confirm(`Are you sure you want to delete the entry "${filename}" from topic "${topic}"? This action cannot be undone.`)) {
        return;
    }
    
    fetch(`/api/offline/kb/topics/${encodeURIComponent(topic)}/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error deleting entry: ${data.error}`);
                return;
            }
            
            alert('Entry deleted successfully');
            loadTopicEntries(topic);
        })
        .catch(error => {
            console.error('Error deleting entry:', error);
            alert(`Error deleting entry: ${error.message}`);
        });
}

// Search knowledge base
function searchKnowledgeBase() {
    if (!knowledgeBaseContent || !knowledgeBaseSearch) return;
    
    const query = knowledgeBaseSearch.value.trim();
    if (!query) {
        alert('Please enter a search query');
        return;
    }
    
    // Show loading indicator
    knowledgeBaseContent.innerHTML = '<p class="text-center py-4">Searching knowledge base...</p>';
    
    // Fetch search results
    fetch(`/api/offline/kb/search?query=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                knowledgeBaseContent.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            if (!data.results || data.results.length === 0) {
                knowledgeBaseContent.innerHTML = `<p class="text-center py-4">No results found for "${query}"</p>`;
                return;
            }
            
            // Display search results
            let html = `
                <div class="mb-4 flex justify-between items-center">
                    <h3 class="text-lg font-medium">Search Results for "${query}"</h3>
                    <button class="text-sm text-blue-600 hover:text-blue-800" onclick="loadKnowledgeBaseTopics()">
                        ← Back to Topics
                    </button>
                </div>
                <div class="space-y-4">
            `;
            
            data.results.forEach(result => {
                const date = result.date ? new Date(result.date).toLocaleString() : 'N/A';
                
                // Truncate content if too long
                let content = result.content;
                if (content.length > 200) {
                    content = content.substring(0, 200) + '...';
                }
                
                html += `
                    <div class="bg-white p-4 rounded-lg shadow">
                        <div class="flex justify-between items-start">
                            <div>
                                <div class="font-medium">${result.topic} / ${result.filename}</div>
                                <div class="text-sm text-gray-500 mb-2">${date}</div>
                            </div>
                            <button class="text-sm text-blue-600 hover:text-blue-800" onclick="viewEntry('${result.topic}', '${result.filename}')">
                                View Full Content
                            </button>
                        </div>
                        <div class="text-sm border-t pt-2 mt-2">
                            <pre class="whitespace-pre-wrap">${content}</pre>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            knowledgeBaseContent.innerHTML = html;
        })
        .catch(error => {
            console.error('Error searching knowledge base:', error);
            knowledgeBaseContent.innerHTML = `<p class="text-center py-4 text-red-500">Error searching knowledge base: ${error.message}</p>`;
        });
}

// Add to knowledge base
function addToKnowledgeBase(topic, content) {
    if (!topic || !content) {
        alert('Topic and content are required');
        return;
    }
    
    fetch('/api/offline/kb/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ topic, content })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error adding to knowledge base: ${data.error}`);
                return;
            }
            
            alert('Added to knowledge base successfully');
            loadKnowledgeBaseTopics();
        })
        .catch(error => {
            console.error('Error adding to knowledge base:', error);
            alert(`Error adding to knowledge base: ${error.message}`);
        });
}

// Format bytes to human-readable format
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Export functions for use in other modules
window.initOffline = initOffline;
window.addToKnowledgeBase = addToKnowledgeBase;
