"""
Pioneer Add Patient Condition Wizard Popup Handler
Dismisses the "Add Patient Condition Wizard" popup by clicking Cancel if it appears.
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
                title_re=".*(Fill Requests|Edit|Fill Rx).*",
                timeout=config.TIMEOUT_POPUP_CHECK
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def dismiss_wizard_popup():
    """
    Check if the "Add Patient Condition Wizard" popup is visible.
    If so, click the Cancel button to dismiss it.

    Returns:
        tuple: (success: bool, was_dismissed: bool)
    """
    global _app
    _app = None

    if not connect_to_pioneer():
        return False, False

    try:
        main_window = _app.window(title_re=".*(Fill Requests|Edit|Fill Rx).*")
        wizard_popup = main_window.child_window(title="Add Patient Condition Wizard", control_type="Window")
        if not wizard_popup.exists(timeout=0):
            log_print("No wizard popup found — skipping")
            return True, False

        cancel_btn = wizard_popup.child_window(auto_id="uxCancel", control_type="Button")
        cancel_btn.click_input()
        time.sleep(0.3)

        log_print("Wizard popup dismissed")
        return True, True

    except Exception as e:
        log_print(f"Wizard popup check: {e}")
        return False, False


if __name__ == "__main__":
    success, dismissed = dismiss_wizard_popup()
    if success:
        log_print(f"\n✓ TEST PASSED (dismissed={dismissed})")
    else:
        log_print("\n✗ TEST FAILED")
