/**
 * Tools JavaScript for MultiAgentConsole Web UI
 * 
 * This file handles the tools functionality:
 * - Loading and displaying available tools
 * - Filtering tools by category
 * - Executing tools and displaying results
 * - Handling tool-specific UI interactions
 */

// Tool Categories and their display names
const TOOL_CATEGORIES = {
    'git': 'Git Tools',
    'database': 'Database Tools',
    'api': 'API Tools',
    'media': 'Media Tools',
    'voice': 'Voice Tools',
    'document': 'Document Tools',
    'system': 'System Tools',
    'mcp': 'MCP Tools',
    'graph': 'Graph Tools',
    'a2a': 'A2A Tools'
};

// DOM Elements
const toolCategorySelector = document.getElementById('tool-category-selector');
const toolContainer = document.getElementById('tool-container');
const multimodalCategorySelector = document.getElementById('multimodal-category-selector');

// Image Processing Elements
const imageUpload = document.getElementById('image-upload');
const imageInfoBtn = document.getElementById('image-info-btn');
const ocrImageBtn = document.getElementById('ocr-image-btn');
const resizeImageBtn = document.getElementById('resize-image-btn');
const imagePreview = document.getElementById('image-preview');
const previewImg = document.getElementById('preview-img');
const imageResult = document.getElementById('image-result');

// Audio Processing Elements
const ttsInput = document.getElementById('tts-input');
const ttsBtn = document.getElementById('tts-btn');
const recordAudioBtn = document.getElementById('record-audio-btn');
const audioUpload = document.getElementById('audio-upload');
const audioPlayer = document.getElementById('audio-player');
const audioElement = document.getElementById('audio-element');
const sttBtn = document.getElementById('stt-btn');
const sttResult = document.getElementById('stt-result');

// Chart Generation Elements
const chartType = document.getElementById('chart-type');
const chartData = document.getElementById('chart-data');
const generateChartBtn = document.getElementById('generate-chart-btn');
const chartContainer = document.getElementById('chart-container');
const chartCanvas = document.getElementById('chart-canvas');

// Document Processing Elements
const documentUpload = document.getElementById('document-upload');
const extractTextBtn = document.getElementById('extract-text-btn');
const getDocInfoBtn = document.getElementById('get-doc-info-btn');
const documentResult = document.getElementById('document-result');

// State
let availableTools = [];
let chartInstance = null;
let mediaRecorder = null;
let audioChunks = [];

// Initialize the tools functionality
function initTools() {
    // Load available tools
    loadTools();
    
    // Set up event listeners
    setupToolEventListeners();
    
    // Set up multi-modal event listeners
    setupMultiModalEventListeners();
}

// Load available tools from the server
async function loadTools() {
    try {
        const response = await fetch('/api/tools');
        const data = await response.json();
        availableTools = data.tools || [];
        
        // Display tools
        displayTools('all');
    } catch (error) {
        console.error('Error loading tools:', error);
        toolContainer.innerHTML = `<div class="col-span-full p-4 bg-red-100 text-red-700 rounded">
            Error loading tools. Please try again later.
        </div>`;
    }
}

// Display tools filtered by category
function displayTools(category) {
    // Clear the container
    toolContainer.innerHTML = '';
    
    // Filter tools by category if not 'all'
    const filteredTools = category === 'all' 
        ? availableTools 
        : availableTools.filter(tool => tool.category === category);
    
    if (filteredTools.length === 0) {
        toolContainer.innerHTML = `<div class="col-span-full p-4 bg-gray-100 rounded">
            No tools found in this category.
        </div>`;
        return;
    }
    
    // Create a card for each tool
    filteredTools.forEach(tool => {
        const toolCard = document.createElement('div');
        toolCard.className = 'tool-card p-4 border rounded-lg hover:shadow-md transition-shadow';
        toolCard.innerHTML = `
            <h3 class="font-semibold text-lg">${tool.name}</h3>
            <p class="text-gray-600 text-sm mb-2">${tool.description}</p>
            <div class="flex justify-between items-center">
                <span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">${TOOL_CATEGORIES[tool.category] || tool.category}</span>
                <button class="execute-tool-btn bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm" 
                    data-tool-id="${tool.id}">
                    Execute
                </button>
            </div>
            <div class="tool-form mt-3 p-3 bg-gray-50 rounded" id="form-${tool.id}">
                <h4 class="font-medium mb-2">Parameters</h4>
                <form id="params-${tool.id}">
                    ${generateParamInputs(tool.parameters)}
                    <button type="submit" class="mt-2 bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm">
                        Run
                    </button>
                </form>
            </div>
            <div class="tool-result mt-3 p-3 bg-gray-50 rounded hidden" id="result-${tool.id}">
                <h4 class="font-medium mb-2">Result</h4>
                <pre class="text-sm whitespace-pre-wrap bg-white p-2 rounded border"></pre>
            </div>
        `;
        toolContainer.appendChild(toolCard);
        
        // Add event listener to the execute button
        const executeBtn = toolCard.querySelector('.execute-tool-btn');
        executeBtn.addEventListener('click', () => {
            // Toggle the form visibility
            const form = document.getElementById(`form-${tool.id}`);
            form.classList.toggle('active');
        });
        
        // Add event listener to the form
        const form = toolCard.querySelector(`#params-${tool.id}`);
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            executeToolFromForm(tool, form);
        });
    });
}

