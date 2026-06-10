"""
Prescription API Module
Fetches prescription data from the drug substitution API (POST).
Includes retry logic with exponential backoff.
"""
import base64
import time
import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


USE_TEST_RESPONSE = False

# TEST_RESPONSE = {
#     "id": 3728,
#     "pioneer_rx_number": "1628995",
#     "original_drug_ndc": "78206012901",
#     "original_drug_name": "Apri 28 Day Tablet",
#     "original_drug_dose": "1 ct",
#     "original_is_compound": False,
#     "substitute_drug_ndc": "44087111501",
#     "substitute_drug_name": "Gonal-f RFF Redi-ject Pen 300 IU",
#     "substitute_drug_dose": "1 ct",
#     "substitute_is_compound": False,
#     "substitute_drug_qty": None,
#     "substitute_drug_sig": None,
#     "annotation": "Substituted Gonal-f RFF Redi-ject Pen 300 IU  from Apri 28 Day Tablet  per standing order on file",
# }


def _build_auth_header():
    """Build auth header using the pre-configured API_AUTH_HEADER."""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Basic {base64.b64encode(f'{config.PORTAL_USERNAME}:{config.PORTAL_PASSWORD}'.encode()).decode()}",
    }


def _parse_response(data):
    """
    Map API response fields to a standardized transaction dict.

    API response item:
    {
        "id": 12345,
        "pioneer_rx_number": "RX123456",
        "original_drug_ndc": "00002143380",
        "original_drug_name": "Gonal-F",
        "original_drug_dose": "3",
        "original_drug_unit": "CT",
        "original_is_compound": false,
        "substitute_drug_ndc": "00002143390",
        "substitute_drug_name": "Follistim",
        "substitute_is_compound": false,
        "substitute_drug_dose": "3",
        "substitute_drug_unit": "ML",
        "substitute_drug_sig": "Inject 225 IU subcutaneously daily",
        "annotation": "Substituted Follistim x 3 doses from Gonal-F x 3 doses per standing order on file"
    }
    """
    return {
        "api_id": data.get("id", ""),
        "rx_number": data.get("pioneer_rx_number", ""),
        "original_drug_ndc": data.get("original_drug_ndc", ""),
        "original_drug_name": data.get("original_drug_name", ""),
        "original_drug_dose": str(data.get("original_drug_dose", "")),
        "original_drug_unit": data.get("original_drug_unit", ""),
        "original_is_compound": bool(data.get("original_is_compound", False)),
        "substitute_drug_ndc": data.get("substitute_drug_ndc", ""),
        "substitute_drug_name": data.get("substitute_drug_name", ""),
        "substitute_drug_dose": str(data.get("substitute_drug_dose", "")),
        "substitute_drug_unit": data.get("substitute_drug_unit", ""),
        "substitute_is_compound": bool(data.get("substitute_is_compound", False)),
        "substitute_drug_sig": data.get("substitute_drug_sig") or "",
        "drug_ndc": data.get("substitute_drug_ndc", ""),
        "drug_name": data.get("substitute_drug_name", ""),
        "annotation": data.get("annotation") or "",
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
    # if USE_TEST_RESPONSE:
    #     log_print("[PRESCRIPTION API] Using TEST response (not calling API)")
    #     parsed = _parse_response(TEST_RESPONSE)
    #     log_print(
    #         f"[PRESCRIPTION API] Got Rx: {parsed['rx_number']} | "
    #         f"Substitute: {parsed['substitute_drug_name']} (NDC: {parsed['substitute_drug_ndc']}) | "
    #         f"Dose: {parsed['substitute_drug_dose']}"
    #     )
    #     return parsed

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
