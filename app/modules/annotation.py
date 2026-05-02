"""
Annotation Module
Clicks the pencil/edit icon on the Edit Rx screen to open the annotation popup,
types the annotation text from the API response, and saves/closes the popup.
"""
import time
import ctypes
from pywinauto.keyboard import send_keys
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


def _set_clipboard(text):
    """Copy text to clipboard using Win32 API."""
    CF_UNICODETEXT = 13
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    user32.OpenClipboard(0)
    user32.EmptyClipboard()
    data = text.encode("utf-16le") + b'\x00\x00'
    h = kernel32.GlobalAlloc(0x0042, len(data))
    p = kernel32.GlobalLock(h)
    ctypes.memmove(p, data, len(data))
    kernel32.GlobalUnlock(h)
    user32.SetClipboardData(CF_UNICODETEXT, h)
    user32.CloseClipboard()


def _clear_clipboard():
    """Clear clipboard using Win32 API."""
    user32 = ctypes.windll.user32
    user32.OpenClipboard(0)
    user32.EmptyClipboard()
    user32.CloseClipboard()


_app = None


def connect_to_pioneer():
    """Connect to running Pioneer via shared cache."""
    global _app
    try:
        _app = get_pioneer_app()
        return True
    except Exception as e:
        log_print(f"[ANNOTATION] Failed to connect: {e}")
        return False


def add_annotation(annotation_text):
    """
    Click the pencil/edit icon on the Edit Rx screen to open the annotation popup,
    type the annotation text, and save/close the popup.

    Args:
        annotation_text: The annotation text to enter (from API response)

    Returns:
        bool: True if annotation added successfully
    """
    global _app

    if not annotation_text or not annotation_text.strip():
        log_print("[ANNOTATION] No annotation text provided — skipping")
        return True

    if not connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait("visible", timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # Click the pencil/edit icon to open annotation popup
        # Try common auto_id patterns for annotation buttons
        pencil_btn = None
        for auto_id in ("uxAnnotationEdit", "uxEditAnnotation", "uxAnnotation", "uxNotes"):
            try:
                pencil_btn = window.child_window(auto_id=auto_id, control_type="Button")
                if pencil_btn.exists(timeout=1):
                    break
                pencil_btn = None
            except Exception:
                pencil_btn = None

        if pencil_btn is None:
            # Fallback: search by title containing "annotation" or pencil-related text
            for btn in window.descendants(control_type="Button"):
                try:
                    title = btn.window_text().strip().lower()
                    if "annot" in title or "note" in title or "edit" in title:
                        pencil_btn = btn
                        break
                except Exception:
                    continue

        if pencil_btn is None:
            log_print("[ANNOTATION] Pencil/edit icon not found — skipping annotation")
            return False

        pencil_btn.click_input()
        time.sleep(1)
        log_print("[ANNOTATION] Pencil icon clicked — annotation popup opened")

        # Type annotation text in the popup
        # The popup should now be the active window/dialog
        try:
            _set_clipboard(annotation_text)
            send_keys("^v")
        finally:
            _clear_clipboard()
        time.sleep(config.TIMEOUT_AFTER_TYPE)

        log_print(f"[ANNOTATION] Annotation text entered: '{annotation_text[:50]}...'")

        # Save and close the annotation popup
        # Try clicking Save/OK button, or use keyboard shortcuts
        try:
            popup = window.child_window(title_re=".*Annotation.*|.*Note.*", control_type="Window")
            if popup.exists(timeout=1):
                save_btn = popup.child_window(title_re=".*Save.*|.*OK.*", control_type="Button")
                if save_btn.exists(timeout=1):
                    save_btn.click_input()
                    time.sleep(0.5)
                    log_print("[ANNOTATION] Annotation saved via button")
                    return True
        except Exception:
            pass

        # Fallback: Tab to OK/Save and press Enter
        send_keys("{TAB}")
        time.sleep(0.3)
        send_keys("{ENTER}")
        time.sleep(0.5)

        log_print("[ANNOTATION] Annotation saved")
        return True

    except Exception as e:
        log_print(f"[ANNOTATION] Failed to add annotation: {e}")
        return False


if __name__ == "__main__":
    if add_annotation("Test annotation from bot"):
        log_print("\nTEST PASSED")
    else:
        log_print("\nTEST FAILED")