// Generate HTML for parameter inputs based on tool parameters
function generateParamInputs(parameters) {
    if (!parameters || parameters.length === 0) {
        return '<p class="text-gray-500 italic">No parameters required</p>';
    }
    
    return parameters.map(param => {
        let inputHtml = '';
        
        switch (param.type) {
            case 'string':
                inputHtml = `<input type="text" name="${param.name}" class="w-full border rounded p-2 mb-2" ${param.required ? 'required' : ''} placeholder="${param.description || param.name}">`;
                break;
            case 'number':
                inputHtml = `<input type="number" name="${param.name}" class="w-full border rounded p-2 mb-2" ${param.required ? 'required' : ''} placeholder="${param.description || param.name}">`;
                break;
            case 'boolean':
                inputHtml = `
                    <div class="flex items-center mb-2">
                        <input type="checkbox" id="${param.name}" name="${param.name}" class="mr-2">
                        <label for="${param.name}">${param.description || param.name}</label>
                    </div>
                `;
                break;
            case 'file':
                inputHtml = `
                    <div class="mb-2">
                        <label class="block text-gray-700 mb-1">${param.description || param.name}</label>
                        <input type="file" name="${param.name}" class="w-full" ${param.required ? 'required' : ''}>
                    </div>
                `;
                break;
            case 'select':
                const options = param.options || [];
                inputHtml = `
                    <div class="mb-2">
                        <label class="block text-gray-700 mb-1">${param.description || param.name}</label>
                        <select name="${param.name}" class="w-full border rounded p-2" ${param.required ? 'required' : ''}>
                            ${options.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('')}
                        </select>
                    </div>
                `;
                break;
            case 'textarea':
                inputHtml = `
                    <div class="mb-2">
                        <label class="block text-gray-700 mb-1">${param.description || param.name}</label>
                        <textarea name="${param.name}" class="w-full border rounded p-2" rows="3" ${param.required ? 'required' : ''}
                            placeholder="${param.description || param.name}"></textarea>
                    </div>
                `;
                break;
            default:
                inputHtml = `<input type="text" name="${param.name}" class="w-full border rounded p-2 mb-2" ${param.required ? 'required' : ''} placeholder="${param.description || param.name}">`;
        }
        
        return `
            <div class="mb-3">
                <label class="block text-gray-700 mb-1">${param.description || param.name}${param.required ? ' *' : ''}</label>
                ${inputHtml}
            </div>
        `;
    }).join('');
}

// Execute a tool with parameters from a form
async function executeToolFromForm(tool, form) {
    // Get form data
    const formData = new FormData(form);
    const params = {};
    
    // Convert FormData to object
    for (const [key, value] of formData.entries()) {
        params[key] = value;
    }
    
    // Show loading state
    const resultContainer = document.getElementById(`result-${tool.id}`);
    const resultPre = resultContainer.querySelector('pre');
    resultContainer.classList.remove('hidden');
    resultPre.textContent = 'Executing...';
    
    try {
        // Execute the tool
        const response = await fetch('/api/execute-tool', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tool_id: tool.id,
                parameters: params
            })
        });
        
        const data = await response.json();
        
        // Display the result
        if (data.error) {
            resultPre.textContent = `Error: ${data.error}`;
            resultPre.classList.add('text-red-600');
        } else {
            resultPre.textContent = JSON.stringify(data.result, null, 2);
            resultPre.classList.remove('text-red-600');
        }
    } catch (error) {
        console.error('Error executing tool:', error);
        resultPre.textContent = `Error: ${error.message}`;
        resultPre.classList.add('text-red-600');
    }
}

// Set up event listeners for tools
function setupToolEventListeners() {
    // Filter tools by category
    toolCategorySelector.addEventListener('change', () => {
        const category = toolCategorySelector.value;
        displayTools(category);
    });
}

