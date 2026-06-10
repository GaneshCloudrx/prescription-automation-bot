"""
Pioneer Dispense Module
Fills Dispense Quantity, Days Supply, and RPh fields and validates each
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


def set_dispense(quantity, days_supply, rph):
    """
    Fill Dispense Quantity, Days Supply, and RPh fields and validate.

    Args:
        quantity:    Dispensed quantity value
        days_supply: Days supply value
        rph:         Pharmacist (RPh) name

    Returns:
        tuple: (success: bool, all_valid: bool)
    """
    global _app

    if not connect_to_pioneer():
        return False, False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # --- 1. Dispense Quantity (auto_id: uxDispensedQuantity) ---
        if quantity:
            qty_field = window.child_window(auto_id="uxDispensedQuantity", control_type="Edit")
            qty_field.click_input()
            time.sleep(config.TIMEOUT_AFTER_TYPE)
            send_keys("{END}+{HOME}{DELETE}")
            time.sleep(config.TIMEOUT_AFTER_TYPE)
            send_keys(str(quantity))
            time.sleep(config.TIMEOUT_AFTER_CLICK)
            send_keys("{TAB}")
            time.sleep(config.TIMEOUT_AFTER_CLICK)
            log_print(f"Dispense Quantity: '{quantity}'")

        # --- 2. Days Supply (auto_id: uxDaysSupply) ---
        ds_field = window.child_window(auto_id="uxDaysSupply", control_type="Edit")
        ds_field.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{END}+{HOME}{DELETE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(str(days_supply))
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{TAB}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        log_print(f"Days Supply: '{days_supply}'")

        # --- 3. RPh (Win32 Edit inside "RPh:" ComboBox, auto_id: 1001) ---
        rph_combo = window.child_window(title="RPh:", control_type="ComboBox")
        rph_edit = rph_combo.child_window(auto_id="1001", control_type="Edit")
        rph_edit.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{END}+{HOME}{DELETE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(str(rph), with_spaces=True)
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{DOWN}{TAB}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        log_print(f"Dispense: ALL SET")
        return True, True

    except Exception as e:
        log_print(f"Failed to set dispense fields: {e}")
        return False, False


def set_rph(rph=None):
    """
    Select the pharmacist (RPh) in the RPh ComboBox on the Edit Rx window.
    Uses config.PHARMACIST_NAME if no rph argument is provided.

    Returns:
        bool: True if RPh set successfully
    """
    global _app
    _app = None

    if not rph:
        rph = config.PHARMACIST_NAME
    if not rph:
        log_print("[DISPENSE] No pharmacist name configured — skipping RPh")
        return True

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        rph_combo = window.child_window(title="RPh:", control_type="ComboBox")
        rph_edit = rph_combo.child_window(auto_id="1001", control_type="Edit")
        rph_edit.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{END}+{HOME}{DELETE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(str(rph), with_spaces=True)
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{DOWN}{TAB}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        log_print(f"[DISPENSE] RPh set to: {rph}")
        return True

    except Exception as e:
        log_print(f"[DISPENSE] Failed to set RPh: {e}")
        return False


def clear_secondary_insurance():
    """Set Secondary insurance to <None> to resolve Third Party errors."""
    global _app
    _app = None

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        sec_combo = window.child_window(title="Secondary:", control_type="ComboBox")
        sec_edit = sec_combo.child_window(auto_id="1001", control_type="Edit")
        sec_edit.click_input()
        time.sleep(0.2)
        send_keys("{END}+{HOME}{DELETE}")
        time.sleep(0.2)
        send_keys("<None>", with_spaces=True)
        time.sleep(0.3)
        send_keys("{TAB}")
        time.sleep(0.5)
        log_print("Secondary insurance set to <None>")
        return True

    except Exception as e:
        log_print(f"Failed to set secondary insurance: {e}")
        return False


def toggle_daw():
    """Toggle the DAW checkbox."""
    global _app
    _app = None

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        daw_checkbox = window.child_window(auto_id="uxDawCode", control_type="CheckBox")
        daw_checkbox.click_input()
        time.sleep(0.3)
        log_print("DAW checkbox toggled")
        return True

    except Exception as e:
        log_print(f"Failed to toggle DAW: {e}")
        return False


if __name__ == "__main__":
    if toggle_daw():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
