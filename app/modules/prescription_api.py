"""
Prescription API Module
Fetches prescription data from the drug substitution API (POST).
Includes retry logic with exponential backoff.
"""
import time
import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


def _build_auth_header():
    """Build auth header using the pre-configured API_AUTH_HEADER."""
    return {
        "Content-Type": "application/json",
        "Authorization": config.API_AUTH_HEADER,
    }


def _parse_response(data):
    """
    Map API response fields to a standardized transaction dict.

    API response item:
    {
        "id": 101,
        "pioneer_rx_number": "RX123456",
        "original_drug_ndc": "00052031301",
        "original_drug_name": "Follistim AQ 600 IU",
        "original_drug_dose": 1,
        "substitute_drug_ndc": "44087111501",
        "substitute_drug_name": "Gonal-F 450 IU",
        "substitute_drug_dose": 2,
        "sig": "Inject 0.5ml subcutaneously daily",
        "annotation": "Substituted per physician approval"
    }
    """
    return {
        "api_id": data.get("id", ""),
        "rx_number": data.get("pioneer_rx_number", ""),
        "original_drug_ndc": data.get("original_drug_ndc", ""),
        "original_drug_name": data.get("original_drug_name", ""),
        "original_drug_dose": data.get("original_drug_dose", ""),
        "substitute_drug_ndc": data.get("substitute_drug_ndc", ""),
        "substitute_drug_name": data.get("substitute_drug_name", ""),
        "substitute_drug_dose": str(data.get("substitute_drug_dose", "")),
        "drug_ndc": data.get("substitute_drug_ndc", ""),
        "drug_name": data.get("substitute_drug_name", ""),
        "sig": data.get("sig", ""),
        "annotation": data.get("annotation", ""),
        "is_compound": bool(data.get("is_compound", False)),
        "raw_response": data,
    }


def fetch_next_prescription(max_retries=config.MAX_API_RETRIES):
    """
    Fetch the next prescription to process from the API via POST.

    Returns:
        dict: Parsed transaction data, or None if no records available.

    Raises:
        config.SystemException: If all retry attempts fail with a non-recoverable error.
    """
    headers = _build_auth_header()
    payload = {
        "server_name": config.MACHINE_NAME,
        "bot_name": config.HEARTBEAT_BOT_NAME,
    }

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = 2 * (2 ** (attempt - 1))
                log_print(f"[PRESCRIPTION API] Retry {attempt + 1}/{max_retries} after {delay}s...")
                time.sleep(delay)

            log_print(f"[PRESCRIPTION API] Fetching next prescription (attempt {attempt + 1}/{max_retries})...")
            response = requests.post(
                config.PRESCRIPTION_API_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=config.API_TIMEOUT,
            )
            log_print(f"[PRESCRIPTION API] Response: {response.text}")

            if response.status_code == 200:
                result = response.json()
                status = str(result.get("status", "")).upper()

                if status == "SUCCESS":
                    data = result.get("data")
                    if not data:
                        log_print("[PRESCRIPTION API] No records available")
                        return None

                    if isinstance(data, list):
                        data = data[0] if data else None
                    if not data:
                        log_print("[PRESCRIPTION API] Empty data in response")
                        return None

                    parsed = _parse_response(data)
                    log_print(
                        f"[PRESCRIPTION API] Got Rx: {parsed['rx_number']} | "
                        f"Substitute: {parsed['substitute_drug_name']} (NDC: {parsed['substitute_drug_ndc']}) | "
                        f"Dose: {parsed['substitute_drug_dose']}"
                    )
                    return parsed

                elif status in ("NO_RECORDS", "EMPTY"):
                    log_print("[PRESCRIPTION API] No records available")
                    return None
                else:
                    log_print(f"[PRESCRIPTION API] Unexpected status: {status} | Response: {result}")
                    return None
            else:
                log_print(f"[PRESCRIPTION API] HTTP {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            log_print(f"[PRESCRIPTION API] Timeout (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.RequestException as e:
            log_print(f"[PRESCRIPTION API] Request failed: {e} (attempt {attempt + 1}/{max_retries})")

    log_print(f"[PRESCRIPTION API] All {max_retries} attempts failed")
    raise config.SystemException("Failed to fetch prescription data from API after all retries")


if __name__ == "__main__":
    result = fetch_next_prescription()
    if result:
        log_print(f"\nTEST PASSED | Rx: {result['rx_number']}")
    else:
        log_print("\nNo records returned")
