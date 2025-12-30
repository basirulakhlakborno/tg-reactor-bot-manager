"""Configuration management."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Server configuration
SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(os.getenv('SERVER_PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Data file path
DATA_FILE = os.getenv('DATA_FILE', str(BASE_DIR / 'data' / 'bot_data.json'))

# Logging configuration
LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'bot_manager.log'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
Path(DATA_FILE).parent.mkdir(parents=True, exist_ok=True)

