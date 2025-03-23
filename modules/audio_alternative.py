"""
FFmpeg-based audio processing module.
This module uses FFmpeg directly to split audio files without any dependency on pydub or pyaudioop.
"""
import os
import uuid
import logging
import traceback
import subprocess
import json
from flask import current_app as app

logger = logging.getLogger(__name__)

def get_audio_duration(file_path):
    """Get the duration of an audio file using ffprobe."""
    try:
        cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'json', 
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        duration_sec = float(data['format']['duration'])
        return int(duration_sec * 1000)  # Convert to milliseconds
    except Exception as e:
        logger.error(f"Error getting audio duration: {str(e)}")
        raise e

def split_audio(file_path, segment_duration, overlap_duration, app_config=None):
    """Split audio file into segments of specified duration with overlap using ffmpeg directly."""
    try:
        # Check if ffmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            raise ImportError("FFmpeg is not installed or not in PATH. Please install FFmpeg.")
        
        # Get duration of audio file
        total_duration = get_audio_duration(file_path)
        
        # Calculate number of segments
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
            
            # Convert milliseconds to seconds for ffmpeg
            start_sec = start / 1000
            duration_sec = (end - start) / 1000
            
            # Generate unique filename
            segment_filename = f"segment_{i}_{uuid.uuid4()}.mp3"
            segment_path = os.path.join(upload_folder, segment_filename)
            
            # Use ffmpeg to extract segment
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output files
                '-i', file_path,  # Input file
                '-ss', str(start_sec),  # Start time
                '-t', str(duration_sec),  # Duration
                '-acodec', 'libmp3lame',  # MP3 codec
                '-q:a', '2',  # Quality
                segment_path  # Output file
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            # Store segment information
            segments.append({
                'path': segment_path,
                'start_time': start,
                'end_time': end,
                'index': i
            })
        
        return segments
    except ImportError as ie:
        error_details = traceback.format_exc()
        logger.error(f"Import Error: {str(ie)}")
        logger.error(f"Make sure FFmpeg is installed and available in your PATH")
        logger.error(f"Traceback: {error_details}")
        raise ie
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error splitting audio: {str(e)}")
        logger.error(f"Traceback: {error_details}")
        raise e 