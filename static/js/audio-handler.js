// Audio file upload handling
function initializeDropzone() {
    const dropZone = document.querySelector('.file-upload');
    if (!dropZone) return;
    
    // Add drag & drop event listeners
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    // Add highlight/unhighlight event listeners
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    // Add drop handler
    dropZone.addEventListener('drop', handleDrop, false);
    
    // Display file name when selected via button
    const fileInput = document.getElementById('audioFile');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = this.files.length ? this.files[0].name : '';
            const fileNameDisplay = document.getElementById('fileName');
            if (fileNameDisplay) {
                fileNameDisplay.textContent = fileName;
            }
        });
    }
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight() {
    this.style.borderColor = 'var(--primary)';
    this.style.backgroundColor = 'rgba(67, 97, 238, 0.05)';
}

function unhighlight() {
    this.style.borderColor = '#ddd';
    this.style.backgroundColor = 'var(--gray)';
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length) {
        const fileInput = document.getElementById('audioFile');
        fileInput.files = files;
        
        // Update file name display
        const fileNameDisplay = document.getElementById('fileName');
        if (fileNameDisplay) {
            fileNameDisplay.textContent = files[0].name;
        }
        
        // Enable transcribe button if we have an API key
        const apiKey = document.getElementById('apiKeyInput').value;
        const uploadBtn = document.getElementById('uploadBtn');
        if (uploadBtn) {
            uploadBtn.disabled = !apiKey;
        }
    }
}

async function transcribeAudio() {
    const fileInput = document.getElementById('audioFile');
    const apiKey = document.getElementById('apiKeyInput').value;
    const enableDiarization = document.getElementById('diarizationToggle').checked;
    const numSpeakers = document.getElementById('numSpeakers').value;
    const modelId = 'scribe_v1'; // Hardcoded since there's only one option
    
    if (!fileInput.files.length) {
        alert('Please select an audio file.');
        return;
    }
    
    if (!apiKey) {
        alert('Please enter your ElevenLabs API key.');
        return;
    }
    
    // Reset the UI
    resetUI();
    
    // Show loading state
    const uploadBtn = document.getElementById('uploadBtn');
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<div class="spinner"></div> <span>Processing...</span>';
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('audio', file);
    formData.append('api_key', apiKey);
    formData.append('enable_diarization', enableDiarization.toString());
    if (numSpeakers && enableDiarization) {
        formData.append('num_speakers', numSpeakers);
    }
    formData.append('model_id', modelId);
    
    // Show progress container
    const progressContainer = document.getElementById('progressContainer');
    if (progressContainer) {
        progressContainer.style.display = 'block';
    }
    
    try {
        const response = await fetch('/transcribe', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Transcription failed');
        }
        
        // Start polling for progress
        pollProgress();
        
    } catch (error) {
        const statusText = document.getElementById('statusText');
        if (statusText) {
            statusText.textContent = 'Error: ' + error.message;
        }
        
        // Reset button
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<span>Transcribe</span>';
    }
} 