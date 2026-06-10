"""
Pioneer Drug Unit Module
Selects unit (EA/ML/GM) in the Edit Rx window based on substitute_drug_unit from API.

Logic:
- CT: Not a Pioneer unit. Quantity is typed as "dose ct" (e.g. "3 ct"). No unit selection.
- EA/ML/GM: Valid Pioneer units. Select from unit dropdown.
- Other: Unsupported — skip prescription.
"""
import time
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


# Global app reference
_app = None

# Valid unit options available in Pioneer's unit dropdown
VALID_UNITS = {"EA", "ML", "GM"}


def is_supported_unit(unit_value):
    """
    Check if the API unit is supported by the bot.
    
    Returns:
        True if unit is CT, EA, ML, or GM. False otherwise (bot should skip).
    """
    unit = str(unit_value).strip().upper() if unit_value else ""
    return unit in VALID_UNITS or unit == "CT"


def is_ct_unit(unit_value):
    """Check if unit is CT (needs dose appended with 'ct' instead of dropdown selection)."""
    return str(unit_value).strip().upper() == "CT" if unit_value else False


def connect_to_pioneer():
    """Connect to running Pioneer via shared cache."""
    global _app
    try:
        _app = get_pioneer_app()
        return True
    except Exception as e:
        log_print(f"[DRUG UNIT] Failed to connect: {e}")
        return False


def set_unit(unit_value):
    """
    Select unit from Pioneer's unit dropdown.
    Only call this for EA/ML/GM — NOT for CT.
    
    Args:
        unit_value: "EA", "ML", or "GM"
    
    Returns:
        tuple: (success: bool, is_valid: bool)
    """
    global _app
    
    if not connect_to_pioneer():
        return False, False
    
    unit = str(unit_value).strip().upper() if unit_value else ""
    if unit not in VALID_UNITS:
        log_print(f"[DRUG UNIT] Invalid unit for dropdown: '{unit_value}'")
        return False, False
    
    try:
        edit_rx_window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        edit_rx_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_rx_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        unit_combo = edit_rx_window.child_window(auto_id="uxQuantityPrescribedUnit", control_type="ComboBox")
        unit_field = unit_combo.child_window(class_name="Edit")
        unit_field.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{END}+{HOME}{DELETE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(unit)
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{DOWN}{ENTER}")
        time.sleep(0.5)
        
        log_print(f"[DRUG UNIT] Unit set: '{unit}'")
        return True, True
        
    except Exception as e:
        log_print(f"[DRUG UNIT] Failed to set unit: {e}")
        return False, False


if __name__ == "__main__":
    success, is_valid = set_unit("ML")
    if success and is_valid:
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