// Set up event listeners for multi-modal tools
function setupMultiModalEventListeners() {
    // Image Processing
    imageUpload.addEventListener('change', handleImageUpload);
    imageInfoBtn.addEventListener('click', getImageInfo);
    ocrImageBtn.addEventListener('click', extractTextFromImage);
    resizeImageBtn.addEventListener('click', resizeImage);
    
    // Audio Processing
    ttsBtn.addEventListener('click', textToSpeech);
    recordAudioBtn.addEventListener('click', toggleRecording);
    audioUpload.addEventListener('change', handleAudioUpload);
    sttBtn.addEventListener('click', speechToText);
    
    // Chart Generation
    generateChartBtn.addEventListener('click', generateChart);
    
    // Document Processing
    documentUpload.addEventListener('change', handleDocumentUpload);
    extractTextBtn.addEventListener('click', extractTextFromDocument);
    getDocInfoBtn.addEventListener('click', getDocumentInfo);
    
    // Filter multi-modal tools by category
    multimodalCategorySelector.addEventListener('change', filterMultiModalTools);
}

// Handle image upload
function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Display image preview
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImg.src = e.target.result;
        imagePreview.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
}

// Get image information
async function getImageInfo() {
    const file = imageUpload.files[0];
    if (!file) {
        alert('Please upload an image first');
        return;
    }
    
    const formData = new FormData();
    formData.append('image', file);
    
    try {
        const response = await fetch('/api/image-info', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Display the result
        imageResult.classList.remove('hidden');
        imageResult.querySelector('pre').textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        console.error('Error getting image info:', error);
        imageResult.classList.remove('hidden');
        imageResult.querySelector('pre').textContent = `Error: ${error.message}`;
    }
}

// Extract text from image using OCR
async function extractTextFromImage() {
    const file = imageUpload.files[0];
    if (!file) {
        alert('Please upload an image first');
        return;
    }
    
    const formData = new FormData();
    formData.append('image', file);
    
    try {
        const response = await fetch('/api/ocr-image', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Display the result
        imageResult.classList.remove('hidden');
        imageResult.querySelector('pre').textContent = data.text || 'No text found in the image';
    } catch (error) {
        console.error('Error extracting text from image:', error);
        imageResult.classList.remove('hidden');
        imageResult.querySelector('pre').textContent = `Error: ${error.message}`;
    }
}

// Resize image
async function resizeImage() {
    const file = imageUpload.files[0];
    if (!file) {
        alert('Please upload an image first');
        return;
    }
    
    // Prompt for dimensions
    const width = prompt('Enter new width (in pixels):', '300');
    const height = prompt('Enter new height (in pixels):', '200');
    
    if (!width || !height) return;
    
    const formData = new FormData();
    formData.append('image', file);
    formData.append('width', width);
    formData.append('height', height);
    
    try {
        const response = await fetch('/api/resize-image', {
            method: 'POST',
            body: formData
        });
        
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        // Display the resized image
        previewImg.src = url;
        imagePreview.classList.remove('hidden');
        
        // Display success message
        imageResult.classList.remove('hidden');
        imageResult.querySelector('pre').textContent = `Image resized to ${width}x${height} pixels`;
    } catch (error) {
        console.error('Error resizing image:', error);
        imageResult.classList.remove('hidden');
        imageResult.querySelector('pre').textContent = `Error: ${error.message}`;
    }
}

// Convert text to speech
async function textToSpeech() {
    const text = ttsInput.value.trim();
    if (!text) {
        alert('Please enter text to convert to speech');
        return;
    }
    
    try {
        const response = await fetch('/api/text-to-speech', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });
        
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        // Play the audio
        audioElement.src = url;
        audioPlayer.classList.remove('hidden');
        audioElement.play();
    } catch (error) {
        console.error('Error converting text to speech:', error);
        alert(`Error: ${error.message}`);
    }
}

// Toggle audio recording
function toggleRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        // Stop recording
        mediaRecorder.stop();
        recordAudioBtn.textContent = 'Record Audio';
        recordAudioBtn.classList.remove('bg-red-700');
        recordAudioBtn.classList.add('bg-red-600');
    } else {
        // Start recording
        startRecording();
        recordAudioBtn.textContent = 'Stop Recording';
        recordAudioBtn.classList.remove('bg-red-600');
        recordAudioBtn.classList.add('bg-red-700');
    }
}

