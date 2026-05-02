"""
Pioneer Rx In Use Popup Handler
Clicks Cancel if Rx In Use popup appears inside Fill Requests window
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
                title_re=config.SELECTOR_FILL_REQUESTS,
                timeout=config.TIMEOUT_POPUP_CHECK
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_cancel_rxinuse():
    """
    Click Cancel on Rx In Use popup if it appears.
    
    Returns:
        bool: True if cancelled successfully
    """
    global _app
    _app = None

    if not connect_to_pioneer():
        return False
    
    try:
        fill_requests_window = _app.window(title_re=config.SELECTOR_FILL_REQUESTS)
        rxinuse_dialog = fill_requests_window.child_window(auto_id="RxQueueItemCollectionLockPromptDialog")
        if not rxinuse_dialog.exists(timeout=0):
            return False
        
        cancel_button = rxinuse_dialog.child_window(auto_id="uxCancel", control_type="Button")
        cancel_button.click_input()
        time.sleep(0.3)
        
        log_print("Rx In Use popup cancelled")
        return True
        
    except Exception as e:
        log_print(f"Rx In Use popup check: {e}")
        return False


if __name__ == "__main__":
    if click_cancel_rxinuse():
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
