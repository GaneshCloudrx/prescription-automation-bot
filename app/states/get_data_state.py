"""
Get Data State - Fetch next prescription from API
Returns transaction dict or None if no more items
"""
import sys
import os
import time
import base64
from datetime import datetime

import requests
from pywinauto.keyboard import send_keys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modules.helper import log_print, stop_recording, start_recording, restart_server
from modules import prescription_api, login


def _heartbeat():
    """Send heartbeat to portal and return active status."""
    auth = base64.b64encode(f"{config.PORTAL_USERNAME}:{config.PORTAL_PASSWORD}".encode()).decode()
    body = {"server_name": config.MACHINE_NAME, "bot_name": config.HEARTBEAT_BOT_NAME}
    for attempt in range(3):
        try:
            resp = requests.post(
                config.HEARTBEAT_URL, json=body,
                headers={"Authorization": f"Basic {auth}"},
                timeout=config.API_TIMEOUT,
            )
            if resp.ok:
                data = resp.json().get("data", {})
                if isinstance(data, list):
                    data = data[0] if data else {}
                active = data.get("active", "1") if isinstance(data, dict) else "1"
                log_print(f"[HEARTBEAT] active={active}")
                return str(active).strip()
        except Exception as e:
            log_print(f"[HEARTBEAT] Attempt {attempt + 1} failed: {e}")
    return "1"


def run():
    """
    Get next transaction item to process.
    1. Check heartbeat / daily restart
    2. Fetch next prescription from API

    Returns:
        dict: Transaction data with keys (api_id, rx_number, drug_ndc, drug_name,
              substitute_drug_dose, sig, annotation, is_compound, raw_response)
              or None if no more items

    Raises:
        config.SystemException: If API call fails after retries
    """
    log_print("=" * 60)
    log_print("[GET_DATA] Getting next transaction")
    log_print("=" * 60)

    # Daily restart check
    now = datetime.now()
    if (
        not config.DEV_MODE
        and config.get_last_restart_date() != now.date()
        and (now.hour, now.minute) >= (config.BOT_RESTART_HOUR_ACTUAL, config.BOT_RESTART_MINUTE_ACTUAL)
    ):
        config.set_last_restart_date(now.date())
        log_print(f"[GET_DATA] Daily restart time reached ({config.BOT_RESTART_HOUR_ACTUAL}:{config.BOT_RESTART_MINUTE_ACTUAL:02d})")
        restart_server("Daily scheduled restart")

    # Clear any stale popups
    send_keys("{ESC}")
    time.sleep(0.5)
    send_keys("{ESC}")
    time.sleep(0.5)

    # Heartbeat check — pause until portal reactivates
    active = _heartbeat()
    if active == "0":
        log_print("[GET_DATA] Bot deactivated by portal — killing Pioneer and entering wait loop")
        stop_recording()
        login.kill_pioneer()
        while _heartbeat() == "0":
            log_print("[GET_DATA] Still inactive — sleeping 5 minutes")
            time.sleep(300)
        log_print("[GET_DATA] Bot reactivated — restarting from login")
        start_recording()
        raise config.SystemException("Bot reactivated after pause")

    # Fetch next prescription from API
    transaction = prescription_api.fetch_next_prescription()

    if transaction is None:
        log_print("[GET_DATA] No prescriptions available")
        return None

    log_print(f"[GET_DATA] Claimed: Rx {transaction['rx_number']} | Drug: {transaction['drug_name']}")
    return transaction


def reset():
    """Reset state for next cycle (no persistent state needed with API approach)."""
    pass
