"""
Pioneer Drug Search Module
Opens drug search, fills NDC fields, searches, and selects first result or cancels
"""
import time
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


_app = None


def connect_to_pioneer():
    """Connect to running Pioneer via shared cache."""
    global _app
    try:
        _app = get_pioneer_app()
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def get_item_text():
    """Return the current text of the Item (drug) textbox, or empty string on failure."""
    global _app

    if not connect_to_pioneer():
        return ""

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        item_box = window.child_window(auto_id="uxPrescribedItemQuickSearch", control_type="Edit")
        text = (item_box.get_value() or "").strip()
        log_print(f"Item textbox value: '{text}'")
        return text
    except Exception as e:
        log_print(f"Failed to read item textbox: {e}")
        return ""


def select_item_from_dropdown():
    """Remove last char from Item textbox and press Enter twice to trigger item selection popup."""
    global _app

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        item_box = window.child_window(auto_id="uxPrescribedItemQuickSearch", control_type="Edit")
        item_box.click_input()
        time.sleep(0.3)
        send_keys("{END}")
        time.sleep(0.3)
        send_keys("{BACKSPACE}")
        time.sleep(0.5)
        send_keys("{ENTER}")
        time.sleep(3)
        send_keys("{ENTER}")
        time.sleep(3)
        send_keys("{ENTER}")
        time.sleep(1)
        #Comment out the following line:
        #from pywinauto import mouse
        #mouse.double_click(coords=(498, 619))
        #time.sleep(2)

        log_print("✓ Item selected via textbox")
        return True
    except Exception as e:
        log_print(f"Failed to select item from dropdown: {e}")
        return False


def search_drug(ndc):
    """
    Click drug binocular, split 11-digit NDC into 5-4-2, search, and select first row.
    If not found, click Cancel.

    Args:
        ndc: 11-digit NDC string (e.g. "00781400332")

    Returns:
        tuple: (success: bool, drug_found: bool)
    """
    global _app

    if not connect_to_pioneer():
        return False, False

    ndc = ndc.replace("-", "").zfill(11)

    try:
        # Step 1: Click binocular search button on Edit Rx window
        edit_window = _app.window(title_re=".*(Edit|Fill Rx|Search For a Prescriber|Search for a Patient|Fill Requests).*")
        edit_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        search_icon = edit_window.child_window(auto_id="AdvancedSearchButton", title="Expire:", control_type="Button")
        search_icon.click_input()
        time.sleep(0.5)
        log_print("✓ Drug search binocular clicked")

        # Step 2: Wait for drug search window
        search_window = _app.window(title_re=config.SELECTOR_SEARCH_DRUG)
        search_window.wait('visible', timeout=config.TIMEOUT_SEARCH_WINDOW)
        search_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        log_print("✓ Drug search window visible")

        # Step 3: Fill NDC fields (5-4-2 split) under "NDC:" pane
        ndc_pane = search_window.child_window(title="NDC:", control_type="Pane")
        ndc_pane.child_window(auto_id="uxFirstEntry", control_type="Edit").set_edit_text(ndc[:5])
        ndc_pane.child_window(auto_id="uxMiddleEntry", control_type="Edit").set_edit_text(ndc[5:9])
        ndc_pane.child_window(auto_id="uxLastEntry", control_type="Edit").set_edit_text(ndc[9:11])
        log_print(f"✓ NDC entered: {ndc[:5]}-{ndc[5:9]}-{ndc[9:11]}")

        # Click Search
        search_window.child_window(auto_id="uxSearch", control_type="Button").click_input()
        time.sleep(config.TIMEOUT_AFTER_SEARCH)
        log_print("✓ Search clicked")

        # Step 3b: Check for first row and double-click, or cancel
        try:
            first_row = search_window.child_window(title="Table row 1", control_type="Custom")
            first_row.wait('exists', timeout=15)
            first_row.click_input(double=True)
            time.sleep(0.5)
            send_keys("{ENTER}")
            time.sleep(0.3)
            log_print("✓ Drug selected")
            return True, True

        except Exception:
            log_print("✗ Drug not found")
            send_keys("{ESC}")
            time.sleep(config.TIMEOUT_AFTER_CLICK)
            log_print("Cancel clicked")
            return True, False

    except Exception as e:
        log_print(f"Failed drug search: {e}")
        return False, False


if __name__ == "__main__":
    item_text = get_item_text()
    if item_text:
        log_print(f"\n✓ TEST PASSED (item_text={item_text})")
    else:
        log_print("\n✗ TEST FAILED")
