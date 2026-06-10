"""
Annotation Module
1. Click pencil icon on Edit Rx toolbar (mainToolStrip) — 75px from left
2. "Annotate an Image" window opens
3. Click "Add Note" icon on its toolbar (toolStrip1) — 10px from left
4. Paste annotation text
5. Click "Save F12" button (uxSave) on the Annotate window

"""
import time
import subprocess
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
from pywinauto import mouse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


def _set_clipboard(text):
    """Copy text to clipboard using PowerShell Set-Clipboard."""
    subprocess.run(
        ["powershell", "-Command", f"Set-Clipboard -Value '{text}'"],
        check=True, timeout=5
    )


def _clear_clipboard():
    """Clear clipboard using PowerShell."""
    subprocess.run(
        ["powershell", "-Command", "Set-Clipboard -Value ' '"],
        timeout=5
    )


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
    Open annotation window, click Add Note, type text, save.

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
        # Pre-load clipboard BEFORE opening annotation window
        _set_clipboard(annotation_text)
        log_print("[ANNOTATION] Clipboard loaded with annotation text")

        window = _app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait("visible", timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # Step 1: Click pencil icon on Edit Rx toolbar (75px from left edge)
        toolbar = window.child_window(auto_id="mainToolStrip", control_type="ToolBar")
        toolbar.wait("visible", timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        rect = toolbar.rectangle()
        pencil_x = rect.left + 75
        pencil_y = (rect.top + rect.bottom) // 2

        mouse.click(coords=(pencil_x, pencil_y))
        time.sleep(1.5)
        log_print(f"[ANNOTATION] Pencil icon clicked at ({pencil_x}, {pencil_y})")

        # Step 2: Find annotation toolbar inside the Edit Rx window
        # Step 3: Click "Add Note" icon on annotation toolbar (10px from left edge)
        note_toolbar = window.child_window(auto_id="toolStrip1", control_type="ToolBar")
        note_toolbar.wait("visible", timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        note_rect = note_toolbar.rectangle()
        note_x = note_rect.left + 20
        note_y = (note_rect.top + note_rect.bottom) // 2

        mouse.click(coords=(note_x, note_y))
        time.sleep(1)
        log_print(f"[ANNOTATION] Add Note icon clicked at ({note_x}, {note_y})")

        # Step 3: Directly Ctrl+V (clipboard already loaded)
        send_keys("^v")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        log_print(f"[ANNOTATION] Annotation text pasted: '{annotation_text[:60]}...'")

        # Step 4: Save annotation using F12 shortcut (avoids duplicate uxSave button issue)
        send_keys("{F12}")
        time.sleep(1)
        log_print("[ANNOTATION] F12 Save pressed")

        # Step 5: Handle "Save Image" popup — click Yes (Alt+Y)
        send_keys("%y")
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        log_print("[ANNOTATION] Save Image popup confirmed (Yes)")
        return True

    except Exception as e:
        log_print(f"[ANNOTATION] Failed to add annotation: {e}")
        return False
    finally:
        try:
            _clear_clipboard()
        except Exception:
            pass


if __name__ == "__main__":
    if add_annotation("Test annotation from bot"):
        log_print("\nTEST PASSED")
    else:
        log_print("\nTEST FAILED")
