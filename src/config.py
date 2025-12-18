"""
Configuration module for loading environment variables.
Loads credentials from .env file if present.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Load .env file if it exists
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded environment variables from {env_path}")
else:
    print("⚠ No .env file found, using system environment variables")

# Google Cloud Vision Configuration
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


def validate_credentials():
    """
    Validate that all required credentials are configured.
    
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    
    # Check Google Cloud credentials
    if not GOOGLE_APPLICATION_CREDENTIALS:
        errors.append("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
    else:
        # Check if file exists
        creds_path = PROJECT_ROOT / GOOGLE_APPLICATION_CREDENTIALS
        if not creds_path.exists():
            errors.append(f"❌ Google credentials file not found: {creds_path}")
        else:
            print(f"✓ Google Cloud credentials found: {creds_path}")
    
    # Check OpenAI API key
    if not OPENAI_API_KEY:
        errors.append("❌ OPENAI_API_KEY not set")
    elif OPENAI_API_KEY == "your-openai-api-key-here":
        errors.append("❌ OPENAI_API_KEY is still set to placeholder value")
    else:
        print(f"✓ OpenAI API key configured")
    
    return len(errors) == 0, errors


if __name__ == "__main__":
    # Test configuration when run directly
    print("\n" + "="*60)
    print("Configuration Validation")
    print("="*60 + "\n")
    
    is_valid, errors = validate_credentials()
    
    if is_valid:
        print("\n✅ All credentials configured correctly!")
    else:
        print("\n⚠ Configuration issues found:\n")
        for error in errors:
            print(f"  {error}")
        print("\nPlease update your .env file with the correct values.")
    
    print("\n" + "="*60 + "\n")
