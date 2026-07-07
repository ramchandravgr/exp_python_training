import os
from dotenv import load_dotenv

load_dotenv()

API_SECRET_ACCESS_KEY = os.environ.get("API_SECRET_ACCESS_KEY")
INTEGRATION_GATEWAY_URL = os.environ.get("INTEGRATION_GATEWAY_URL")
ENFORCE_STRICT_AUDIT = os.environ.get("ENFORCE_STRICT_AUDIT") == True
VERBOSE_DEBUG_METRICS = os.environ.get("VERBOSE_DEBUG_METRICS") == True
