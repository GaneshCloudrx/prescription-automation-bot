"""
Update Status API Module
Calls update status endpoint for three outcomes: skipped, completed, failed.
Payload format: {"id": <int>, "status": "<status>", "remarks": "<details>"}
"""
import base64
import time
import requests
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print

API_UPDATE_ENDPOINT = config.API_UPDATE_ENDPOINT


def _call_update_api(payload, max_retries=config.MAX_API_RETRIES):
    """
    POST payload to the update status endpoint with retry logic.

    Args:
        payload: dict with id, status, remarks
        max_retries: number of retry attempts

    Returns:
        bool: True if API acknowledged successfully
    """
    if not payload.get("id"):
        log_print("[UPDATE API] Skipped — no id available")
        return False

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {base64.b64encode(f'{config.PORTAL_USERNAME}:{config.PORTAL_PASSWORD}'.encode()).decode()}",
    }

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = 2 * (2 ** (attempt - 1))
                log_print(f"[UPDATE API] Retry {attempt + 1}/{max_retries} after {delay}s...")
                time.sleep(delay)

            log_print(f"[UPDATE API] Sending payload: {payload}")
            response = requests.post(
                API_UPDATE_ENDPOINT, json=payload, headers=headers,
                timeout=config.API_TIMEOUT
            )

            result = response.json()
            status = str(result.get("status", "")).upper()
            log_print(f"[UPDATE API] Response: {result}")
            return status == "SUCCESS"

        except requests.exceptions.Timeout:
            log_print(f"[UPDATE API] Timeout (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.RequestException as e:
            log_print(f"[UPDATE API] Request failed: {e} (attempt {attempt + 1}/{max_retries})")

    log_print(f"[UPDATE API] All {max_retries} attempts failed")
    return False


def update_skipped(api_id, remarks="skipped", screenshot_path=None):
    """
    Mark Rx as skipped.

    Args:
        api_id: record id from prescription API response
        remarks: reason for skipping

    Returns:
        bool: True if acknowledged
    """
    payload = {
        "id": api_id,
        "status": "skipped",
        "remarks": remarks,
    }
    log_print(f"[UPDATE API] Sending SKIPPED — {remarks}")
    return _call_update_api(payload)


def update_success(api_id, screenshot_path=None):
    """
    Mark Rx as successfully completed.

    Args:
        api_id: record id from prescription API response

    Returns:
        bool: True if acknowledged
    """
    payload = {
        "id": api_id,
        "status": "completed",
        "remarks": "Drug substituted successfully in PioneerRx",
    }
    log_print("[UPDATE API] Sending SUCCESS")
    return _call_update_api(payload)


def update_failed(api_id, remarks="failed"):
    """
    Mark Rx as failed due to an exception.

    Args:
        api_id: record id from prescription API response
        remarks: error description

    Returns:
        bool: True if acknowledged
    """
    payload = {
        "id": api_id,
        "status": "failed",
        "remarks": remarks[:500],
    }
    log_print(f"[UPDATE API] Sending FAILED — {remarks}")
    return _call_update_api(payload)
