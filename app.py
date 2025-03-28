from flask import Flask, render_template, request, jsonify, send_from_directory, redirect
import os
import uuid
import threading
import logging
import traceback
import json
import time

# Import configuration
from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH, SEGMENT_DURATION, OVERLAP_DURATION

# Track import errors
import_errors = []

# Import modules with improved error handling
try:
    from modules.utils import save_uploaded_file, clean_up_file
    utils_imported = True
except ImportError as e:
    error_msg = f"Error importing utils module: {e}"
    import_errors.append(error_msg)
    logging.error(error_msg)
    print(f"Error: Could not import utils module. Make sure all requirements are installed.")
    utils_imported = False

# Import the FFmpeg-based audio module
try:
    from modules.audio import split_audio
    audio_imported = True
    print("Successfully imported FFmpeg-based audio module")
except ImportError as e:
    error_msg = f"Error importing audio module: {e}"
    import_errors.append(error_msg)
    logging.error(error_msg)
    print(f"Failed to import audio module: {e}")
    audio_imported = False

try:
    from modules.transcription import transcribe_segment_with_requests, process_transcript_with_labels
    from modules.api import log_elevenlabs_endpoints, check_scribe_access, log_api_capabilities
    api_imported = True
except ImportError as e:
    error_msg = f"Error importing transcription/API modules: {e}"
    import_errors.append(error_msg)
    logging.error(error_msg)
    print(f"Error: Could not import transcription or API modules. Make sure all requirements are installed.")
    api_imported = False

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create a static directory if it doesn't exist
os.makedirs('static/img', exist_ok=True)

# Configure logger
logger = logging.getLogger(__name__)

# Global variables to track transcription progress
current_job = {
    'id': None,
    'progress': 0,
    'status': 'Not started',
    'complete': False,
    'transcript': [],
    'processing_progress': 0,
    'processing_complete': False
}

def process_audio(file_path, api_key, enable_diarization=True, num_speakers='', model_id='scribe_v1'):
    """Process audio file: split into segments and transcribe."""
    global current_job
    
    try:
        logger.info(f"Starting audio processing for file: {file_path}")
        logger.info(f"Settings: diarization={enable_diarization}, speakers={num_speakers}, model={model_id}")
        
        # Log API capabilities at the beginning
        log_elevenlabs_endpoints(api_key)
        
        # Split audio into segments with overlap
        current_job['status'] = 'Splitting audio into segments'
        logger.info("Splitting audio file into segments with overlap")
        
        try:
            # Pass app.config to avoid application context issues
            segments = split_audio(
                file_path, 
                SEGMENT_DURATION, 
                OVERLAP_DURATION, 
                app_config=app.config
            )
            logger.info(f"Successfully split audio into {len(segments)} segments")
            current_job['raw_segments'] = segments  # Store raw segment information
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Error splitting audio: {str(e)}")
            logger.error(f"Traceback: {error_details}")
            current_job['status'] = f'Error splitting audio: {str(e)}'
            current_job['complete'] = True
            return
        
        # Transcribe each segment
        segment_transcriptions = []
        for i, segment in enumerate(segments):
            segment_path = segment['path']
            segment_index = segment['index']
            
            current_job['status'] = f'Transcribing segment {i+1} of {len(segments)}'
            current_job['progress'] = int((i / len(segments)) * 100)
            logger.info(f"Starting transcription of segment {i+1}/{len(segments)}: {segment_path}")
            
            segment_transcript = transcribe_segment_with_requests(
                segment_path, 
                api_key, 
                enable_diarization, 
                num_speakers, 
                model_id
            )
            
            # Add segment metadata to transcript
            for item in segment_transcript:
                item['segment_index'] = segment_index
                item['segment_start_time'] = segment['start_time']
                item['absolute_start'] = segment['start_time'] + item.get('start', 0)
                item['absolute_end'] = segment['start_time'] + item.get('end', 0)
            
            logger.info(f"Segment {i+1} transcription result has {len(segment_transcript)} items")
            segment_transcriptions.append(segment_transcript)
            
            # Update only the first segment for initial display
            if i == 0:
                current_job['first_segment'] = segment_transcript
                current_job['transcript'] = segment_transcript
            
            # Store all segments for later processing
            current_job['all_segments'] = segment_transcriptions
            
            # Clean up segment file
            clean_up_file(segment_path)
        
        # Mark as ready for post-processing
        current_job['status'] = 'Ready for speaker labeling'
        current_job['progress'] = 100
        current_job['stage'] = 'speaker_labeling'  # Indicate we're in the labeling stage
        current_job['complete'] = True
        
        # Extract unique speakers from the first segment for labeling
        speakers = set()
        for item in current_job['first_segment']:
            speakers.add(item.get('speaker', 'Unknown'))
        
        current_job['speakers'] = list(speakers)
        logger.info(f"Found {len(speakers)} unique speakers in the first segment")
        
        # Clean up original file
        clean_up_file(file_path)
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in process_audio: {str(e)}")
        logger.error(f"Traceback: {error_details}")
        current_job['status'] = f'Error: {str(e)}'
        current_job['complete'] = True