// Start audio recording
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.addEventListener('dataavailable', event => {
            audioChunks.push(event.data);
        });
        
        mediaRecorder.addEventListener('stop', () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Display the audio player
            audioElement.src = audioUrl;
            audioPlayer.classList.remove('hidden');
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        });
        
        mediaRecorder.start();
    } catch (error) {
        console.error('Error starting recording:', error);
        alert(`Error: ${error.message}`);
    }
}

// Handle audio upload
function handleAudioUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Display audio player
    const audioUrl = URL.createObjectURL(file);
    audioElement.src = audioUrl;
    audioPlayer.classList.remove('hidden');
}

// Convert speech to text
async function speechToText() {
    let audioFile;
    
    // Check if we have a recorded audio or an uploaded file
    if (audioChunks.length > 0) {
        audioFile = new Blob(audioChunks, { type: 'audio/wav' });
    } else if (audioUpload.files.length > 0) {
        audioFile = audioUpload.files[0];
    } else {
        alert('Please record or upload audio first');
        return;
    }
    
    const formData = new FormData();
    formData.append('audio', audioFile);
    
    try {
        const response = await fetch('/api/speech-to-text', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Display the result
        sttResult.classList.remove('hidden');
        sttResult.querySelector('p').textContent = data.text || 'No speech detected';
    } catch (error) {
        console.error('Error converting speech to text:', error);
        sttResult.classList.remove('hidden');
        sttResult.querySelector('p').textContent = `Error: ${error.message}`;
    }
}

// Generate chart
function generateChart() {
    try {
        // Parse chart data
        const chartDataJson = JSON.parse(chartData.value);
        const chartTypeValue = chartType.value;
        
        // Destroy existing chart if any
        if (chartInstance) {
            chartInstance.destroy();
        }
        
        // Create new chart
        const ctx = chartCanvas.getContext('2d');
        chartInstance = new Chart(ctx, {
            type: chartTypeValue,
            data: {
                labels: chartDataJson.labels,
                datasets: [{
                    label: chartDataJson.title || 'Data',
                    data: chartDataJson.values,
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(255, 206, 86, 0.2)',
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(153, 102, 255, 0.2)',
                        'rgba(255, 159, 64, 0.2)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
        
        // Show the chart container
        chartContainer.classList.remove('hidden');
    } catch (error) {
        console.error('Error generating chart:', error);
        alert(`Error: ${error.message}`);
    }
}

// Handle document upload
function handleDocumentUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Display file name
    documentResult.classList.remove('hidden');
    documentResult.querySelector('pre').textContent = `File selected: ${file.name}`;
}

// Extract text from document
async function extractTextFromDocument() {
    const file = documentUpload.files[0];
    if (!file) {
        alert('Please upload a document first');
        return;
    }
    
    const formData = new FormData();
    formData.append('document', file);
    
    try {
        const response = await fetch('/api/extract-text-from-document', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Display the result
        documentResult.classList.remove('hidden');
        documentResult.querySelector('pre').textContent = data.text || 'No text found in the document';
    } catch (error) {
        console.error('Error extracting text from document:', error);
        documentResult.classList.remove('hidden');
        documentResult.querySelector('pre').textContent = `Error: ${error.message}`;
    }
}

// Get document information
async function getDocumentInfo() {
    const file = documentUpload.files[0];
    if (!file) {
        alert('Please upload a document first');
        return;
    }
    
    const formData = new FormData();
    formData.append('document', file);
    
    try {
        const response = await fetch('/api/document-info', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Display the result
        documentResult.classList.remove('hidden');
        documentResult.querySelector('pre').textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        console.error('Error getting document info:', error);
        documentResult.classList.remove('hidden');
        documentResult.querySelector('pre').textContent = `Error: ${error.message}`;
    }
}

// Filter multi-modal tools by category
function filterMultiModalTools() {
    const category = multimodalCategorySelector.value;
    
    // Get all multi-modal tool containers
    const imageProcessing = document.getElementById('image-processing');
    const audioProcessing = document.getElementById('audio-processing');
    const chartGeneration = document.getElementById('chart-generation');
    const documentProcessing = document.getElementById('document-processing');
    
    // Show/hide based on selected category
    if (category === 'all') {
        imageProcessing.style.display = 'block';
        audioProcessing.style.display = 'block';
        chartGeneration.style.display = 'block';
        documentProcessing.style.display = 'block';
    } else {
        imageProcessing.style.display = category === 'image' ? 'block' : 'none';
        audioProcessing.style.display = category === 'audio' ? 'block' : 'none';
        chartGeneration.style.display = category === 'chart' ? 'block' : 'none';
        documentProcessing.style.display = category === 'document' ? 'block' : 'none';
    }
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', initTools);
