/**
 * Workflow functionality for MultiAgentConsole Web UI
 */

// DOM Elements
const workflowPanel = document.getElementById('workflow-panel');
const templateList = document.getElementById('workflow-template-list');
const activeWorkflowList = document.getElementById('active-workflow-list');
const workflowContent = document.getElementById('workflow-content');

// Initialize workflow functionality
function initWorkflow() {
    // Set up event listeners
    setupWorkflowEventListeners();
    
    // Load initial content
    loadWorkflowTemplates();
    loadActiveWorkflows();
    
    console.log('Workflow functionality initialized');
}

// Set up event listeners for workflow functionality
function setupWorkflowEventListeners() {
    // Create workflow button
    document.getElementById('create-workflow-btn')?.addEventListener('click', () => {
        const templateName = document.getElementById('template-selector').value;
        if (templateName) {
            createWorkflow(templateName);
        }
    });
    
    // Refresh buttons
    document.getElementById('refresh-templates-btn')?.addEventListener('click', loadWorkflowTemplates);
    document.getElementById('refresh-workflows-btn')?.addEventListener('click', loadActiveWorkflows);
}

// Load workflow templates
function loadWorkflowTemplates() {
    if (!templateList) return;
    
    // Show loading indicator
    templateList.innerHTML = '<p class="text-center py-4">Loading templates...</p>';
    
    // Fetch templates from API
    fetch('/api/workflows/templates')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                templateList.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            if (!data.templates || data.templates.length === 0) {
                templateList.innerHTML = '<p class="text-center py-4">No templates available</p>';
                return;
            }
            
            // Display templates
            let html = '<div class="space-y-4">';
            
            // Add template selector
            html += `
                <div class="mb-4">
                    <label for="template-selector" class="block text-sm font-medium text-gray-700 mb-1">Select Template</label>
                    <div class="flex space-x-2">
                        <select id="template-selector" class="flex-grow border border-gray-300 rounded-md shadow-sm px-3 py-2">
                            ${data.templates.map(template => `
                                <option value="${template.name}">${template.name} (${template.steps_count} steps)</option>
                            `).join('')}
                        </select>
                        <button id="create-workflow-btn" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
                            Create
                        </button>
                    </div>
                </div>
            `;
            
            // List all templates
            html += '<h3 class="font-medium text-lg mb-2">Available Templates</h3>';
            
            data.templates.forEach(template => {
                html += `
                    <div class="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow">
                        <h4 class="font-medium text-lg">${template.name}</h4>
                        <p class="text-gray-600 mb-2">${template.description || 'No description'}</p>
                        <div class="text-sm text-gray-500">Steps: ${template.steps_count}</div>
                    </div>
                `;
            });
            
            html += '</div>';
            templateList.innerHTML = html;
            
            // Re-attach event listener
            document.getElementById('create-workflow-btn')?.addEventListener('click', () => {
                const templateName = document.getElementById('template-selector').value;
                if (templateName) {
                    createWorkflow(templateName);
                }
            });
        })
        .catch(error => {
            console.error('Error loading templates:', error);
            templateList.innerHTML = `<p class="text-center py-4 text-red-500">Error loading templates: ${error.message}</p>`;
        });
}

// Load active workflows
function loadActiveWorkflows() {
    if (!activeWorkflowList) return;
    
    // Show loading indicator
    activeWorkflowList.innerHTML = '<p class="text-center py-4">Loading workflows...</p>';
    
    // Fetch workflows from API
    fetch('/api/workflows')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                activeWorkflowList.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            if (!data.workflows || data.workflows.length === 0) {
                activeWorkflowList.innerHTML = '<p class="text-center py-4">No active workflows</p>';
                return;
            }
            
            // Display workflows
            let html = '<div class="space-y-4">';
            
            data.workflows.forEach(workflow => {
                const isCompleted = workflow.completed;
                const statusClass = isCompleted ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800';
                const statusText = isCompleted ? 'Completed' : 'In Progress';
                
                html += `
                    <div class="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow">
                        <div class="flex justify-between items-start">
                            <h4 class="font-medium text-lg">${workflow.name}</h4>
                            <span class="px-2 py-1 text-xs rounded-full ${statusClass}">${statusText}</span>
                        </div>
                        <p class="text-gray-600 mb-2">${workflow.description || 'No description'}</p>
                        <div class="flex justify-between text-sm text-gray-500">
                            <div>Step ${workflow.current_step + 1} of ${workflow.steps_count}</div>
                            <div>${formatDate(workflow.created_at)}</div>
                        </div>
                        <div class="mt-3 flex space-x-2">
                            <button class="view-workflow-btn bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm" data-id="${workflow.id}">
                                View
                            </button>
                            ${!isCompleted ? `
                                <button class="execute-workflow-btn bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm" data-id="${workflow.id}">
                                    Execute Step
                                </button>
                            ` : ''}
                            <button class="delete-workflow-btn bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm" data-id="${workflow.id}">
                                Delete
                            </button>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            activeWorkflowList.innerHTML = html;
            
            // Add event listeners
            document.querySelectorAll('.view-workflow-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const workflowId = btn.getAttribute('data-id');
                    viewWorkflow(workflowId);
                });
            });
            
            document.querySelectorAll('.execute-workflow-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const workflowId = btn.getAttribute('data-id');
                    executeWorkflowStep(workflowId);
                });
            });
            
            document.querySelectorAll('.delete-workflow-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const workflowId = btn.getAttribute('data-id');
                    deleteWorkflow(workflowId);
                });
            });
        })
        .catch(error => {
            console.error('Error loading workflows:', error);
            activeWorkflowList.innerHTML = `<p class="text-center py-4 text-red-500">Error loading workflows: ${error.message}</p>`;
        });
}

// Create a new workflow
function createWorkflow(templateName) {
    // Show loading indicator
    const createBtn = document.getElementById('create-workflow-btn');
    const originalText = createBtn.textContent;
    createBtn.textContent = 'Creating...';
    createBtn.disabled = true;
    
    // Create workflow
    fetch('/api/workflows/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ template_name: templateName })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error creating workflow: ${data.error}`);
                return;
            }
            
            // Reload workflows
            loadActiveWorkflows();
            
            // Show success message
            alert(`Workflow created: ${data.workflow_id}`);
            
            // View the new workflow
            viewWorkflow(data.workflow_id);
        })
        .catch(error => {
            console.error('Error creating workflow:', error);
            alert(`Error creating workflow: ${error.message}`);
        })
        .finally(() => {
            // Reset button
            createBtn.textContent = originalText;
            createBtn.disabled = false;
        });
}

