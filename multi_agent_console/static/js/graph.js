/**
 * Graph visualization for MultiAgentConsole Web UI
 */

// DOM Elements
const graphView = document.getElementById('graph-view');
const graphPluginSelector = document.getElementById('graph-plugin-selector');
const analyzeButton = document.getElementById('analyze-button');
const insightsContent = document.getElementById('insights-content');

// State
let currentGraph = null;
let cytoscape = null;

// Initialize the graph visualization
function initGraph() {
    // Load available graph plugins
    loadGraphPlugins();

    // Set up event listeners
    setupGraphEventListeners();

    // Initialize empty graph
    initCytoscape();

    console.log('Graph visualization initialized');
}

// Load available graph plugins
async function loadGraphPlugins() {
    try {
        const response = await fetch('/api/plugins/graph');
        const data = await response.json();

        if (data.plugins && data.plugins.length > 0) {
            // Clear existing options except the first one (default)
            while (graphPluginSelector.options.length > 1) {
                graphPluginSelector.remove(1);
            }

            // Add new options
            data.plugins.forEach(plugin => {
                const option = document.createElement('option');
                option.value = plugin;
                option.textContent = plugin.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
                graphPluginSelector.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading graph plugins:', error);
    }
}

// Set up event listeners for graph functionality
function setupGraphEventListeners() {
    // Analyze button
    analyzeButton.addEventListener('click', analyzeCurrentQuery);

    // Graph plugin selection change
    graphPluginSelector.addEventListener('change', () => {
        // If we have a current graph, re-analyze with the new plugin
        if (currentGraph) {
            analyzeCurrentQuery();
        }
    });

    // Tab activation for graph
    document.getElementById('graph-tab').addEventListener('click', () => {
        // Resize the graph when the tab becomes visible
        setTimeout(() => {
            if (cytoscape) {
                cytoscape.resize();
                cytoscape.fit();
            }
        }, 100);
    });
}

// Initialize Cytoscape.js
function initCytoscape() {
    cytoscape = window.cytoscape({
        container: graphView,
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#6366f1',
                    'label': 'data(id)',
                    'color': '#000000',
                    'text-outline-width': 2,
                    'text-outline-color': '#ffffff',
                    'font-size': '12px',
                    'width': 'data(size)',
                    'height': 'data(size)'
                }
            },
            {
                selector: 'node[group = 2]',
                style: {
                    'background-color': '#f59e0b',
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 'data(weight)',
                    'line-color': '#cbd5e1',
                    'target-arrow-color': '#cbd5e1',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier'
                }
            }
        ],
        layout: {
            name: 'cose',
            idealEdgeLength: 100,
            nodeOverlap: 20,
            refresh: 20,
            fit: true,
            padding: 30,
            randomize: false,
            componentSpacing: 100,
            nodeRepulsion: 400000,
            edgeElasticity: 100,
            nestingFactor: 5,
            gravity: 80,
            numIter: 1000,
            initialTemp: 200,
            coolingFactor: 0.95,
            minTemp: 1.0
        },
        elements: {
            nodes: [],
            edges: []
        }
    });

    // Add zoom controls
    cytoscape.on('tap', 'node', function(evt) {
        const node = evt.target;
        console.log('Tapped node: ' + node.id());
    });
}

// Analyze the current query
function analyzeCurrentQuery() {
    // Get the last user message from the chat
    const userMessages = document.querySelectorAll('.user-message');
    if (userMessages.length === 0) {
        alert('Please send a message first');
        return;
    }

    const lastUserMessage = userMessages[userMessages.length - 1].textContent.trim();
    const selectedPlugin = graphPluginSelector.value;

    // Add thinking indicator to insights
    insightsContent.innerHTML = '<p class="text-gray-500 italic">Analyzing...</p>';

    // Send analysis request via WebSocket if connected
    if (window.isConnected) {
        window.webSocket.send(JSON.stringify({
            type: 'graph_analysis',
            query: lastUserMessage,
            plugin_id: selectedPlugin || null
        }));
    } else {
        // Fallback to REST API
        fetch('/api/graph', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: lastUserMessage,
                plugin_id: selectedPlugin || null
            })
        })
        .then(response => response.json())
        .then(data => {
            updateGraph(data.data);
            updateInsights(data.data);
        })
        .catch(error => {
            console.error('Error analyzing query:', error);
            insightsContent.innerHTML = '<p class="text-red-500">Error analyzing query. Please try again.</p>';
        });
    }
}

