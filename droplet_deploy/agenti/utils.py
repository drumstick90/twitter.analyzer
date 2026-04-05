import os
from anthropic import Anthropic

def get_latest_opus_model(api_key=None):
    """
    Finds the latest available Claude 3 Opus model.
    Defaults to 'claude-3-opus-20240229' if API call fails or no newer model found.
    """
    default_model = "claude-3-opus-20240229"
    
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return default_model
        
    try:
        client = Anthropic(api_key=api_key)
        # List models is available in newer SDK versions
        # If not available, we catch the error and return default
        if hasattr(client.models, 'list'):
            models = client.models.list()
            opus_models = [
                m.id for m in models.data 
                if "claude-3-opus" in m.id and not m.id.endswith("-200k") # Filter out legacy/context variants if any
            ]
            
            if not opus_models:
                return default_model
                
            # Sort by date/version string (simple string sort works for YYYYMMDD suffix)
            opus_models.sort(reverse=True)
            return opus_models[0]
            
    except Exception as e:
        # Fallback silently on error
        pass
        
    return default_model
