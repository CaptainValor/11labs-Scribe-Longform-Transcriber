document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI components
    initializeToggles();
    initializeDropzone();
    initializeButtons();
    
    // Initialize form validation
    validateForm();
    
    // Reset UI to ensure correct initial state
    resetUI();
});

function initializeToggles() {
    // Toggle collapsible sections
    document.querySelectorAll('.section-title').forEach(title => {
        title.addEventListener('click', () => {
            const parent = title.parentElement;
            parent.classList.toggle('section-expanded');
        });
    });
    
    // Settings section should be collapsed by default
    // (Don't add the section-expanded class as we did before)
    
    // Diarization toggle
    const diarizationToggle = document.getElementById('diarizationToggle');
    if (diarizationToggle) {
        diarizationToggle.addEventListener('change', function() {
            const speakerCountGroup = document.getElementById('speakerCountGroup');
            speakerCountGroup.style.display = this.checked ? 'block' : 'none';
        });
    }
}

function validateForm() {
    // Enable/disable transcribe button based on file and API key
    const audioFileInput = document.getElementById('audioFile');
    const apiKeyInput = document.getElementById('apiKeyInput');
    const uploadBtn = document.getElementById('uploadBtn');
    
    const checkUploadButton = () => {
        const hasFile = audioFileInput.files.length > 0;
        const hasApiKey = apiKeyInput.value.trim() !== '';
        uploadBtn.disabled = !(hasFile && hasApiKey);
    };
    
    if (audioFileInput && apiKeyInput) {
        audioFileInput.addEventListener('change', checkUploadButton);
        apiKeyInput.addEventListener('input', checkUploadButton);
        
        // Also check when settings are expanded/collapsed
        const settingsTitle = document.querySelector('.section-title');
        if (settingsTitle) {
            settingsTitle.addEventListener('click', () => {
                // Give a slight delay to ensure the input is visible
                setTimeout(checkUploadButton, 100);
            });
        }
    }
}

function resetUI() {
    // Hide containers that should be initially hidden
    const containerIdsToHide = [
        'speakerLabelingContainer', 
        'speakerProcessingContainer', 
        'resultContainer'
    ];
    
    containerIdsToHide.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.style.display = 'none';
        }
    });
    
    // Reset the title of the transcript container
    const titleElement = document.querySelector('#resultContainer .stage-title');
    if (titleElement) {
        titleElement.textContent = 'Initial Transcription';
    }
    
    // Show placeholders
    const placeholderIdsToShow = [
        'placeholderLabelingContainer',
        'placeholderResultContainer'
    ];
    
    placeholderIdsToShow.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.style.display = 'block';
        }
    });
    
    // Reset progress
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        progressBar.style.width = '0%';
    }
    
    const statusText = document.getElementById('statusText');
    if (statusText) {
        statusText.textContent = 'Initializing...';
    }
    
    // Hide progress container
    const progressContainer = document.getElementById('progressContainer');
    if (progressContainer) {
        progressContainer.style.display = 'none';
    }
    
    // Reset process button text
    const processSpeakersBtn = document.getElementById('processSpeakersBtn');
    if (processSpeakersBtn) {
        processSpeakersBtn.innerHTML = '<span>Process Transcript</span>';
    }
    
    // Also make sure the speaker count group is shown/hidden properly based on toggle
    const diarizationToggle = document.getElementById('diarizationToggle');
    const speakerCountGroup = document.getElementById('speakerCountGroup');
    if (diarizationToggle && speakerCountGroup) {
        speakerCountGroup.style.display = diarizationToggle.checked ? 'block' : 'none';
    }
}

function formatTranscript(transcript) {
    let html = '';
    let currentSpeaker = '';
    
    if (!transcript || transcript.length === 0) {
        return '<p>No transcript data found.</p>';
    }
    
    transcript.forEach(segment => {
        // Format the speaker label to ensure it's always "Speaker X"
        let speakerLabel = segment.speaker;
        
        // If the speaker is just a number or "speakerX", format it as "Speaker X"
        if (/^[0-9]+$/.test(speakerLabel) || /^speaker_?[0-9]+$/i.test(speakerLabel)) {
            // Extract just the number part
            const speakerNum = speakerLabel.replace(/^speaker_?/i, '');
            speakerLabel = `Speaker ${speakerNum}`;
        }
        
        if (speakerLabel !== currentSpeaker) {
            currentSpeaker = speakerLabel;
            html += `<div class="speaker">${speakerLabel}</div>`;
        }
        html += `<div class="transcript-text">${segment.text}</div>`;
    });
    
    return html;
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
} 