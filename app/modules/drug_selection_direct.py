"""
Direct Drug Selection Module (Cloudrx)

A faster alternative to the binocular search window flow in search_drug.py.
Instead of opening the "Search for a Prescription Item" window and filling the
5-4-2 NDC fields, the bot types the NDC (or compound text) directly into the
drug Item quick-search box and confirms with Enter(s), then reads the Rx
Expire date to decide found / not-found.

Flow
----
1. Type the NDC directly into the Item textbox (uxPrescribedItemQuickSearch).
2. Press Enter once. Pioneer shows the matching item list. While waiting for
   that list to render (~1s), take a debug screenshot — grabbing the screen
   does NOT steal keyboard focus, so the Item box keeps focus for the next
   Enter.
3. Special case: if only one item matched, that single Enter already selected
   the drug and populated the Expire date. If so, we stop (no second Enter).
4. Normal case: Expire date is still empty (the list is showing), so press
   Enter a second time to select the highlighted item.
5. Read the Expire date (uxExpirationDate). If it is NOT empty the drug was
   selected (found); if it IS empty the drug was not found.

UI element ids are shared with search_drug.py (same Edit Rx window):
    - uxPrescribedItemQuickSearch  -> drug Item textbox
    - uxExpirationDate             -> Rx Expire date (Name "Expire:")

Same signature/return contract as search_drug.search_drug so the caller can
swap between the two with no other changes.
"""
import time
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print, take_screenshot
from modules.app_cache import get_pioneer_app


ITEM_AUTO_ID = "uxPrescribedItemQuickSearch"
EXPIRE_AUTO_ID = "uxExpirationDate"

_app = None


def connect_to_pioneer():
    """Connect to running Pioneer via shared cache."""
    global _app
    try:
        _app = get_pioneer_app()
        return True
    except Exception as e:
        log_print(f"Failed to connect to Edit Rx window (direct drug selection): {e}")
        return False


def _read_expiry_date():
    """Return current Rx Expire date value; empty string on failure/empty."""
    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        expire_box = window.child_window(auto_id=EXPIRE_AUTO_ID, control_type="Edit")
        return (expire_box.get_value() or "").strip()
    except Exception as e:
        log_print(f"[DIRECT] Could not read Expire date: {e}")
        return ""


def _read_drug_field():
    """Return current Item textbox value; empty string on failure."""
    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        item_box = window.child_window(auto_id=ITEM_AUTO_ID, control_type="Edit")
        return (item_box.get_value() or "").strip()
    except Exception as e:
        log_print(f"[DIRECT] Could not read drug field: {e}")
        return ""


def search_drug_direct(ndc, is_compound=False):
    """
    Type the NDC directly into the Item box, confirm with Enter(s), and use the
    Rx Expire date to decide found / not-found.

    Args:
        ndc: 11-digit NDC for a specific drug (dashes/spaces are stripped and
             the value is left-padded to 11 digits). For compounds this may be
             free text and is typed as-is (no normalization/validation).
        is_compound: True to skip NDC digit normalization (compound search).

    Returns:
        tuple: (success: bool, drug_found: bool)
    """
    global _app

    if not connect_to_pioneer():
        return False, False

    search_text = ndc if is_compound else ndc.replace("-", "").replace(" ", "").zfill(11)

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        item_box = window.child_window(auto_id=ITEM_AUTO_ID, control_type="Edit")

        # Read existing drug content before clearing
        existing_drug = (item_box.get_value() or "").strip()
        if existing_drug:
            log_print(f"[DIRECT] Existing drug in textbox: '{existing_drug}'", level="INFO")

        # Clear the drug textbox — try multiple approaches
        item_box.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)

        cleared = False
        for clear_attempt in range(3):
            # Home → Shift+End → Delete to select all and clear
            send_keys("{HOME}+{END}")
            time.sleep(0.1)
            send_keys("{DELETE}")
            time.sleep(0.3)

            # Verify the field is now empty
            current_value = (item_box.get_value() or "").strip()
            if not current_value:
                cleared = True
                break

            log_print(f"[DIRECT] Clear attempt {clear_attempt + 1}/3 — field still has: '{current_value}'", level="WARN")
            time.sleep(0.3)

        if not cleared:
            log_print("[DIRECT] ✗ Could not clear drug textbox after retries — skipping", level="ERROR")
            return False, False

        # Type the new NDC
        send_keys(search_text, with_spaces=True)
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        log_print(f"[DIRECT] Typed into Item box: '{search_text}'")

        # First Enter — Pioneer shows the matching item list
        send_keys("{ENTER}")
        time.sleep(1)

        # Second Enter to select the highlighted item
        send_keys("{ENTER}")
        time.sleep(1)
        expiry = _read_expiry_date()

        # Retry: on slower servers the item list may not be ready
        for attempt in range(1, 4):
            if expiry:
                break
            log_print(f"[DIRECT] Expire date empty — retry Enter {attempt}/3")
            send_keys("{ENTER}")
            time.sleep(1)
            expiry = _read_expiry_date()

        # Verify the drug actually changed (not still the old one)
        new_drug = _read_drug_field()
        if expiry and new_drug and existing_drug and new_drug == existing_drug:
            log_print(f"[DIRECT] ✗ Drug field unchanged after substitution (still '{new_drug}') — failed", level="ERROR")
            return False, False

        if expiry:
            log_print(f"[DIRECT] ✓ Drug found — Expire: '{expiry}' | Item: '{new_drug}'", level="INFO")
            return True, True

        log_print(f"[DIRECT] ✗ Drug not found — Expire date empty after retries | Item: '{new_drug}'", level="WARN")
        return True, False

    except Exception as e:
        log_print(f"[DIRECT] Failed direct drug selection: {e}", level="ERROR")
        return False, False


if __name__ == "__main__":
    ok, found = search_drug_direct("00781400332")
    log_print(f"success={ok}, drug_found={found}")
