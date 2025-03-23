// Initialize buttons and their event handlers
function initializeButtons() {
    // Transcribe button
    const uploadBtn = document.getElementById('uploadBtn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', transcribeAudio);
    }
    
    // Process speakers button
    const processSpeakersBtn = document.getElementById('processSpeakersBtn');
    if (processSpeakersBtn) {
        processSpeakersBtn.addEventListener('click', processTranscriptWithLabels);
    }
    
    // Copy and download buttons
    const copyBtn = document.getElementById('copyBtn');
    if (copyBtn) {
        copyBtn.addEventListener('click', copyTranscript);
    }
    
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadTranscript);
    }
}

async function pollProgress() {
    try {
        const response = await fetch('/progress');
        const data = await response.json();
        
        // Update progress bar
        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            progressBar.style.width = data.progress + '%';
        }
        
        // Update status
        const statusText = document.getElementById('statusText');
        if (statusText) {
            statusText.textContent = data.status || 'Processing...';
        }
        
        // Show result container as soon as transcription starts
        if (data.progress > 0 && data.transcript && data.transcript.length > 0) {
            const placeholderResult = document.getElementById('placeholderResultContainer');
            const resultContainer = document.getElementById('resultContainer');
            
            if (placeholderResult) {
                placeholderResult.style.display = 'none';
            }
            
            if (resultContainer) {
                resultContainer.style.display = 'flex';
                const resultDiv = document.getElementById('result');
                if (resultDiv) {
                    resultDiv.innerHTML = formatTranscript(data.transcript);
                    
                    // Remove auto-scrolling behavior
                    // resultDiv.scrollTop = resultDiv.scrollHeight;
                }
            }
        }
        
        if (data.complete) {
            // Show speaker labeling container and hide placeholder
            const placeholderLabeling = document.getElementById('placeholderLabelingContainer');
            if (placeholderLabeling) {
                placeholderLabeling.style.display = 'none';
            }
            
            // Get the final transcription result of first segment
            const resultResponse = await fetch('/result');
            const resultData = await resultResponse.json();
            
            // Display the final result
            const resultDiv = document.getElementById('result');
            if (resultDiv) {
                resultDiv.innerHTML = formatTranscript(resultData.transcript);
            }
            
            // Reset the transcribe button
            const uploadBtn = document.getElementById('uploadBtn');
            if (uploadBtn) {
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = '<span>Transcribe</span>';
            }
            
            // Load speakers for labeling
            await loadSpeakersForLabeling();
        } else {
            // Continue polling
            setTimeout(pollProgress, 2000);
        }
    } catch (error) {
        console.error('Error polling progress:', error);
        
        const statusText = document.getElementById('statusText');
        if (statusText) {
            statusText.textContent = 'Error checking progress: ' + error.message;
        }
        
        // Reset the transcribe button
        const uploadBtn = document.getElementById('uploadBtn');
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<span>Transcribe</span>';
        }
    }
}

let processingInterval;
let processingProgress = 10;

