/**
 * Multi-Modal functionality for MultiAgentConsole Web UI
 */

// DOM Elements
const multimodalPanel = document.getElementById('multimodal-panel');
const categorySelector = document.getElementById('multimodal-category-selector');
const multimodalContent = document.getElementById('multimodal-content');

// Initialize multi-modal functionality
function initMultiModal() {
    // Set up event listeners
    setupMultiModalEventListeners();

    // Load initial content
    loadMultiModalTools();

    console.log('Multi-Modal functionality initialized');
}

// Set up event listeners for multi-modal functionality
function setupMultiModalEventListeners() {
    // Category selector change
    if (categorySelector) {
        categorySelector.addEventListener('change', () => {
            loadMultiModalTools(categorySelector.value);
        });
    }
}

// Load multi-modal tools based on category
function loadMultiModalTools(category = 'all') {
    if (!multimodalContent) return;

    // Show loading indicator
    multimodalContent.innerHTML = '<p class="text-center py-4">Loading multi-modal tools...</p>';

    // Create the basic tool cards
    const tools = getMultiModalTools(category);

    // Display the tools
    displayMultiModalTools(tools);
}

// Get multi-modal tools based on category
function getMultiModalTools(category) {
    // Basic tool definitions
    const allTools = [
        {
            id: 'image-upload',
            name: 'Image Upload & Analysis',
            description: 'Upload and analyze images',
            category: 'image',
            icon: '📷'
        },
        {
            id: 'ocr',
            name: 'OCR (Text Extraction)',
            description: 'Extract text from images',
            category: 'image',
            icon: '🔍'
        },
        {
            id: 'text-to-speech',
            name: 'Text to Speech',
            description: 'Convert text to spoken audio',
            category: 'audio',
            icon: '🔊'
        },
        {
            id: 'speech-to-text',
            name: 'Speech to Text',
            description: 'Convert spoken audio to text',
            category: 'audio',
            icon: '🎤'
        },
        {
            id: 'chart-generator',
            name: 'Chart Generator',
            description: 'Create charts and visualizations',
            category: 'chart',
            icon: '📊'
        },
        {
            id: 'document-processor',
            name: 'Document Processor',
            description: 'Extract text and information from documents',
            category: 'document',
            icon: '📄'
        }
    ];

    // Filter tools by category
    if (category !== 'all') {
        return allTools.filter(tool => tool.category === category);
    }

    return allTools;
}

// Display multi-modal tools
function displayMultiModalTools(tools) {
    if (!multimodalContent) return;

    if (tools.length === 0) {
        multimodalContent.innerHTML = '<p class="text-center py-4">No tools available for this category.</p>';
        return;
    }

    let html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">';

    tools.forEach(tool => {
        html += `
            <div class="tool-card bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow" data-tool-id="${tool.id}" data-category="${tool.category}">
                <div class="flex items-center mb-2">
                    <div class="text-2xl mr-2">${tool.icon}</div>
                    <h3 class="text-lg font-semibold">${tool.name}</h3>
                </div>
                <p class="text-gray-600 mb-3">${tool.description}</p>
                <button class="use-tool-btn bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm" data-tool-id="${tool.id}">
                    Use Tool
                </button>
            </div>
        `;
    });

    html += '</div>';
    multimodalContent.innerHTML = html;

    // Add event listeners to the tool buttons
    document.querySelectorAll('.use-tool-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const toolId = e.target.getAttribute('data-tool-id');
            showToolInterface(toolId);
        });
    });
}

