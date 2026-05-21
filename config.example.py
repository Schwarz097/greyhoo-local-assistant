# Copy this file to config.local.py and edit locally.
# Do not commit config.local.py.

MODEL_NAME = "ilunaz-qwen"
OLLAMA_BASE_URL = "http://localhost:11434"

# Optional WeChat polling settings.
WHITELIST = ["文件传输助手"]
TRIGGER_PREFIX = "/ai"
CHECK_INTERVAL_SECONDS = 2
RECENT_MESSAGE_LIMIT = 8
AUTO_SEND = True
PRINT_DRAFT = True

# UI settings.
PET_IMAGE_SIZE = 220
WINDOW_WIDTH = 397
WINDOW_HEIGHT = 500
