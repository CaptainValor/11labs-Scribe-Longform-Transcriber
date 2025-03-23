import os
import uuid
import logging
from flask import current_app

logger = logging.getLogger(__name__)

def save_uploaded_file(file):
    """Save the uploaded file to a temporary location."""
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filepath

def clean_up_file(file_path):
    """Remove a file."""
    try:
        os.remove(file_path)
        logger.info(f"Removed file: {file_path}")
        return True
    except Exception as e:
        logger.warning(f"Failed to remove file {file_path}: {str(e)}")
        return False 