// Show the interface for a specific tool
function showToolInterface(toolId) {
    if (!multimodalContent) return;

    // Basic tool interfaces
    let html = '';

    switch (toolId) {
        case 'image-upload':
            html = `
                <div class="tool-interface p-4 bg-white rounded-lg shadow">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold">Image Upload & Analysis</h3>
                        <button class="back-btn text-blue-500 hover:text-blue-700">← Back to Tools</button>
                    </div>
                    <div class="mb-4">
                        <label class="block text-gray-700 mb-2">Upload an image for analysis:</label>
                        <input type="file" id="image-file" accept="image/*" class="border border-gray-300 p-2 w-full rounded">
                    </div>
                    <button id="analyze-image-btn" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
                        Analyze Image
                    </button>
                    <div id="image-preview" class="mt-4 hidden">
                        <h4 class="font-medium mb-2">Preview:</h4>
                        <img id="preview-img" class="max-w-full h-auto max-h-64 rounded border border-gray-300" src="" alt="Preview">
                    </div>
                    <div id="image-result" class="mt-4 hidden">
                        <h4 class="font-medium mb-2">Analysis Result:</h4>
                        <div id="image-result-content" class="p-3 bg-gray-100 rounded"></div>
                    </div>
                </div>
            `;
            break;

        case 'ocr':
            html = `
                <div class="tool-interface p-4 bg-white rounded-lg shadow">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold">OCR (Text Extraction)</h3>
                        <button class="back-btn text-blue-500 hover:text-blue-700">← Back to Tools</button>
                    </div>
                    <div class="mb-4">
                        <label class="block text-gray-700 mb-2">Upload an image to extract text:</label>
                        <input type="file" id="ocr-file" accept="image/*" class="border border-gray-300 p-2 w-full rounded">
                    </div>
                    <button id="extract-text-btn" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
                        Extract Text
                    </button>
                    <div id="ocr-preview" class="mt-4 hidden">
                        <h4 class="font-medium mb-2">Preview:</h4>
                        <img id="ocr-preview-img" class="max-w-full h-auto max-h-64 rounded border border-gray-300" src="" alt="Preview">
                    </div>
                    <div id="ocr-result" class="mt-4 hidden">
                        <h4 class="font-medium mb-2">Extracted Text:</h4>
                        <div id="ocr-result-content" class="p-3 bg-gray-100 rounded whitespace-pre-wrap"></div>
                    </div>
                </div>
            `;
            break;

                case 'text-to-speech':
            html = `
                <div class="tool-interface p-4 bg-white rounded-lg shadow">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold">Text to Speech</h3>
                        <button class="back-btn text-blue-500 hover:text-blue-700">← Back to Tools</button>
                    </div>
                    <div class="mb-4">
                        <label class="block text-gray-700 mb-2">Enter text to convert to speech:</label>
                        <textarea id="tts-text" class="border border-gray-300 p-2 w-full rounded" rows="4" placeholder="Enter text here..."></textarea>
                    </div>
                    <div class="mb-4">
                        <label class="block text-gray-700 mb-2">Voice Options:</label>
                        <select id="tts-voice" class="border border-gray-300 p-2 w-full rounded">
                            <option value="default">Default Voice</option>
                            <option value="male">Male Voice</option>
                            <option value="female">Female Voice</option>
                        </select>
                    </div>
                    <button id="convert-tts-btn" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
                        Convert to Speech
                    </button>
                    <div id="tts-result" class="mt-4 hidden">
                        <h4 class="font-medium mb-2">Audio Result:</h4>
                        <audio id="tts-audio" controls class="w-full"></audio>
                    </div>
                </div>
            `;
            break;

        case 'speech-to-text':
            html = `
                <div class="tool-interface p-4 bg-white rounded-lg shadow">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold">Speech to Text</h3>
                        <button class="back-btn text-blue-500 hover:text-blue-700">← Back to Tools</button>
                    </div>
                    <div class="mb-4">
                        <label class="block text-gray-700 mb-2">Upload an audio file or record audio:</label>
                        <div class="flex flex-col space-y-2">
                            <input type="file" id="stt-file" accept="audio/*" class="border border-gray-300 p-2 w-full rounded">
                            <button id="record-audio-btn" class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded">
                                Record Audio (5s)
                            </button>
                        </div>
                    </div>
                    <div id="recording-status" class="mb-4 hidden">
                        <p class="text-red-500 font-medium">Recording... <span id="recording-timer">5</span>s</p>
                    </div>
                    <div id="audio-preview" class="mb-4 hidden">
                        <h4 class="font-medium mb-2">Audio Preview:</h4>
                        <audio id="audio-player" controls class="w-full"></audio>
                    </div>
                    <button id="convert-stt-btn" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
                        Convert to Text
                    </button>
                    <div id="stt-result" class="mt-4 hidden">
                        <h4 class="font-medium mb-2">Transcription Result:</h4>
                        <div id="stt-result-content" class="p-3 bg-gray-100 rounded whitespace-pre-wrap"></div>
                    </div>
                </div>
            `;
            break;

        // Add more tool interfaces as needed

        default:
            html = `
                <div class="p-4 bg-white rounded-lg shadow">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold">Tool Interface</h3>
                        <button class="back-btn text-blue-500 hover:text-blue-700">← Back to Tools</button>
                    </div>
                    <p>Interface for ${toolId} is under development.</p>
                </div>
            `;
    }

    multimodalContent.innerHTML = html;

    // Add event listeners for the back button
    document.querySelectorAll('.back-btn').forEach(button => {
        button.addEventListener('click', () => {
            loadMultiModalTools(categorySelector ? categorySelector.value : 'all');
        });
    });

    // Add tool-specific event listeners
    setupToolEventListeners(toolId);
}

