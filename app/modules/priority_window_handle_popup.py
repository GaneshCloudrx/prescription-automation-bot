"""
Pioneer Priority Window Popup Handler
Clicks Cancel if a Priority popup window appears
"""
import time
from pywinauto.application import Application
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


def click_cancel_priority():
    """
    Click Cancel - ESC button if Priority popup window appears.
    
    Returns:
        bool: True if cancelled or window not found (no action needed)
    """
    global _app
    
    if not connect_to_pioneer():
        return False
    
    try:
        edit_rx_window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        priority_dialog = edit_rx_window.child_window(auto_id="RxPromiseTimeDialog")
        if not priority_dialog.exists(timeout=2):
            return False
        
        cancel_button = priority_dialog.child_window(auto_id="uxCancel", control_type="Button")
        cancel_button.click_input()
        time.sleep(0.3)
        
        log_print("Priority popup cancelled")
        return True
        
    except Exception as e:
        log_print(f"Priority popup check: {e}")
        return False


if __name__ == "__main__":
    if click_cancel_priority():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