async function pollProcessingProgress() {
    try {
        // Simulate progress updates while processing
        processingInterval = setInterval(() => {
            if (processingProgress < 90) {
                processingProgress += 5;
                
                const processingProgressBar = document.getElementById('processingProgressBar');
                if (processingProgressBar) {
                    processingProgressBar.style.width = processingProgress + '%';
                    
                    // Update status text at certain points
                    const processingStatusText = document.getElementById('processingStatusText');
                    if (processingStatusText) {
                        if (processingProgress === 30) {
                            processingStatusText.textContent = 'Analyzing segment overlaps...';
                        } else if (processingProgress === 50) {
                            processingStatusText.textContent = 'Mapping speaker identities...';
                        } else if (processingProgress === 70) {
                            processingStatusText.textContent = 'Applying speaker labels...';
                        }
                    }
                }
            }
        }, 500);
        
        // Monitor actual status from server
        const checkServerStatus = async () => {
            try {
                const response = await fetch('/processing-progress');
                const data = await response.json();
                
                // If we have actual progress data, use it
                if (data.progress > 0) {
                    processingProgress = data.progress;
                    
                    const processingProgressBar = document.getElementById('processingProgressBar');
                    if (processingProgressBar) {
                        processingProgressBar.style.width = processingProgress + '%';
                    }
                    
                    const processingStatusText = document.getElementById('processingStatusText');
                    if (processingStatusText && data.status) {
                        processingStatusText.textContent = data.status;
                    }
                }
                
                if (data.complete) {
                    await finalizeProcessing();
                    return true;
                }
                
                return false;
            } catch (error) {
                console.error('Error checking processing progress:', error);
                return false;
            }
        };
        
        // Check for final transcript
        const checkFinalTranscript = async () => {
            try {
                // Add a cache-busting parameter to the URL
                const finalResponse = await fetch('/final-transcript?t=' + new Date().getTime(), {
                    headers: {
                        'Cache-Control': 'no-cache'
                    }
                });
                
                const finalData = await finalResponse.json();
                
                if (finalData.transcript && finalData.transcript.length > 0) {
                    // Log the received transcript for debugging
                    console.log('Received final transcript:', finalData.transcript);
                    
                    await finalizeProcessing(finalData);
                    return true;
                }
                return false;
            } catch (error) {
                console.error('Error checking final transcript:', error);
                return false;
            }
        };
        
        // Finalize processing and update UI
        const finalizeProcessing = async (finalData) => {
            // Clear the interval
            clearInterval(processingInterval);
            
            // Set progress to 100%
            const processingProgressBar = document.getElementById('processingProgressBar');
            if (processingProgressBar) {
                processingProgressBar.style.width = '100%';
            }
            
            const processingStatusText = document.getElementById('processingStatusText');
            if (processingStatusText) {
                processingStatusText.textContent = 'Processing complete!';
            }
            
            // Wait a moment to show completion
            setTimeout(() => {
                // Replace the initial transcript with the final processed transcript
                const resultContainer = document.getElementById('resultContainer');
                if (resultContainer) {
                    // Update the title to indicate this is the final transcript
                    const titleElement = resultContainer.querySelector('.stage-title');
                    if (titleElement) {
                        titleElement.textContent = 'Final Processed Transcript';
                    }
                    
                    // Update the content
                    const resultDiv = document.getElementById('result');
                    if (resultDiv) {
                        // Force a complete refresh of the content
                        resultDiv.innerHTML = formatTranscript(finalData.transcript);
                    }
                    
                    // Make sure the result container is displayed
                    resultContainer.style.display = 'flex';
                }
                
                // Hide processing container but keep labeling available
                const speakerProcessingContainer = document.getElementById('speakerProcessingContainer');
                if (speakerProcessingContainer) {
                    speakerProcessingContainer.style.display = 'none';
                }
                
                // Keep the speaker labeling container visible for re-labeling
                const speakerLabelingContainer = document.getElementById('speakerLabelingContainer');
                if (speakerLabelingContainer) {
                    speakerLabelingContainer.style.display = 'flex';
                    
                    // Update the button text to indicate re-labeling
                    const processSpeakersBtn = document.getElementById('processSpeakersBtn');
                    if (processSpeakersBtn) {
                        processSpeakersBtn.innerHTML = '<span>Re-Process With New Labels</span>';
                        processSpeakersBtn.disabled = false;
                    }
                }
                
                // Make sure the placeholder is hidden
                const placeholderResultContainer = document.getElementById('placeholderResultContainer');
                if (placeholderResultContainer) {
                    placeholderResultContainer.style.display = 'none';
                }
                
                // Reset progress for next time
                processingProgress = 10;
            }, 1000);
        };
        
        // Poll for completion
        const pollUntilComplete = async () => {
            // Check server status first, then fall back to checking final transcript
            const isCompleteServer = await checkServerStatus();
            if (!isCompleteServer) {
                const isCompleteTranscript = await checkFinalTranscript();
                if (!isCompleteTranscript) {
                    setTimeout(pollUntilComplete, 2000);
                }
            }
        };
        
        pollUntilComplete();
        
    } catch (error) {
        console.error('Error in pollProcessingProgress:', error);
        
        clearInterval(processingInterval);
        
        const processingStatusText = document.getElementById('processingStatusText');
        if (processingStatusText) {
            processingStatusText.textContent = 'Error checking processing: ' + error.message;
        }
        
        // Reset the process button
        const processBtn = document.getElementById('processSpeakersBtn');
        if (processBtn) {
            processBtn.disabled = false;
            processBtn.innerHTML = '<span>Process Final Transcript</span>';
        }
        
        // Switch back to labeling view
        const speakerProcessingContainer = document.getElementById('speakerProcessingContainer');
        const speakerLabelingContainer = document.getElementById('speakerLabelingContainer');
        
        if (speakerProcessingContainer) {
            speakerProcessingContainer.style.display = 'none';
        }
        
        if (speakerLabelingContainer) {
            speakerLabelingContainer.style.display = 'flex';
        }
    }
}

