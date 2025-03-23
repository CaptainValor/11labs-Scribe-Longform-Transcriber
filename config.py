import os
import logging

# Configuration settings
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')

# Segment duration in milliseconds (8 minutes)
SEGMENT_DURATION = 8 * 60 * 1000

# Overlap duration in milliseconds (10 seconds)
OVERLAP_DURATION = 10 * 1000

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('transcription.log')
    ]
)
logger = logging.getLogger(__name__) 