def ensure_logo_exists():
    """Make sure we have the ElevenLabs logo downloaded."""
    logo_path = os.path.join('static/img', '11labs-logo.png')
    if not os.path.exists(logo_path):
        try:
            import requests
            logger.info("Downloading ElevenLabs logo...")
            response = requests.get('https://elevenlabs.io/images/logo.png', stream=True)
            if response.status_code == 200:
                with open(logo_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                logger.info(f"Logo downloaded to {logo_path}")
            else:
                logger.warning(f"Failed to download logo: status {response.status_code}")
        except Exception as e:
            logger.warning(f"Error downloading logo: {str(e)}")

# Routes
@app.route('/')
def index():
    if import_errors:
        error_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dependency Error</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .error { background-color: #ffebee; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
                h1 { color: #d32f2f; }
                pre { background-color: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }
                .solution { background-color: #e8f5e9; padding: 15px; border-radius: 4px; margin-top: 20px; }
                .command { background-color: #f5f5f5; padding: 8px; border-radius: 4px; display: inline-block; font-family: monospace; }
            </style>
        </head>
        <body>
            <h1>Dependency Error</h1>
            <p>The application could not start because of the following issues:</p>
            <div class="error">
                <pre>%s</pre>
            </div>
            <div class="solution">
                <h2>Solution</h2>
                <p>This application requires FFmpeg to be installed on your system:</p>
                <ol>
                    <li><strong>Install FFmpeg</strong>:
                        <ul>
                            <li>Mac: <span class="command">brew install ffmpeg</span></li>
                            <li>Ubuntu/Debian: <span class="command">sudo apt-get install ffmpeg</span></li>
                            <li>Windows: Download from <a href="https://ffmpeg.org/download.html" target="_blank">ffmpeg.org</a> and add to your PATH</li>
                        </ul>
                    </li>
                    <li><strong>Verify FFmpeg is working</strong>: Run <span class="command">ffmpeg -version</span> in your terminal</li>
                    <li><strong>Install Python dependencies</strong>: <span class="command">pip install -r requirements.txt</span></li>
                </ol>
            </div>
        </body>
        </html>
        """ % '\n'.join(import_errors)
        return error_html
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    global current_job
    
    # Get file and API key from the request
    audio_file = request.files.get('audio')
    api_key = request.form.get('api_key')
    
    # Get diarization settings
    enable_diarization = request.form.get('enable_diarization', 'true').lower() == 'true'
    num_speakers = request.form.get('num_speakers', '')
    model_id = request.form.get('model_id', 'scribe_v1')
    
    if not audio_file or not api_key:
        return jsonify({'error': 'Missing audio file or API key'}), 400
    
    # Save uploaded file before starting the thread
    try:
        file_path = save_uploaded_file(audio_file)
    except Exception as e:
        return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
    
    # Reset current job
    current_job = {
        'id': str(uuid.uuid4()),
        'progress': 0,
        'status': 'Processing audio file',
        'complete': False,
        'transcript': [],
        'file_path': file_path,
        'enable_diarization': enable_diarization,
        'num_speakers': num_speakers,
        'model_id': model_id,
        'processing_progress': 0,
        'processing_complete': False
    }
    
    # Start processing in a background thread
    threading.Thread(
        target=process_audio, 
        args=(
            file_path, 
            api_key, 
            enable_diarization, 
            num_speakers, 
            model_id
        )
    ).start()
    
    return jsonify({'job_id': current_job['id']}), 202

@app.route('/progress', methods=['GET'])
def progress():
    return jsonify({
        'progress': current_job['progress'],
        'status': current_job['status'],
        'complete': current_job['complete'],
        'transcript': current_job['transcript']
    })

@app.route('/result', methods=['GET'])
def result():
    return jsonify({
        'transcript': current_job['transcript']
    })

@app.route('/speakers', methods=['GET'])
def get_speakers():
    speakers = current_job.get('speakers', [])
    return jsonify({'speakers': speakers})

@app.route('/process-transcript', methods=['POST'])
def process_transcript():
    global current_job
    
    # Get speaker labels from request
    data = request.json
    speaker_labels = data.get('speaker_labels', {})
    
    # Log the received speaker labels for debugging
    logger.info(f"Received speaker labels: {speaker_labels}")
    
    if not speaker_labels:
        return jsonify({"error": "No speaker labels provided"}), 400
    
    # Reset processing status to ensure fresh processing
    current_job["processing_progress"] = 0
    current_job["processing_complete"] = False
    current_job["final_transcript"] = []  # Clear any existing final transcript
    
    current_job["status"] = "Processing transcript with custom speaker labels"
    
    # Start processing in background thread
    threading.Thread(
        target=process_transcript_with_labels, 
        args=(current_job, speaker_labels)
    ).start()
    
    return jsonify({"status": "processing"}), 202

@app.route('/processing-progress', methods=['GET'])
def processing_progress():
    return jsonify({
        'progress': current_job.get('processing_progress', 0),
        'status': current_job.get('status', 'Processing'),
        'complete': current_job.get('processing_complete', False)
    })

@app.route('/final-transcript', methods=['GET'])
def get_final_transcript():
    final_transcript = current_job.get('final_transcript', [])
    
    # Add debug logging
    logger.info(f"Returning final transcript with {len(final_transcript)} entries")
    if len(final_transcript) > 0:
        logger.debug(f"Sample entry: {final_transcript[0]}")
    
    return jsonify({'transcript': final_transcript})

@app.route('/debug-transcript', methods=['GET'])
def debug_transcript():
    """Debug endpoint to show the current state of transcript processing."""
    return jsonify({
        'job_status': current_job.get('status', 'Unknown'),
        'processing_complete': current_job.get('processing_complete', False),
        'processing_progress': current_job.get('processing_progress', 0),
        'final_transcript_count': len(current_job.get('final_transcript', [])),
        'transcript_sample': current_job.get('final_transcript', [])[:2],
        'has_first_segment': 'first_segment' in current_job,
        'has_all_segments': 'all_segments' in current_job
    })

@app.route('/logo')
def logo():
    """Serve the ElevenLabs logo."""
    try:
        # First try to serve from static directory
        return send_from_directory('static/img', '11labs-logo.png')
    except:
        # If the logo file isn't found, create a redirect to the ElevenLabs logo
        return redirect('https://elevenlabs.io/images/logo.png')

if __name__ == '__main__':
    ensure_logo_exists()
    app.run(debug=True) 