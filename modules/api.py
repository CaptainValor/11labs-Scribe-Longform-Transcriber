import requests
import logging
import traceback

logger = logging.getLogger(__name__)

def log_elevenlabs_endpoints(api_key):
    """Log available ElevenLabs API endpoints for troubleshooting."""
    try:
        headers = {
            'xi-api-key': api_key,
            'Accept': 'application/json'
        }
        
        # Try to get the OpenAPI spec
        response = requests.get(
            'https://api.elevenlabs.io/v1/docs',
            headers=headers
        )
        
        if response.status_code == 200:
            logger.info("Successfully retrieved ElevenLabs API spec")
        else:
            logger.warning(f"Could not retrieve API spec, status: {response.status_code}")
            
        # Try listing the models (should work for all accounts)
        response = requests.get(
            'https://api.elevenlabs.io/v1/models',
            headers=headers
        )
        
        if response.status_code == 200:
            models = response.json()
            logger.info(f"Available models: {models}")
        else:
            logger.warning(f"Could not retrieve models, status: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error logging endpoints: {str(e)}")

def check_scribe_access(api_key):
    """Check if the API key has access to Scribe."""
    try:
        headers = {
            'xi-api-key': api_key,
            'Accept': 'application/json'
        }
        
        # Check models to see if Scribe is available
        response = requests.get(
            'https://api.elevenlabs.io/v1/models',
            headers=headers
        )
        
        if response.status_code != 200:
            logger.warning(f"Failed to retrieve models: {response.status_code}")
            return False
        
        models_data = response.json()
        logger.info(f"Available models: {models_data}")
        
        # Check if any of the models indicate Scribe/speech recognition capability
        has_scribe = False
        for model in models_data.get('models', []):
            model_id = model.get('model_id', '').lower()
            name = model.get('name', '').lower()
            description = model.get('description', '').lower()
            
            if ('whisper' in model_id or 
                'scribe' in model_id or 
                'transcription' in name or 
                'speech recognition' in description or
                'speech-to-text' in description):
                logger.info(f"Found speech recognition model: {model.get('name')}")
                has_scribe = True
                break
        
        return has_scribe
        
    except Exception as e:
        logger.error(f"Error checking Scribe access: {str(e)}")
        return False

def log_api_capabilities(api_key):
    """Log the API capabilities available to this key."""
    try:
        headers = {
            'xi-api-key': api_key,
            'Accept': 'application/json'
        }
        
        endpoints_to_test = [
            'https://api.elevenlabs.io/v1/models',
            'https://api.elevenlabs.io/v1/user',
            'https://api.elevenlabs.io/v1/user/subscription',
            'https://api.elevenlabs.io/v1/speech-to-text/models',
            'https://api.elevenlabs.io/v1/audio-to-speech-text/models'
        ]
        
        logger.info("Testing API endpoints accessibility:")
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(endpoint, headers=headers)
                logger.info(f"Endpoint {endpoint}: Status {response.status_code}")
                if response.status_code == 200:
                    logger.info(f"  Response keys: {list(response.json().keys()) if response.text else 'empty'}")
            except Exception as e:
                logger.warning(f"  Error testing {endpoint}: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error logging API capabilities: {str(e)}") 