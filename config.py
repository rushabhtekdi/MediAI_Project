import os
from dotenv import load_dotenv

load_dotenv()

# Set to True for development/testing without making API calls
# Set to False to use the actual Anthropic API
USE_MOCK_RESPONSE = False

# Get API key from environment variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Verify that the API key is available
if not ANTHROPIC_API_KEY and not USE_MOCK_RESPONSE:
    print("WARNING: Anthropic API key not found and mock responses are disabled.")
    print("Either add your API key to the .env file or set USE_MOCK_RESPONSE to True.")