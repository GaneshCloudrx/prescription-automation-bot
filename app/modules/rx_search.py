"""
Rx Search Module
Searches for a prescription by Rx number in Pioneer's Rx Profile search,
selects the result, and opens the Edit Rx screen.
"""
import time
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


_app = None


def _connect_to_pioneer():
    """Connect to Pioneer's main/Fill Requests window."""
    global _app
    try:
        _app = Application(backend="uia").connect(
            title_re=config.SELECTOR_FILL_REQUESTS,
            timeout=config.TIMEOUT_ELEMENT_VISIBLE,
        )
        return True
    except Exception as e:
        log_print(f"[RX SEARCH] Failed to connect: {e}")
        return False


def open_rx_search():
    """
    Open the Rx Profile search window.
    Navigates: Fill Requests -> Rx Profile search (Ctrl+R or via menu).

    Returns:
        bool: True if search window opened successfully
    """
    global _app

    if not _connect_to_pioneer():
        return False

    try:
        window = _app.window(title_re=config.SELECTOR_FILL_REQUESTS)
        window.wait("visible", timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # Use Ctrl+R to open Rx Profile search (standard Pioneer shortcut)
        send_keys("^r")
        time.sleep(1)

        log_print("[RX SEARCH] Rx Profile search opened")
        return True

    except Exception as e:
        log_print(f"[RX SEARCH] Failed to open Rx Profile search: {e}")
        return False


def search_by_rx_number(rx_number):
    """
    Enter Rx number in the search field and execute search.

    Args:
        rx_number: The prescription Rx number to search for

    Returns:
        tuple: (success: bool, found: bool)
    """
    global _app

    if not _app:
        if not _connect_to_pioneer():
            return False, False

    try:
        window = _app.window(title_re=config.SELECTOR_FILL_REQUESTS)
        window.wait("visible", timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # Type Rx number in the search/filter field
        rx_field = window.child_window(auto_id="uxRxNumber", control_type="Edit")
        rx_field.wait("visible", timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        rx_field.click_input()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        send_keys("^a")
        time.sleep(0.1)
        send_keys("{BACKSPACE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)

        send_keys(str(rx_number), with_spaces=True)
        time.sleep(config.TIMEOUT_AFTER_TYPE)

        send_keys("{ENTER}")
        time.sleep(config.TIMEOUT_AFTER_SEARCH)

        log_print(f"[RX SEARCH] Searched for Rx: {rx_number}")
        return True, True

    except Exception as e:
        log_print(f"[RX SEARCH] Search failed: {e}")
        return False, False


def select_prescription():
    """
    Select the first result from search and open the Edit Rx screen.
    Double-clicks the first row in the search results.

    Returns:
        bool: True if prescription selected and Edit Rx opened
    """
    global _app

    if not _app:
        if not _connect_to_pioneer():
            return False

    try:
        window = _app.window(title_re=config.SELECTOR_FILL_REQUESTS)
        window.wait("visible", timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        # Select the first row in search results
        first_row = window.child_window(title="Row 0", control_type="DataItem")
        first_row.wait("exists", timeout=config.TIMEOUT_SEARCH_WINDOW)
        first_row.click_input(double=True)
        time.sleep(1)

        log_print("[RX SEARCH] Prescription selected")
        return True

    except Exception as e:
        log_print(f"[RX SEARCH] Failed to select prescription: {e}")
        return False


def search_and_open_rx(rx_number):
    """
    Full workflow: open search, enter Rx number, select result, open Edit Rx.

    Args:
        rx_number: The prescription Rx number to search for

    Returns:
        tuple: (success: bool, found: bool)
    """
    if not open_rx_search():
        return False, False

    success, found = search_by_rx_number(rx_number)
    if not success or not found:
        log_print(f"[RX SEARCH] Rx {rx_number} not found")
        send_keys("{ESC}")
        time.sleep(0.5)
        return success, False

    if not select_prescription():
        log_print(f"[RX SEARCH] Failed to select Rx {rx_number}")
        send_keys("{ESC}")
        time.sleep(0.5)
        return False, False

    log_print(f"[RX SEARCH] Rx {rx_number} opened in Edit Rx")
    return True, True


if __name__ == "__main__":
    success, found = search_and_open_rx("12345678")
    if success and found:
        log_print("\nTEST PASSED")
    else:
        log_print("\nTEST FAILED")