// Set up event listeners for specific tools
function setupToolEventListeners(toolId) {
    switch (toolId) {
        case 'image-upload':
            const imageFileInput = document.getElementById('image-file');
            const analyzeImageBtn = document.getElementById('analyze-image-btn');
            const imagePreview = document.getElementById('image-preview');
            const previewImg = document.getElementById('preview-img');

            if (imageFileInput) {
                imageFileInput.addEventListener('change', (e) => {
                    if (e.target.files && e.target.files[0]) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            previewImg.src = e.target.result;
                            imagePreview.classList.remove('hidden');
                        };
                        reader.readAsDataURL(e.target.files[0]);
                    }
                });
            }

            if (analyzeImageBtn) {
                analyzeImageBtn.addEventListener('click', () => {
                    analyzeImage();
                });
            }
            break;

        case 'ocr':
            const ocrFileInput = document.getElementById('ocr-file');
            const extractTextBtn = document.getElementById('extract-text-btn');
            const ocrPreview = document.getElementById('ocr-preview');
            const ocrPreviewImg = document.getElementById('ocr-preview-img');

            if (ocrFileInput) {
                ocrFileInput.addEventListener('change', (e) => {
                    if (e.target.files && e.target.files[0]) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            ocrPreviewImg.src = e.target.result;
                            ocrPreview.classList.remove('hidden');
                        };
                        reader.readAsDataURL(e.target.files[0]);
                    }
                });
            }

            if (extractTextBtn) {
                extractTextBtn.addEventListener('click', () => {
                    extractTextFromImage();
                });
            }
            break;

        case 'text-to-speech':
            const ttsText = document.getElementById('tts-text');
            const ttsVoice = document.getElementById('tts-voice');
            const convertTtsBtn = document.getElementById('convert-tts-btn');
            const ttsResult = document.getElementById('tts-result');
            const ttsAudio = document.getElementById('tts-audio');

            if (convertTtsBtn) {
                convertTtsBtn.addEventListener('click', () => {
                    if (!ttsText || !ttsText.value.trim()) {
                        alert('Please enter some text to convert.');
                        return;
                    }

                    // Show loading state
                    convertTtsBtn.textContent = 'Converting...';
                    convertTtsBtn.disabled = true;

                    // Call the text-to-speech API
                    convertTextToSpeech(ttsText.value, ttsVoice.value);
                });
            }
            break;

        case 'speech-to-text':
            const sttFile = document.getElementById('stt-file');
            const recordAudioBtn = document.getElementById('record-audio-btn');
            const audioPreview = document.getElementById('audio-preview');
            const audioPlayer = document.getElementById('audio-player');
            const convertSttBtn = document.getElementById('convert-stt-btn');
            const recordingStatus = document.getElementById('recording-status');
            const recordingTimer = document.getElementById('recording-timer');

            // Audio file upload
            if (sttFile) {
                sttFile.addEventListener('change', (e) => {
                    if (e.target.files && e.target.files[0]) {
                        const file = e.target.files[0];
                        const url = URL.createObjectURL(file);
                        audioPlayer.src = url;
                        audioPreview.classList.remove('hidden');
                    }
                });
            }

            // Record audio button
            if (recordAudioBtn) {
                recordAudioBtn.addEventListener('click', () => {
                    // Check if browser supports audio recording
                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                        alert('Your browser does not support audio recording. Please upload an audio file instead.');
                        return;
                    }

                    // Start recording
                    startAudioRecording();
                });
            }

            // Convert to text button
            if (convertSttBtn) {
                convertSttBtn.addEventListener('click', () => {
                    if (!audioPlayer.src) {
                        alert('Please upload or record audio first.');
                        return;
                    }

                    // Show loading state
                    convertSttBtn.textContent = 'Converting...';
                    convertSttBtn.disabled = true;

                    // Call the speech-to-text API
                    convertSpeechToText();
                });
            }
            break;

        // Add more tool-specific event listeners as needed
    }
}

