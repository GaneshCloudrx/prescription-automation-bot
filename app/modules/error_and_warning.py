"""
Error and Warning Module
Handles the Error/Warning List window that may appear after Save & Continue.
Returns (passed, non_bypassable) so the caller can decide next steps.
"""
import time
from pywinauto import Desktop
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


def handle_error_warning():
    """
    If the Error Warning List window appeared:
      1. Click Save & Continue (uxContinue) on it.
      2. If "Outstanding Errors" (non-bypassable) popup appears -> click OK,
         extract errors, cancel warning, return failure with error text.
      3. Otherwise warnings were bypassable -> return success.

    Returns:
        tuple: (success: bool, non_bypassable: bool, error_text: str)
    """
    global _app

    if not connect_to_pioneer():
        return False, False, ""

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)

        try:
            warning_win = window.child_window(title="Error  Warning List", control_type="Window")
            warning_win.wait("exists", timeout=config.TIMEOUT_POPUP_CHECK)
        except Exception:
            return True, False, ""

        log_print("[WARNING] Error Warning List window detected")

        save_btn = warning_win.child_window(auto_id="uxContinue", control_type="Button")
        save_btn.wait("enabled", timeout=config.TIMEOUT_ELEMENT_EXISTS)
        save_btn.click_input()
        log_print("Warning Save & Continue clicked")
        time.sleep(0.5)

        try:
            outstanding = warning_win.child_window(title="Outstanding Errors", control_type="Window")
            outstanding.wait("exists", timeout=config.TIMEOUT_POPUP_CHECK)
        except Exception:
            log_print("Warnings bypassed successfully")
            return True, False, ""

        log_print("[WARNING] Non-bypassable Outstanding Errors detected")
        ok_btn = outstanding.child_window(title="OK", control_type="Button")
        ok_btn.click_input()
        time.sleep(0.3)

        error_text = extract_error_list()

        cancel_btn = warning_win.child_window(auto_id="uxClose", control_type="Button")
        cancel_btn.click_input()
        log_print("Warning window cancelled")

        return False, True, error_text

    except Exception as e:
        log_print(f"Error handling warning window: {e}")
        _app = None
        return False, False, ""


def extract_error_list():
    """
    Extract all text from the uxErrorGrid DataGridView.
    Must be called while the Error Warning List window is open.

    Returns:
        str: All text from the error grid, or empty string on failure.
    """
    global _app

    if not connect_to_pioneer():
        return ""

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        warning_win = window.child_window(title="Error  Warning List", control_type="Window")
        if not warning_win.exists(timeout=1):
            return ""

        grid = warning_win.child_window(auto_id="uxErrorGrid", control_type="Table")
        all_text = []
        for cell in grid.descendants(control_type="Edit"):
            try:
                val = cell.legacy_properties().get("Value", "").strip()
                if val:
                    all_text.append(val)
            except Exception:
                pass
        joined = " | ".join(all_text)
        log_print(f"[WARNING] Error grid content: {joined}")
        return joined

    except Exception as e:
        log_print(f"Failed to extract error list: {e}")
        return ""


def _find_alerts_window():
    """
    Locate the Alerts window. It is nested inside the Fill Rx / Edit Rx window,
    so it cannot be reached with a top-level connect by title.

    Returns:
        WindowSpecification or None if the popup is not present.
    """
    try:
        parent = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        alerts_win = parent.child_window(title_re=r"Alerts -.*", control_type="Window")
        if alerts_win.exists(timeout=config.TIMEOUT_ELEMENT_EXISTS):
            return alerts_win
    except Exception as e:
        log_print(f"[ALERTS] Nested window lookup failed: {e}")

    try:
        alerts_win = Desktop(backend="uia").window(title_re=r"Alerts -.*")
        if alerts_win.exists(timeout=config.TIMEOUT_POPUP_CHECK):
            log_print("[ALERTS] Found Alerts window at top level")
            return alerts_win
    except Exception as e:
        log_print(f"[ALERTS] Top-level window lookup failed: {e}")

    return None


def _fill_alerts_captcha(alerts_win):
    """Copy the confirmation characters into the input box when the captcha is shown."""
    try:
        captcha_label = alerts_win.child_window(auto_id="uxConfirmCharacters", control_type="Text")
        if not captcha_label.exists(timeout=1):
            return
        captcha_text = captcha_label.window_text().strip()
        captcha_input = alerts_win.child_window(auto_id="uxConfirmationCharacters", control_type="Edit")
        captcha_input.set_edit_text(captcha_text)
        time.sleep(0.3)
        log_print(f"✓ Alerts captcha filled: '{captcha_text}'")
    except Exception as e:
        log_print(f"[ALERTS] Captcha step skipped: {e}")


def _save_continue_alerts(alerts_win):
    """
    Trigger Save & Continue on the Alerts popup.
    Clicks the uxSaveContinue button, falling back to the F12 shortcut.

    Returns:
        bool: True if either action was performed.
    """
    try:
        save_btn = alerts_win.child_window(auto_id="uxSaveContinue", control_type="Button")
        save_btn.wait("enabled", timeout=config.TIMEOUT_ELEMENT_EXISTS)
        save_btn.click_input()
        log_print("✓ Alerts popup — Save & Continue clicked")
        return True
    except Exception as e:
        log_print(f"[ALERTS] Save & Continue button not clickable: {e}")

    try:
        alerts_win.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{F12}")
        log_print("✓ Alerts popup — Save & Continue (F12) pressed")
        return True
    except Exception as e:
        log_print(f"[ALERTS] F12 fallback failed: {e}")
        return False


def handle_alerts_popup():
    """
    Handle the optional Alerts popup that may appear after saving.
    Returns True always (popup is optional).
    """
    global _app

    if not connect_to_pioneer():
        return True

    try:
        alerts_win = _find_alerts_window()
        if alerts_win is None:
            log_print("[ALERTS] Alerts popup not found")
            return True

        log_print("[ALERTS] Alerts popup detected")
        _fill_alerts_captcha(alerts_win)
        _save_continue_alerts(alerts_win)
        time.sleep(0.5)
    except Exception as e:
        log_print(f"[ALERTS] Error handling Alerts popup: {e}")
        _app = None

    return True


if __name__ == "__main__":
    #lets test the alerts popup
    success = handle_alerts_popup()
    if success:
        log_print("\n✓ TEST PASSED")
    else:
        log_print(f"\n✗ TEST FAILED")
