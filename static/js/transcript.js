// Speaker labeling functionality
async function loadSpeakersForLabeling() {
    try {
        const response = await fetch('/speakers');
        const data = await response.json();
        
        if (data.speakers && data.speakers.length > 0) {
            // Get example text for each speaker from the first segment
            const resultResponse = await fetch('/result');
            const resultData = await resultResponse.json();
            
            const speakerExamples = {};
            resultData.transcript.forEach(segment => {
                if (!speakerExamples[segment.speaker]) {
                    speakerExamples[segment.speaker] = segment.text;
                }
            });
            
            // Sort speakers numerically (this fixes the order)
            const sortedSpeakers = [...data.speakers].sort((a, b) => {
                // Extract numbers from speaker IDs (handles formats like "0", "1", "speaker_0", etc.)
                const numA = parseInt(a.replace(/^speaker_?/i, ''), 10) || 0;
                const numB = parseInt(b.replace(/^speaker_?/i, ''), 10) || 0;
                return numA - numB;
            });
            
            // Generate HTML for speaker labels
            const speakersList = document.getElementById('speakersList');
            if (speakersList) {
                speakersList.innerHTML = '';
                
                const speakerColors = [
                    '#4361ee', '#3a0ca3', '#7209b7', '#f72585', '#4cc9f0',
                    '#4895ef', '#560bad', '#b5179e', '#f15bb5', '#00b4d8'
                ];
                
                sortedSpeakers.forEach((speaker, index) => {
                    const colorIndex = index % speakerColors.length;
                    const speakerItem = document.createElement('div');
                    speakerItem.className = 'speaker-item';
                    speakerItem.innerHTML = `
                        <div class="speaker-color" style="background-color: ${speakerColors[colorIndex]}"></div>
                        <div class="speaker-label">
                            <input type="text" id="speaker-${speaker}" 
                                  placeholder="Speaker ${speaker}" 
                                  value="Speaker ${speaker}">
                            <div class="speaker-example">"${truncateText(speakerExamples[speaker] || '', 100)}"</div>
                        </div>
                    `;
                    speakersList.appendChild(speakerItem);
                });
                
                // Show the speaker labeling container
                const speakerLabelingContainer = document.getElementById('speakerLabelingContainer');
                if (speakerLabelingContainer) {
                    speakerLabelingContainer.style.display = 'flex';
                }
            }
        }
    } catch (error) {
        console.error('Error loading speakers:', error);
    }
}

async function processTranscriptWithLabels() {
    // Get the process button and disable it
    const processBtn = document.getElementById('processSpeakersBtn');
    if (processBtn) {
        processBtn.disabled = true;
        processBtn.innerHTML = '<div class="spinner"></div> <span>Processing...</span>';
    }
    
    // Hide speaker labeling and show processing container
    const speakerLabelingContainer = document.getElementById('speakerLabelingContainer');
    const speakerProcessingContainer = document.getElementById('speakerProcessingContainer');
    
    if (speakerLabelingContainer) {
        speakerLabelingContainer.style.display = 'none';
    }
    
    if (speakerProcessingContainer) {
        speakerProcessingContainer.style.display = 'flex';
    }
    
    // Set initial processing status
    const processingProgressBar = document.getElementById('processingProgressBar');
    if (processingProgressBar) {
        processingProgressBar.style.width = '10%';
    }
    
    const processingStatusText = document.getElementById('processingStatusText');
    if (processingStatusText) {
        processingStatusText.textContent = 'Collecting speaker labels...';
    }
    
    try {
        // Collect speaker labels - Force fresh collection by querying the DOM directly
        const speakerLabels = {};
        const speakerInputs = document.querySelectorAll('[id^="speaker-"]');
        
        // Add debug logging to see what's being collected
        console.log('Found ' + speakerInputs.length + ' speaker input fields');
        
        speakerInputs.forEach(input => {
            const speakerId = input.id.replace('speaker-', '');
            const labelValue = input.value || `Speaker ${speakerId}`;
            speakerLabels[speakerId] = labelValue;
            
            // Log each speaker and its label for debugging
            console.log(`Speaker ${speakerId} labeled as: ${labelValue}`);
        });
        
        // Log the entire speaker labels object
        console.log('Speaker labels being sent to server:', speakerLabels);
        
        // Update processing status
        if (processingStatusText) {
            processingStatusText.textContent = 'Sending labels to server...';
        }
        
        // Send to server for processing - Add a timestamp to prevent caching
        const response = await fetch('/process-transcript?t=' + new Date().getTime(), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            },
            body: JSON.stringify({ speaker_labels: speakerLabels }),
        });
        
        if (!response.ok) {
            throw new Error('Failed to process transcript: ' + response.statusText);
        }
        
        // Update status
        if (processingStatusText) {
            processingStatusText.textContent = 'Processing transcript...';
        }
        
        // Start polling for final transcript
        pollProcessingProgress();
        
    } catch (error) {
        console.error('Error processing transcript:', error);
        
        const processingStatusText = document.getElementById('processingStatusText');
        if (processingStatusText) {
            processingStatusText.textContent = 'Error: ' + error.message;
        }
        
        // Reset button
        if (processBtn) {
            processBtn.disabled = false;
            processBtn.innerHTML = '<span>Process Final Transcript</span>';
        }
        
        // Switch back to labeling view
        if (speakerProcessingContainer) {
            speakerProcessingContainer.style.display = 'none';
        }
        
        if (speakerLabelingContainer) {
            speakerLabelingContainer.style.display = 'flex';
        }
    }
} 