// Analyze an image
function analyzeImage() {
    const imageFileInput = document.getElementById('image-file');
    const imageResult = document.getElementById('image-result');
    const imageResultContent = document.getElementById('image-result-content');

    if (!imageFileInput || !imageFileInput.files || imageFileInput.files.length === 0) {
        alert('Please select an image first.');
        return;
    }

    const file = imageFileInput.files[0];
    const formData = new FormData();
    formData.append('image', file);

    // Show loading state
    imageResultContent.innerHTML = '<p class="text-center">Analyzing image...</p>';
    imageResult.classList.remove('hidden');

    // Send the image for analysis
    fetch('/api/image-info', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            imageResultContent.innerHTML = `<p class="text-red-500">${data.error}</p>`;
            return;
        }

        // Display the analysis result
        let html = '<div class="grid grid-cols-2 gap-2">';
        html += `<div><strong>Format:</strong></div><div>${data.format || 'Unknown'}</div>`;
        html += `<div><strong>Size:</strong></div><div>${data.width || 0} x ${data.height || 0} pixels</div>`;
        html += `<div><strong>Mode:</strong></div><div>${data.mode || 'Unknown'}</div>`;
        html += `<div><strong>File Size:</strong></div><div>${formatFileSize(data.file_size || 0)}</div>`;
        html += '</div>';

        imageResultContent.innerHTML = html;
    })
    .catch(error => {
        console.error('Error analyzing image:', error);
        imageResultContent.innerHTML = `<p class="text-red-500">Error analyzing image: ${error.message}</p>`;
    });
}

// Extract text from an image
function extractTextFromImage() {
    const ocrFileInput = document.getElementById('ocr-file');
    const ocrResult = document.getElementById('ocr-result');
    const ocrResultContent = document.getElementById('ocr-result-content');

    if (!ocrFileInput || !ocrFileInput.files || ocrFileInput.files.length === 0) {
        alert('Please select an image first.');
        return;
    }

    const file = ocrFileInput.files[0];
    const formData = new FormData();
    formData.append('image', file);

    // Show loading state
    ocrResultContent.innerHTML = '<p class="text-center">Extracting text...</p>';
    ocrResult.classList.remove('hidden');

    // Send the image for OCR
    fetch('/api/ocr-image', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            ocrResultContent.innerHTML = `<p class="text-red-500">${data.error}</p>`;
            return;
        }

        // Display the extracted text
        ocrResultContent.textContent = data.text || 'No text found in the image.';
    })
    .catch(error => {
        console.error('Error extracting text:', error);
        ocrResultContent.innerHTML = `<p class="text-red-500">Error extracting text: ${error.message}</p>`;
    });
}

// Convert text to speech
function convertTextToSpeech(text, voice) {
    const ttsResult = document.getElementById('tts-result');
    const ttsAudio = document.getElementById('tts-audio');
    const convertTtsBtn = document.getElementById('convert-tts-btn');

    // Prepare request data
    const requestData = {
        text: text,
        voice: voice
    };

    // Call the API
    fetch('/api/text-to-speech', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.blob();
    })
    .then(blob => {
        // Create a URL for the audio blob
        const url = URL.createObjectURL(blob);

        // Set the audio source
        ttsAudio.src = url;

        // Show the result
        ttsResult.classList.remove('hidden');

        // Reset button state
        convertTtsBtn.textContent = 'Convert to Speech';
        convertTtsBtn.disabled = false;

        // Add to chat as a message
        if (typeof addAudioMessage === 'function') {
            addAudioMessage(url, `Text to speech: "${text.substring(0, 30)}${text.length > 30 ? '...' : ''}"`);
        }
    })
    .catch(error => {
        console.error('Error converting text to speech:', error);
        alert('Error converting text to speech: ' + error.message);

        // Reset button state
        convertTtsBtn.textContent = 'Convert to Speech';
        convertTtsBtn.disabled = false;
    });
}

