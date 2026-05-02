"""
Pioneer Drug Fill Popup Handler
Dismisses 'Choose Drug Dispensed' popup if it appears
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


def dismiss_drugfill_popup():
    """
    Send ESC if 'Choose Drug Dispensed' popup appears.

    Returns:
        bool: True if dismissed, False if not found
    """
    global _app

    if not connect_to_pioneer():
        return False

    try:
        edit_rx_window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        dialog = edit_rx_window.child_window(auto_id="RxDispensedItemDialog")
        if not dialog.exists(timeout=config.TIMEOUT_POPUP_CHECK):
            return False

        dialog.set_focus()
        time.sleep(0.2)
        send_keys("{ESC}")
        time.sleep(0.3)

        log_print("Choose Drug Dispensed popup dismissed")
        return True

    except Exception as e:
        log_print(f"Drug fill popup check: {e}")
        return False


if __name__ == "__main__":
    if dismiss_drugfill_popup():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
