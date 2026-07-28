#Imports & Config
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

#Load .env file
load_dotenv()

#API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

#Paths
BASE_DIR = Path(__file__).parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
DOM_DIR = BASE_DIR / "dom"
OUTPUTS_DIR = BASE_DIR / "outputs"
DB_PATH = BASE_DIR / "qa_pipeline.db"

#Create directories if they don't exist
SCREENSHOTS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

#Model
MODEL = "gpt-4o"