// Media recorder for audio recording
let mediaRecorder = null;
let audioChunks = [];

// Start audio recording
function startAudioRecording() {
    const recordingStatus = document.getElementById('recording-status');
    const recordingTimer = document.getElementById('recording-timer');
    const recordAudioBtn = document.getElementById('record-audio-btn');
    const audioPreview = document.getElementById('audio-preview');
    const audioPlayer = document.getElementById('audio-player');

    // Request microphone access
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            // Show recording status
            recordingStatus.classList.remove('hidden');
            recordAudioBtn.disabled = true;

            // Create media recorder
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            // Handle data available event
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            // Handle recording stop event
            mediaRecorder.onstop = () => {
                // Create audio blob
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const audioUrl = URL.createObjectURL(audioBlob);

                // Set audio player source
                audioPlayer.src = audioUrl;
                audioPreview.classList.remove('hidden');

                // Hide recording status
                recordingStatus.classList.add('hidden');
                recordAudioBtn.disabled = false;

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };

            // Start recording
            mediaRecorder.start();

            // Set up timer
            let seconds = 5;
            recordingTimer.textContent = seconds;

            const timerInterval = setInterval(() => {
                seconds--;
                recordingTimer.textContent = seconds;

                if (seconds <= 0) {
                    clearInterval(timerInterval);
                    mediaRecorder.stop();
                }
            }, 1000);

            // Stop recording after 5 seconds
            setTimeout(() => {
                if (mediaRecorder && mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                    clearInterval(timerInterval);
                }
            }, 5000);
        })
        .catch(error => {
            console.error('Error accessing microphone:', error);
            alert('Error accessing microphone: ' + error.message);
            recordAudioBtn.disabled = false;
        });
}

// Convert speech to text
function convertSpeechToText() {
    const sttFile = document.getElementById('stt-file');
    const sttResult = document.getElementById('stt-result');
    const sttResultContent = document.getElementById('stt-result-content');
    const convertSttBtn = document.getElementById('convert-stt-btn');
    const audioPlayer = document.getElementById('audio-player');

    // Check if we have an audio file
    if (!sttFile.files || sttFile.files.length === 0) {
        // If we don't have a file, we might be using recorded audio
        if (!audioChunks.length) {
            alert('Please upload or record audio first.');
            convertSttBtn.textContent = 'Convert to Text';
            convertSttBtn.disabled = false;
            return;
        }

        // Create a FormData object
        const formData = new FormData();
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        formData.append('audio', audioBlob, 'recording.wav');

        // Send the recorded audio
        fetch('/api/speech-to-text', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            // Display the result
            sttResultContent.textContent = data.text || 'No text was recognized.';
            sttResult.classList.remove('hidden');

            // Reset button state
            convertSttBtn.textContent = 'Convert to Text';
            convertSttBtn.disabled = false;

            // Add to chat as a message
            if (typeof addSystemMessage === 'function') {
                addSystemMessage(`Speech to text result: "${data.text}"`);
            }
        })
        .catch(error => {
            console.error('Error converting speech to text:', error);
            sttResultContent.textContent = 'Error: ' + error.message;
            sttResult.classList.remove('hidden');

            // Reset button state
            convertSttBtn.textContent = 'Convert to Text';
            convertSttBtn.disabled = false;
        });
    } else {
        // We have a file upload
        const file = sttFile.files[0];
        const formData = new FormData();
        formData.append('audio', file);

        // Send the file
        fetch('/api/speech-to-text', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            // Display the result
            sttResultContent.textContent = data.text || 'No text was recognized.';
            sttResult.classList.remove('hidden');

            // Reset button state
            convertSttBtn.textContent = 'Convert to Text';
            convertSttBtn.disabled = false;

            // Add to chat as a message
            if (typeof addSystemMessage === 'function') {
                addSystemMessage(`Speech to text result: "${data.text}"`);
            }
        })
        .catch(error => {
            console.error('Error converting speech to text:', error);
            sttResultContent.textContent = 'Error: ' + error.message;
            sttResult.classList.remove('hidden');

            // Reset button state
            convertSttBtn.textContent = 'Convert to Text';
            convertSttBtn.disabled = false;
        });
    }
}

// Format file size in a human-readable format
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Export functions for use in other modules
window.initMultiModal = initMultiModal;
