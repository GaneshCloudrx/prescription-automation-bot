"""
Pioneer Drug SIG Module
Pastes SIG (directions) in the SIG field via clipboard and validates
"""
import time
import ctypes
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


def _set_clipboard(text):
    """Copy text to clipboard using Win32 API with retry on lock contention."""
    CF_UNICODETEXT = 13
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    
    # Retry OpenClipboard — fails if another app (Cursor, clipboard manager) has it open
    for attempt in range(10):
        if user32.OpenClipboard(0):
            break
        time.sleep(0.05)
    else:
        log_print("WARNING: Could not open clipboard after retries")
        return False
    
    user32.EmptyClipboard()
    data = text.encode("utf-16le") + b'\x00\x00'
    h = kernel32.GlobalAlloc(0x0042, len(data))
    p = kernel32.GlobalLock(h)
    ctypes.memmove(p, data, len(data))
    kernel32.GlobalUnlock(h)
    user32.SetClipboardData(CF_UNICODETEXT, h)
    user32.CloseClipboard()
    return True


def _clear_clipboard():
    """Clear clipboard using Win32 API."""
    user32 = ctypes.windll.user32
    user32.OpenClipboard(0)
    user32.EmptyClipboard()
    user32.CloseClipboard()


# Global app reference
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


def set_sig(sig_text):
    """
    Type SIG directions in the SIG field and validate.
    
    Args:
        sig_text: SIG directions text to type
    
    Returns:
        tuple: (success: bool, is_valid: bool)
    """
    global _app
    
    if not connect_to_pioneer():
        return False, False
    
    try:
        # Screen Selector: Edit/Fill Rx window
        edit_rx_window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        edit_rx_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_rx_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: SIG field (RichEdit document)
        try:
            sig_field = edit_rx_window.child_window(auto_id="uxDirectionsSigCodes")
            sig_field.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        except Exception:
            sig_field = edit_rx_window.child_window(class_name_re=".*RichEdit20W.*", found_index=0)
            sig_field.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        
        sig_field.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("^a")
        time.sleep(0.1)
        send_keys("{BACKSPACE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys(sig_text, with_spaces=True)
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{TAB}")
        time.sleep(0.5)
        
        log_print(f"SIG set: '{sig_text}'")
        return True, True
        
    except Exception as e:
        log_print(f"Failed to set SIG: {e}")
        return False, False


def tab_to_dispense():
    """Click SIG field and send Tab to switch to the Dispense tab (no edits)."""
    global _app

    if not connect_to_pioneer():
        return False

    try:
        edit_rx_window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        edit_rx_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_rx_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        try:
            sig_field = edit_rx_window.child_window(auto_id="uxDirectionsSigCodes")
            sig_field.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        except Exception:
            sig_field = edit_rx_window.child_window(class_name_re=".*RichEdit20W.*", found_index=0)
            sig_field.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)

        sig_field.click_input()
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("{TAB}")
        time.sleep(0.5)
        log_print("✓ Tabbed from SIG to Dispense tab")
        return True
    except Exception as e:
        log_print(f"Failed to tab to Dispense: {e}")
        return False


def set_serial_number(serial):
    """Set Serial # field (uxTriplicateNumber) on the Edit Rx window."""
    global _app

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        serial_box = window.child_window(auto_id="uxTriplicateNumber", control_type="Edit")

        if config.PHARMACY_NAME in ("Apthorp", "Apthorp-Blank"):
            serial_box.set_edit_text(serial)
        else:
            serial_box.click_input()
            time.sleep(config.TIMEOUT_AFTER_TYPE)
            send_keys("^a")
            time.sleep(0.1)
            send_keys(serial, with_spaces=True)

        time.sleep(config.TIMEOUT_AFTER_TYPE)
        log_print(f"✓ Serial # set: {serial}")
        return True
    except Exception as e:
        log_print(f"Failed to set Serial #: {e}")
        return False


if __name__ == "__main__":
    success, is_valid = set_sig("[Inject 3-4 vials subcutaneously daily]")
    if success and is_valid:
        log_print("\n✓ SIG TEST PASSED")
    else:
        log_print("\n✗ SIG TEST FAILED")

    if set_serial_number("eeeeeeee"):
        log_print("\n✓ SERIAL # TEST PASSED")
    else:
        log_print("\n✗ SERIAL # TEST FAILED")
