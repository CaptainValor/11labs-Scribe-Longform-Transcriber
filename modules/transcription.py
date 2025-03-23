import logging
import traceback
import requests
import time
from modules.utils import clean_up_file

logger = logging.getLogger(__name__)

def transcribe_segment_with_requests(segment_path, api_key, enable_diarization=True, num_speakers='', model_id='scribe_v1'):
    """Transcribe a single audio segment using ElevenLabs API."""
    try:
        logger.info(f"Starting transcription for segment: {segment_path}")
        logger.info(f"Settings: diarization={enable_diarization}, speakers={num_speakers}, model={model_id}")
        
        # Read the audio file
        with open(segment_path, 'rb') as audio_file:
            audio_data = audio_file.read()
            
            # Log file size for debugging
            file_size = len(audio_data)
            logger.info(f"Audio file size: {file_size} bytes")
            
            # The correct endpoint according to documentation
            url = 'https://api.elevenlabs.io/v1/speech-to-text'
            
            logger.info(f"Making request to ElevenLabs API: {url}")
            
            headers = {
                'xi-api-key': api_key,
                'Accept': 'application/json'
            }
            
            # Create the multipart form data
            files = {
                'file': ('audio.mp3', audio_data, 'audio/mpeg')
            }
            
            # Parameters according to documentation
            data = {
                'model_id': model_id,  # should be 'scribe_v1'
            }
            
            # Add diarization parameters if enabled
            if enable_diarization:
                data['diarize'] = 'true'
                if num_speakers:
                    data['num_speakers'] = num_speakers
            
            logger.info(f"Request data: {data}")
            logger.info("Request setup complete, sending API request...")
            
            # Make the request with the correct parameters
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data
            )
            
            # Log response status and headers for debugging
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            
            # Add complete response logging for debugging
            logger.info(f"Response content: {response.text}")
            
            # Check if response is successful
            if response.status_code != 200:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                return []
            
            # Process the response
            logger.info("Processing response data...")
            try:
                result = response.json()
                logger.info(f"Raw JSON response structure keys: {list(result.keys())}")
            except Exception as e:
                logger.warning(f"Could not parse response as JSON: {str(e)}")
                return []
            
            # Initialize transcription array
            transcription = []
            
            # Extract text from the response
            if 'text' in result:
                # If there's no diarization, just return the plain text
                if not enable_diarization:
                    transcription.append({
                        'text': result['text'],
                        'speaker': '1',
                        'start': 0,
                        'end': 0
                    })
                # If there's diarization, parse the words to get speaker info
                elif 'words' in result:
                    # Group words by speaker
                    current_speaker = None
                    current_text = ""
                    current_start = 0
                    
                    for word in result['words']:
                        speaker_id = word.get('speaker_id', 'Unknown')
                        
                        # If this is a new speaker, add the previous segment and start a new one
                        if current_speaker and speaker_id != current_speaker:
                            transcription.append({
                                'text': current_text.strip(),
                                'speaker': current_speaker.replace('speaker_', ''),
                                'start': current_start,
                                'end': word.get('start', 0)
                            })
                            current_text = ""
                            current_start = word.get('start', 0)
                        
                        # If this is the first word, set the current speaker and start time
                        if not current_speaker:
                            current_speaker = speaker_id
                            current_start = word.get('start', 0)
                        
                        # Add the word to the current text
                        current_text += word.get('text', '')
                        current_speaker = speaker_id
                    
                    # Add the last segment
                    if current_text:
                        transcription.append({
                            'text': current_text.strip(),
                            'speaker': current_speaker.replace('speaker_', ''),
                            'start': current_start,
                            'end': result['words'][-1].get('end', 0) if result['words'] else 0
                        })
                else:
                    # Fallback if there are no words but there is text
                    transcription.append({
                        'text': result['text'],
                        'speaker': '1',
                        'start': 0,
                        'end': 0
                    })
            
            logger.info(f"Transcription complete with {len(transcription)} segments")
            return transcription
            
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error transcribing segment {segment_path}: {str(e)}")
        logger.error(f"Traceback: {error_details}")
        return []