// View a workflow
function viewWorkflow(workflowId) {
    if (!workflowContent) return;
    
    // Show loading indicator
    workflowContent.innerHTML = '<p class="text-center py-4">Loading workflow...</p>';
    
    // Fetch workflow from API
    fetch(`/api/workflows/${workflowId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                workflowContent.innerHTML = `<p class="text-center py-4 text-red-500">${data.error}</p>`;
                return;
            }
            
            // Display workflow
            let html = `
                <div class="bg-white p-4 rounded-lg shadow">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xl font-medium">${data.name}</h3>
                        <div>
                            <button id="back-to-workflows-btn" class="text-blue-500 hover:text-blue-700">← Back to Workflows</button>
                        </div>
                    </div>
                    
                    <p class="text-gray-600 mb-4">${data.description || 'No description'}</p>
                    
                    <div class="mb-4">
                        <div class="flex justify-between text-sm text-gray-500 mb-2">
                            <div>Created: ${formatDate(data.created_at)}</div>
                            <div>Updated: ${formatDate(data.updated_at)}</div>
                        </div>
                        
                        <div class="w-full bg-gray-200 rounded-full h-2.5">
                            <div class="bg-blue-600 h-2.5 rounded-full" style="width: ${Math.round((data.current_step_index / data.steps.length) * 100)}%"></div>
                        </div>
                        
                        <div class="text-sm text-gray-500 mt-1">
                            Step ${data.current_step_index + 1} of ${data.steps.length}
                            ${data.completed ? ' (Completed)' : ''}
                        </div>
                    </div>
                    
                    <h4 class="font-medium text-lg mb-2">Steps</h4>
                    <div class="space-y-3">
            `;
            
            // Display steps
            data.steps.forEach((step, index) => {
                const isCurrent = index === data.current_step_index;
                const isCompleted = step.completed;
                
                let statusClass = 'bg-gray-100 text-gray-800';
                let statusText = 'Pending';
                
                if (isCompleted) {
                    statusClass = 'bg-green-100 text-green-800';
                    statusText = 'Completed';
                } else if (isCurrent) {
                    statusClass = 'bg-blue-100 text-blue-800';
                    statusText = 'Current';
                }
                
                html += `
                    <div class="border rounded-lg p-3 ${isCurrent ? 'border-blue-500 bg-blue-50' : ''}">
                        <div class="flex justify-between items-start">
                            <h5 class="font-medium">${index + 1}. ${step.name}</h5>
                            <span class="px-2 py-1 text-xs rounded-full ${statusClass}">${statusText}</span>
                        </div>
                        <div class="text-sm text-gray-600 mb-2">Action: ${step.action}</div>
                `;
                
                // Display parameters
                if (step.parameters && Object.keys(step.parameters).length > 0) {
                    html += `
                        <div class="mb-2">
                            <div class="text-sm font-medium">Parameters:</div>
                            <pre class="text-xs bg-gray-100 p-2 rounded">${JSON.stringify(step.parameters, null, 2)}</pre>
                        </div>
                    `;
                }
                
                // Display result if completed
                if (isCompleted && step.result) {
                    html += `
                        <div>
                            <div class="text-sm font-medium">Result:</div>
                            <pre class="text-xs bg-gray-100 p-2 rounded">${JSON.stringify(step.result, null, 2)}</pre>
                        </div>
                    `;
                }
                
                // Display error if any
                if (step.error) {
                    html += `
                        <div>
                            <div class="text-sm font-medium text-red-600">Error:</div>
                            <pre class="text-xs bg-red-50 text-red-600 p-2 rounded">${step.error}</pre>
                        </div>
                    `;
                }
                
                // Display timing information
                if (step.start_time) {
                    html += `
                        <div class="text-xs text-gray-500 mt-2">
                            Started: ${formatDate(step.start_time)}
                            ${step.end_time ? ` • Completed: ${formatDate(step.end_time)}` : ''}
                        </div>
                    `;
                }
                
                html += `</div>`;
            });
            
            html += `
                    </div>
                    
                    <div class="mt-4 flex space-x-2">
                        ${!data.completed ? `
                            <button id="execute-step-btn" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded" data-id="${workflowId}">
                                Execute Current Step
                            </button>
                            <button id="advance-workflow-btn" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded" data-id="${workflowId}">
                                Advance to Next Step
                            </button>
                        ` : ''}
                        <button id="delete-workflow-btn" class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded" data-id="${workflowId}">
                            Delete Workflow
                        </button>
                    </div>
                </div>
            `;
            
            workflowContent.innerHTML = html;
            
            // Add event listeners
            document.getElementById('back-to-workflows-btn')?.addEventListener('click', () => {
                workflowContent.innerHTML = '';
                loadActiveWorkflows();
            });
            
            document.getElementById('execute-step-btn')?.addEventListener('click', () => {
                executeWorkflowStep(workflowId);
            });
            
            document.getElementById('advance-workflow-btn')?.addEventListener('click', () => {
                advanceWorkflow(workflowId);
            });
            
            document.getElementById('delete-workflow-btn')?.addEventListener('click', () => {
                deleteWorkflow(workflowId);
            });
        })
        .catch(error => {
            console.error('Error loading workflow:', error);
            workflowContent.innerHTML = `<p class="text-center py-4 text-red-500">Error loading workflow: ${error.message}</p>`;
        });
}

// Execute a workflow step
function executeWorkflowStep(workflowId) {
    // Show loading indicator
    const executeBtn = document.querySelector(`.execute-workflow-btn[data-id="${workflowId}"]`) || 
                       document.getElementById('execute-step-btn');
    
    if (executeBtn) {
        const originalText = executeBtn.textContent;
        executeBtn.textContent = 'Executing...';
        executeBtn.disabled = true;
    }
    
    // Execute step
    fetch(`/api/workflows/${workflowId}/execute`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error executing step: ${data.error}`);
                return;
            }
            
            // Show success message
            if (data.completed) {
                alert(`Step "${data.step}" executed successfully`);
            } else {
                alert(`Error executing step "${data.step}": ${data.error}`);
            }
            
            // Reload workflow
            viewWorkflow(workflowId);
        })
        .catch(error => {
            console.error('Error executing step:', error);
            alert(`Error executing step: ${error.message}`);
        })
        .finally(() => {
            // Reset button
            if (executeBtn) {
                executeBtn.textContent = originalText;
                executeBtn.disabled = false;
            }
            
            // Reload workflows list
            loadActiveWorkflows();
        });
}

