"""
Pioneer Previous Active Fill Popup Handler
Clicks Cancel Fill if Previous Active Fill popup appears inside Fill Requests window
"""
import time
from pywinauto.application import Application
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


_app = None


def connect_to_pioneer():
    """Connect to running Pioneer."""
    global _app

    try:
        if _app is None:
            _app = Application(backend="uia").connect(
                title_re=".*(Fill Requests|Edit an Rx).*",
                timeout=config.TIMEOUT_POPUP_CHECK
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_cancel_fill():
    """
    Click Cancel Fill on Previous Active Fill popup if it appears.

    Returns:
        bool: True if cancelled successfully
    """
    global _app
    _app = None

    if not connect_to_pioneer():
        return False

    try:
        fill_requests_window = _app.window(title_re=".*(Fill Requests|Edit an Rx).*")
        active_fill_dialog = fill_requests_window.child_window(auto_id="RxRefillActiveFillDialog")
        if not active_fill_dialog.exists(timeout=0):
            return False

        cancel_button = active_fill_dialog.child_window(auto_id="uxCancelFill", control_type="Button")
        cancel_button.click_input()
        time.sleep(0.3)

        log_print("Previous Active Fill popup — Cancel Fill clicked")
        return True

    except Exception as e:
        log_print(f"Previous Active Fill popup check: {e}")
        return False


if __name__ == "__main__":
    if click_cancel_fill():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