def merge_transcriptions(segments, speaker_labels, raw_segments=None):
    """Merge transcriptions and apply speaker labels with improved speaker matching."""
    try:
        # Log the inputs for debugging
        logger.info(f"Starting transcript merging with {len(segments)} segments")
        logger.info(f"Speaker labels received: {speaker_labels}")
        
        # First, flatten all segments with absolute timestamps
        all_utterances = []
        
        for segment_idx, segment_transcript in enumerate(segments):
            # Use raw_segments argument instead of current_job
            segment_info = next((s for s in raw_segments if s.get('index') == segment_idx), None) if raw_segments else None
            
            # If segment info not found, use default values
            if not segment_info:
                segment_start_time = 0
            else:
                segment_start_time = segment_info.get('start_time', 0)
            
            for item in segment_transcript:
                # Calculate absolute timestamps
                start_time = segment_start_time + item.get('start', 0)
                end_time = segment_start_time + item.get('end', 0)
                
                all_utterances.append({
                    'text': item.get('text', ''),
                    'speaker': item.get('speaker', 'Unknown'),
                    'start': start_time,
                    'end': end_time,
                    'segment_index': segment_idx,
                    'original_speaker': item.get('speaker', 'Unknown')  # Keep original speaker ID for reference
                })
        
        # Sort by start time
        all_utterances.sort(key=lambda x: x['start'])
        
        # Simplified speaker mapping approach - map everything to the first segment's speakers
        # This avoids creating new_speaker_X labels
        speaker_mapping = {}  # Maps segment_idx, speaker_id to a global speaker ID
        
        # First segment speakers are the canonical ones
        first_segment_speakers = sorted(set(u['speaker'] for u in all_utterances if u['segment_index'] == 0))
        
        # Mapping for first segment speakers (identity mapping)
        for speaker in first_segment_speakers:
            speaker_mapping[(0, speaker)] = speaker
        
        # For each subsequent segment, find best speaker matches
        for segment_idx in range(1, max(u['segment_index'] for u in all_utterances) + 1):
            # Get speakers in this segment
            segment_speakers = sorted(set(u['speaker'] for u in all_utterances if u['segment_index'] == segment_idx))
            
            # Map each segment speaker to the most similar first-segment speaker
            for speaker in segment_speakers:
                # If we already have fewer than or equal speakers in the first segment, use a simple mapping
                if len(segment_speakers) <= len(first_segment_speakers):
                    # Try to map by position/index
                    try:
                        idx = segment_speakers.index(speaker)
                        if idx < len(first_segment_speakers):
                            speaker_mapping[(segment_idx, speaker)] = first_segment_speakers[idx]
                        else:
                            speaker_mapping[(segment_idx, speaker)] = first_segment_speakers[0]
                    except:
                        # Fallback to first speaker
                        speaker_mapping[(segment_idx, speaker)] = first_segment_speakers[0]
                else:
                    # More speakers in this segment than the first - use modulo mapping
                    try:
                        idx = segment_speakers.index(speaker) % len(first_segment_speakers)
                        speaker_mapping[(segment_idx, speaker)] = first_segment_speakers[idx]
                    except:
                        # Fallback to first speaker
                        speaker_mapping[(segment_idx, speaker)] = first_segment_speakers[0]
        
        # Apply speaker mapping and custom labels
        final_transcript = []
        
        for utterance in all_utterances:
            segment_idx = utterance['segment_index']
            original_speaker = utterance['speaker']
            
            # Get mapped speaker ID from first segment
            mapped_speaker = speaker_mapping.get((segment_idx, original_speaker), original_speaker)
            
            # Apply custom label if available
            speaker_label = speaker_labels.get(mapped_speaker, f"Speaker {mapped_speaker}")
            
            # Create transcript entry
            entry = {
                'text': utterance['text'],
                'speaker': speaker_label,
                'start': utterance['start'],
                'end': utterance['end'],
                'segment_index': segment_idx
            }
            
            final_transcript.append(entry)
        
        # Sort by start time
        final_transcript.sort(key=lambda x: x['start'])
        
        # Merge adjacent utterances from the same speaker
        merged_transcript = []
        current_entry = None
        
        for entry in final_transcript:
            if not current_entry:
                current_entry = entry.copy()
                continue
                
            # If same speaker and close in time, merge
            if (entry['speaker'] == current_entry['speaker'] and 
                entry['start'] - current_entry['end'] < 2000):  # 2 second threshold
                current_entry['text'] += " " + entry['text']
                current_entry['end'] = entry['end']
            else:
                merged_transcript.append(current_entry)
                current_entry = entry.copy()
        
        if current_entry:
            merged_transcript.append(current_entry)
        
        # Log the speaker mapping that was created
        logger.info(f"Created speaker mapping: {speaker_mapping}")
        
        # Log the final transcript
        logger.info(f"Final transcript has {len(merged_transcript)} entries")
        
        return merged_transcript
    except Exception as e:
        logger.error(f"Error merging transcriptions: {str(e)}")
        traceback.print_exc()
        return []

def process_transcript_with_labels(current_job, speaker_labels):
    """Process transcript with custom speaker labels."""
    try:
        # Initial status update
        current_job['status'] = "Merging transcription segments"
        current_job['processing_progress'] = 10
        
        # Simulate processing steps with realistic timing
        time.sleep(0.5)
        
        current_job['status'] = "Analyzing segment overlaps"
        current_job['processing_progress'] = 30
        time.sleep(0.5)
        
        current_job['status'] = "Mapping speaker identities"
        current_job['processing_progress'] = 50
        time.sleep(0.5)
        
        # Get all segments from the job
        all_segments = current_job.get('all_segments', [])
        
        if not all_segments:
            current_job['status'] = "Error: No transcript segments found"
            current_job['processing_complete'] = True
            return
        
        current_job['status'] = "Applying speaker labels"
        current_job['processing_progress'] = 70
        time.sleep(0.5)
        
        # Merge transcripts and apply speaker labels
        raw_segments = current_job.get('raw_segments', [])
        final_transcript = merge_transcriptions(all_segments, speaker_labels, raw_segments)
        
        # Update job with final transcript
        current_job['final_transcript'] = final_transcript
        current_job['status'] = "Processing complete"
        current_job['processing_progress'] = 100
        current_job['processing_complete'] = True
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error processing transcript: {str(e)}")
        logger.error(f"Traceback: {error_details}")
        current_job['status'] = f"Error: {str(e)}"
        current_job['processing_complete'] = True 