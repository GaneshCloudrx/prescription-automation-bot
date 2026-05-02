"""
Pioneer Reminder Popup Handler
Clicks Dismiss All if Reminder popup appears inside Fill Requests window
"""
import time
from pywinauto.application import Application
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


# Global app reference
_app = None


def connect_to_pioneer():
    """Connect to running Pioneer."""
    global _app
    
    try:
        if _app is None:
            _app = Application(backend="uia").connect(
                title_re=".*(Fill Requests|Edit an Rx).*",
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_dismiss_all():
    """
    Click Dismiss All button if Reminder popup appears.
    
    Returns:
        bool: True if dismissed successfully
    """
    global _app
    _app = None

    if not connect_to_pioneer():
        return False
    
    try:
        fill_requests_window = _app.window(title_re=".*(Fill Requests|Edit an Rx).*")
        dismiss_button = fill_requests_window.child_window(auto_id="uxDismissAll", control_type="Button")
        if not dismiss_button.exists(timeout=0):
            return False
        dismiss_button.click_input()
        time.sleep(0.3)
        
        log_print("✓ Reminder dismissed")
        return True
        
    except Exception as e:
        log_print(f"Failed to dismiss reminder: {e}")
        return False


if __name__ == "__main__":
    if click_dismiss_all():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
