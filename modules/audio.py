import os
import uuid
import logging
from pydub import AudioSegment
import traceback
from flask import current_app as app

logger = logging.getLogger(__name__)

def split_audio(file_path, segment_duration, overlap_duration, app_config=None):
    """Split audio file into segments of specified duration with overlap."""
    try:
        audio = AudioSegment.from_file(file_path)
        
        # Calculate number of segments
        total_duration = len(audio)
        effective_segment = segment_duration - overlap_duration  # Adjust for overlap
        num_segments = max(1, (total_duration + effective_segment - 1) // effective_segment)  # Ceiling division
        
        logger.info(f"Splitting audio file of {total_duration}ms into {num_segments} segments with {overlap_duration}ms overlap")
        
        # Determine upload folder - use provided config or fallback
        upload_folder = app_config.get('UPLOAD_FOLDER') if app_config else 'uploads'
        
        segments = []
        for i in range(num_segments):
            # Calculate start and end times with overlap
            start = i * effective_segment
            end = min(start + segment_duration, total_duration)
            
            # For the first segment, there's no leading overlap
            # For subsequent segments, include the overlap at the beginning
            if i > 0:
                start = max(0, start - overlap_duration)
            
            segment = audio[start:end]
            
            # Save segment to a temporary file
            segment_filename = f"segment_{i}_{uuid.uuid4()}.mp3"
            segment_path = os.path.join(upload_folder, segment_filename)
            segment.export(segment_path, format="mp3")
            
            # Store segment information
            segments.append({
                'path': segment_path,
                'start_time': start,
                'end_time': end,
                'index': i
            })
        
        return segments
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error splitting audio: {str(e)}")
        logger.error(f"Traceback: {error_details}")
        raise e 