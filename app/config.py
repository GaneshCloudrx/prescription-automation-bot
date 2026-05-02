"""
Configuration file for Prescription Automation Bot
Central source of truth for all timeouts, selectors, credentials, and settings
"""
import os
import hashlib
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_ROOT = os.path.dirname(BASE_DIR)
ENV_FILE = os.path.join(BOT_ROOT, "config", ".env")


def _load_env_file(path):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
_load_env_file(ENV_FILE)

# ============================================================================
# EXCEPTION TYPES
# ============================================================================

class BusinessRuleException(Exception):
    """Expected business errors (drug not found, Rx not found, etc.)"""
    pass

class SystemException(Exception):
    """Unexpected system errors (app crash, timeout, element not found, etc.)"""
    pass

# ============================================================================
# MACHINE / BOT IDENTIFICATION
# ============================================================================

MACHINE_NAME = os.environ.get("COMPUTERNAME", "UNKNOWN").upper()
BOT_NAME = "Prescription Automation Bot"

# ============================================================================
# GENERAL SETTINGS
# ============================================================================

PHARMACY_NAME = os.environ.get("PHARMACY_NAME", "Cloudrx")
DEV_MODE = os.environ.get("DEV_MODE", "").strip().lower() == "true"

# ============================================================================
# PIONEER APPLICATION
# ============================================================================

PIONEER_SHORTCUT_PATH = os.path.join(BASE_DIR, "application", "PioneerRx.lnk")
PIONEER_USERNAME = os.environ.get("PIONEER_USERNAME", "")
PIONEER_PASSWORD = os.environ.get("PIONEER_PASSWORD", "")
PIONEER_PIN = os.environ.get("PIONEER_PIN", "")

# ============================================================================
# PORTAL / API CREDENTIALS (from .env or defaults)
# ============================================================================

PORTAL_USERNAME = os.environ.get("PORTAL_USERNAME", "cloud")
PORTAL_PASSWORD = os.environ.get("PORTAL_PASSWORD", "Cloud@20234")
PHARMACIST_NAME = os.environ.get("PHARMACIST_NAME", "Abigail")
SAVE_METHOD = os.environ.get("SAVE_METHOD", "save_and_continue")
LOGIN_SERVER = os.environ.get("LOGIN_SERVER", "")

# ============================================================================
# TIMEOUTS (seconds)
# ============================================================================

TIMEOUT_LOGIN_WINDOW = 60
TIMEOUT_MAIN_WINDOW = 30
TIMEOUT_SEARCH_WINDOW = 15
TIMEOUT_NO_RECORDS = 5
TIMEOUT_ELEMENT_VISIBLE = 5
TIMEOUT_ELEMENT_EXISTS = 5
TIMEOUT_POPUP_CHECK = 1
TIMEOUT_AFTER_CLICK = 0.3
TIMEOUT_AFTER_TYPE = 0.2
TIMEOUT_AFTER_TAB = 0.3
TIMEOUT_AFTER_SEARCH = 3.0

# ============================================================================
# DAILY RESTART
# ============================================================================

BOT_RESTART_HOUR = 1
BOT_RESTART_WINDOW = 120
_restart_offset = int(hashlib.md5(MACHINE_NAME.encode()).hexdigest(), 16) % BOT_RESTART_WINDOW
BOT_RESTART_HOUR_ACTUAL = BOT_RESTART_HOUR + (_restart_offset // 60)
BOT_RESTART_MINUTE_ACTUAL = _restart_offset % 60
LAST_RESTART_FILE = os.path.join(BOT_ROOT, "data", "last_restart_date.txt")

def get_last_restart_date():
    try:
        with open(LAST_RESTART_FILE, "r") as f:
            return datetime.strptime(f.read().strip(), "%Y-%m-%d").date()
    except Exception:
        return None

def set_last_restart_date(d):
    os.makedirs(os.path.dirname(LAST_RESTART_FILE), exist_ok=True)
    with open(LAST_RESTART_FILE, "w") as f:
        f.write(d.strftime("%Y-%m-%d"))

# ============================================================================
# RETRY SETTINGS
# ============================================================================

MAX_SYSTEM_RETRIES = 3
MAX_API_RETRIES = 3

# ============================================================================
# WINDOW SELECTORS (regex patterns for pywinauto title_re)
# ============================================================================

SELECTOR_LOGIN = r".*Logon to PioneerRx.*"
SELECTOR_MAIN = r".*(MainForm|Fill Requests).*"
SELECTOR_FILL_REQUESTS = r".*(Fill Requests|Rx Profile|MainForm).*"
SELECTOR_EDIT_RX = r".*(Edit|Fill Rx).*"
SELECTOR_EDIT_RX_FULL = r".*(Edit|Fill Rx|Fill Requests|Search for|Alerts).*"
SELECTOR_SEARCH_DRUG = r".*Search for a Prescription Item.*"
SELECTOR_RX_PROFILE = r".*Rx Profile.*"

# ============================================================================
# PRESCRIPTION API CONFIGURATION (GET API for fetching Rx data)
# ============================================================================

API_BASE_URL = os.environ.get("API_BASE_URL", "https://devc.reuniterx.com/api/v1/webservice/endpoint/")
PRESCRIPTION_API_ENDPOINT = os.environ.get("PRESCRIPTION_API_ENDPOINT", API_BASE_URL + "rpa_get_drug_substitution.php")
API_TIMEOUT = 30

# ============================================================================
# UPDATE STATUS API
# ============================================================================

API_UPDATE_ENDPOINT = os.environ.get("API_UPDATE_ENDPOINT", "https://devc.reuniterx.com/api/v1/webservice/endpoint/rpa_update_drug_substitution.php")

# ============================================================================
# FILE PATHS
# ============================================================================

LOGS_DIR = os.path.join(BOT_ROOT, "logs")
REPORTS_DIR = os.path.join(BOT_ROOT, "reports")
RETRY_FILE_PATH = os.path.join(BOT_ROOT, "data", f"retry_{datetime.now().strftime('%Y-%m-%d')}.txt")

# ============================================================================
# API LOGGING
# ============================================================================

API_AUTH_HEADER = "Basic Y2xvdWQxOkNsb3VkQDIwMjY="
API_LOG_ENABLED = True
API_LOG_ENDPOINT = "https://devc.reuniterx.com/api/v1/webservice/endpoint/rpa_get_bot_status.php"
API_LOG_BATCH_SIZE = 10
API_LOG_BATCH_INTERVAL = 5

HEARTBEAT_URL = "https://portal.reuniterx.com/api/v1/webservice/endpoint/rpa_get_bot_status.php"
HEARTBEAT_BOT_NAME = "PrescriptionAutomationBot"

# ============================================================================
# SCREEN RECORDING
# ============================================================================

RECORDINGS_DIR = os.path.join(BOT_ROOT, "recordings")
RECORDING_FPS = 5
RECORDING_QUALITY = "medium"
RECORDING_MAX_SIZE_GB = 2