async function copyTranscript() {
    try {
        // Get the current transcript
        const response = await fetch('/final-transcript');
        let data = await response.json();
        
        // If there's no final transcript yet, use the initial one
        if (!data.transcript || data.transcript.length === 0) {
            const resultResponse = await fetch('/result');
            data = await resultResponse.json();
        }
        
        // Format transcript for copying
        let content = '';
        let currentSpeaker = '';
        
        data.transcript.forEach(segment => {
            // Format speaker label
            let speakerLabel = segment.speaker;
            if (/^[0-9]+$/.test(speakerLabel) || /^speaker_?[0-9]+$/i.test(speakerLabel)) {
                const speakerNum = speakerLabel.replace(/^speaker_?/i, '');
                speakerLabel = `Speaker ${speakerNum}`;
            }
            
            if (speakerLabel !== currentSpeaker) {
                currentSpeaker = speakerLabel;
                content += `\n${currentSpeaker}:\n`;
            }
            content += `${segment.text}\n`;
        });
        
        // Copy to clipboard
        navigator.clipboard.writeText(content).then(
            () => {
                // Temporarily change button text to indicate success
                const copyBtn = document.getElementById('copyBtn');
                if (copyBtn) {
                    const originalText = copyBtn.innerHTML;
                    copyBtn.innerHTML = '<i class="fas fa-check"></i> <span>Copied!</span>';
                    copyBtn.style.backgroundColor = 'var(--success)';
                    
                    setTimeout(() => {
                        copyBtn.innerHTML = originalText;
                        copyBtn.style.backgroundColor = '';
                    }, 2000);
                }
            },
            () => {
                alert('Failed to copy transcript. Please try again.');
            }
        );
        
    } catch (error) {
        alert('Error copying transcript: ' + error.message);
    }
}

async function downloadTranscript() {
    try {
        // Get the current transcript
        const response = await fetch('/final-transcript');
        let data = await response.json();
        
        // If there's no final transcript yet, use the initial one
        if (!data.transcript || data.transcript.length === 0) {
            const resultResponse = await fetch('/result');
            data = await resultResponse.json();
        }
        
        // Format transcript for download
        let content = '';
        let currentSpeaker = '';
        
        data.transcript.forEach(segment => {
            // Format speaker label
            let speakerLabel = segment.speaker;
            if (/^[0-9]+$/.test(speakerLabel) || /^speaker_?[0-9]+$/i.test(speakerLabel)) {
                const speakerNum = speakerLabel.replace(/^speaker_?/i, '');
                speakerLabel = `Speaker ${speakerNum}`;
            }
            
            if (speakerLabel !== currentSpeaker) {
                currentSpeaker = speakerLabel;
                content += `\n${currentSpeaker}:\n`;
            }
            content += `${segment.text}\n`;
        });
        
        // Create download link
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'transcript.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        // Temporarily change button text to indicate success
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            const originalText = downloadBtn.innerHTML;
            downloadBtn.innerHTML = '<i class="fas fa-check"></i> <span>Downloaded!</span>';
            downloadBtn.style.backgroundColor = 'var(--success)';
            
            setTimeout(() => {
                downloadBtn.innerHTML = originalText;
                downloadBtn.style.backgroundColor = '';
            }, 2000);
        }
        
    } catch (error) {
        alert('Error downloading transcript: ' + error.message);
    }
} 