// Advance a workflow to the next step
function advanceWorkflow(workflowId) {
    // Show loading indicator
    const advanceBtn = document.getElementById('advance-workflow-btn');
    
    if (advanceBtn) {
        const originalText = advanceBtn.textContent;
        advanceBtn.textContent = 'Advancing...';
        advanceBtn.disabled = true;
    }
    
    // Advance workflow
    fetch(`/api/workflows/${workflowId}/advance`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error advancing workflow: ${data.error}`);
                return;
            }
            
            // Show success message
            if (data.advanced) {
                alert(`Advanced to step "${data.next_step}"`);
            } else if (data.completed) {
                alert('Workflow completed');
            } else {
                alert('Could not advance workflow');
            }
            
            // Reload workflow
            viewWorkflow(workflowId);
        })
        .catch(error => {
            console.error('Error advancing workflow:', error);
            alert(`Error advancing workflow: ${error.message}`);
        })
        .finally(() => {
            // Reset button
            if (advanceBtn) {
                advanceBtn.textContent = 'Advance to Next Step';
                advanceBtn.disabled = false;
            }
            
            // Reload workflows list
            loadActiveWorkflows();
        });
}

// Delete a workflow
function deleteWorkflow(workflowId) {
    // Confirm deletion
    if (!confirm('Are you sure you want to delete this workflow?')) {
        return;
    }
    
    // Delete workflow
    fetch(`/api/workflows/${workflowId}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error deleting workflow: ${data.error}`);
                return;
            }
            
            // Show success message
            alert('Workflow deleted');
            
            // Clear workflow content
            if (workflowContent) {
                workflowContent.innerHTML = '';
            }
            
            // Reload workflows
            loadActiveWorkflows();
        })
        .catch(error => {
            console.error('Error deleting workflow:', error);
            alert(`Error deleting workflow: ${error.message}`);
        });
}

// Format a date string
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Export functions for use in other modules
window.initWorkflow = initWorkflow;
