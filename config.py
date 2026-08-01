#Imports & Config
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI 
from openai import RateLimitError

#Load .env file
load_dotenv()

#API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Call the chat API with automatic retry on rate limits
# Waits and retries instead of crashing when the per minute token limit is hit
def chat_with_retry(max_retries=5, **kwargs):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError:
            wait = 12 * (attempt + 1)   # back off longer each time
            print(f"  Rate limit hit, waiting {wait}s (attempt {attempt+1}/{max_retries})")
            time.sleep(wait)
    # Final attempt, let the error raise if it still fails
    return client.chat.completions.create(**kwargs)

#Paths
BASE_DIR = Path(__file__).parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
DOM_DIR = BASE_DIR / "dom"
OUTPUTS_DIR = BASE_DIR / "outputs"
DB_PATH = BASE_DIR / "qa_pipeline.db"

#Create directories if they don't exist
SCREENSHOTS_DIR.mkdir(exist_ok=True)
DOM_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

#Model
MODEL = "gpt-4o"