// Update the graph visualization with new data
function updateGraph(graphData) {
    if (!graphData || !graphData.nodes) {
        console.error('Invalid graph data:', graphData);
        return;
    }

    // Save current graph data
    currentGraph = graphData;

    // Convert to Cytoscape.js format
    const elements = {
        nodes: graphData.nodes.map(node => ({
            data: {
                id: node.id,
                size: node.size || 30,
                group: node.group || 1
            }
        })),
        edges: graphData.links.map((link, index) => ({
            data: {
                id: 'e' + index,
                source: link.source,
                target: link.target,
                weight: link.value || 1
            }
        }))
    };

    // Update the graph
    cytoscape.elements().remove();
    cytoscape.add(elements);

    // Apply layout
    cytoscape.layout({
        name: 'cose',
        idealEdgeLength: 100,
        nodeOverlap: 20,
        refresh: 20,
        fit: true,
        padding: 30,
        randomize: false,
        componentSpacing: 100,
        nodeRepulsion: 400000,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0
    }).run();
}

// Update the insights panel with graph analysis results
function updateInsights(graphData) {
    if (!graphData) {
        insightsContent.innerHTML = '<p class="text-gray-500 italic">No insights available</p>';
        return;
    }

    let html = '';

    // Add central concepts
    if (graphData.nodes && graphData.nodes.filter(n => n.group === 2).length > 0) {
        const centralConcepts = graphData.nodes
            .filter(n => n.group === 2)
            .map(n => n.id)
            .join(', ');

        html += `<p class="mb-2"><strong class="text-blue-600">Central Concepts:</strong> ${centralConcepts}</p>`;
    }

    // Add suggestions
    if (graphData.suggestions && graphData.suggestions.length > 0) {
        html += '<p class="mb-2"><strong class="text-blue-600">Suggestions:</strong></p><ul class="list-disc ml-5 mb-3">';
        graphData.suggestions.forEach(suggestion => {
            html += `<li class="mb-1">${suggestion}</li>`;
        });
        html += '</ul>';
    }

    // Add graph statistics
    if (graphData.nodes && graphData.links) {
        html += `<div class="p-2 bg-gray-100 rounded mb-3">
            <p class="text-sm font-medium">Graph Statistics:</p>
            <div class="grid grid-cols-2 gap-2 text-sm">
                <div>Concepts: <span class="font-medium">${graphData.nodes.length}</span></div>
                <div>Relationships: <span class="font-medium">${graphData.links.length}</span></div>
            </div>
        </div>`;
    }

    // Add analysis summary if available
    if (graphData.summary) {
        html += `<div class="p-2 border border-blue-200 bg-blue-50 rounded mb-3">
            <p class="text-sm font-medium text-blue-800">Analysis Summary:</p>
            <p class="text-sm">${graphData.summary}</p>
        </div>`;
    } else {
        html += `<div class="p-2 border border-blue-200 bg-blue-50 rounded mb-3">
            <p class="text-sm font-medium text-blue-800">Analysis Summary:</p>
            <p class="text-sm">Analysis complete. Explore the graph to understand relationships between concepts.</p>
        </div>`;
    }

    // Add missing concepts
    if (graphData.missing_concepts && graphData.missing_concepts.length > 0) {
        html += '<p><strong>Missing Concepts:</strong></p><ul class="list-disc ml-5">';
        graphData.missing_concepts.forEach(concept => {
            html += `<li>${concept}</li>`;
        });
        html += '</ul>';
    }

    // Add structural gaps
    if (graphData.structural_gaps && graphData.structural_gaps.length > 0) {
        html += '<p><strong>Structural Gaps:</strong></p><ul class="list-disc ml-5">';
        graphData.structural_gaps.forEach(gap => {
            html += `<li>${gap}</li>`;
        });
        html += '</ul>';
    }

    if (html === '') {
        html = '<p class="text-gray-500 italic">No significant insights found</p>';
    }

    insightsContent.innerHTML = html;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initGraph);
