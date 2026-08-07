"""
Process State - Orchestrate all modules for one prescription
Flow: Search Rx -> Select drug -> Set quantity -> Set SIG -> Add annotation -> Save -> Handle popups
Raises BusinessRuleException for expected errors, SystemException for unexpected
"""
import sys
import os
import time

from pywinauto.keyboard import send_keys
from pywinauto.application import Application
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modules.helper import log_print, take_screenshot, force_foreground, ensure_session_active

from modules import (
    app_cache,
    rx_search,
    drugtype_selection, search_drug, drug_selection_direct,
    drug_quantity, drug_unit, drug_sig,
    annotation,
    dispense,
    save_and_continue, equivalent_rx,
    error_and_warning, cancel_prescription,
    update_api,
    # Popup handlers
    priority_window_handle_popup,
    rxinuse_popup,
    drugfill_popup,
    renewable_request,
    wizard_add_patient_popup,
    reminder,
    converted_data_popup,
    previous_active_fill_popup,
    noactiveitem_,
    critical_warning,
)


def _add_to_retry(rx_number):
    """Append Rx number to today's retry file."""
    os.makedirs(os.path.dirname(config.RETRY_FILE_PATH), exist_ok=True)
    with open(config.RETRY_FILE_PATH, "a") as f:
        f.write(str(rx_number) + "\n")


def _ensure_pioneer_foreground():
    """Connect to Pioneer and force it to the foreground before critical UI steps."""
    try:
        app = Application(backend="uia").connect(
            title_re=config.SELECTOR_FILL_REQUESTS,
            timeout=config.TIMEOUT_ELEMENT_VISIBLE,
        )
        window = app.window(title_re=config.SELECTOR_FILL_REQUESTS)
        force_foreground(window.handle)
        ensure_session_active()
    except Exception as e:
        log_print(f"[PROCESS] Focus recovery warning: {e}")


def _click_image_tab():
    """Click the 'Image [2]' tab on the Edit Rx window to switch from Dispense to Image."""
    try:
        app = app_cache.get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait("visible", timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        image_tab = window.child_window(title_re="Image.*", control_type="TabItem")
        image_tab.click_input()
        time.sleep(1)
        log_print("[PROCESS] Image tab clicked")
    except Exception as e:
        log_print(f"[PROCESS] Failed to click Image tab: {e}")


def _handle_popups():
    """Dismiss any popups that may appear after opening an Rx."""
    for handler in [
        priority_window_handle_popup.click_cancel_priority,
        #wizard_add_patient_popup.dismiss_wizard_popup,
        #rxinuse_popup.click_cancel_rxinuse,
        #renewable_request.click_cancel_renew,
        #reminder.click_dismiss_all,
        #converted_data_popup.click_ok_conversion,
        #previous_active_fill_popup.click_cancel_fill,
    ]:
        try:
            handler()
        except Exception:
            pass


def run(transaction, api_response):
    """
    Process a single prescription transaction.

    Args:
        transaction: dict from prescription_api with keys:
            (api_id, rx_number, drug_ndc, drug_name, substitute_drug_dose,
             sig, annotation, is_compound, raw_response)
        api_response: unused (kept for state machine compatibility)

    Raises:
        config.BusinessRuleException: Rx/Drug not found, etc.
        config.SystemException: App crash, timeout, element not found
    """
    app_cache.reset()

    rx_number = transaction["rx_number"]
    drug_ndc = transaction.get("drug_ndc", "")
    quantity = transaction.get("substitute_drug_dose", "")
    unit = transaction.get("substitute_drug_unit", "")
    sig_text = transaction.get("substitute_drug_sig", "")
    annotation_text = transaction.get("annotation", "")
    is_compound = transaction.get("substitute_is_compound", False)
    api_id = transaction.get("api_id", "")

    log_print("=" * 60)
    log_print(f"[PROCESS] Processing: Rx {rx_number} | Drug: {transaction.get('drug_name', '')}")
    log_print("=" * 60)

    update_sent = False

    try:
        # ---- Step 1: Ensure Pioneer is in foreground ----
        _ensure_pioneer_foreground()

        # ---- Step 2: Search prescription by Rx number ----
        search_success, rx_found = rx_search.search_and_open_rx(rx_number)
        if not search_success:
            raise config.SystemException(f"Rx search failed for {rx_number}")
        if not rx_found:
            update_api.update_skipped(api_id, f"Rx not found: {rx_number}")
            update_sent = True
            raise config.BusinessRuleException(f"Rx not found: {rx_number}")

        # ---- Step 3: Handle popups after opening Rx ----
        if rxinuse_popup.click_cancel_rxinuse():
            log_print("[PROCESS] Rx In Use — skipping")
            raise config.BusinessRuleException("Rx is in use by another user")

        _handle_popups()

        try:
            drugfill_popup.dismiss_drugfill_popup()
        except Exception:
            pass

        # ---- Step 4: Select drug type and search by NDC ----
        if not drug_ndc:
            update_api.update_skipped(api_id, "No drug NDC provided")
            update_sent = True
            raise config.BusinessRuleException("No drug NDC in API response")

        _ensure_pioneer_foreground()
        drugtype_selection.select_drug_type(is_compound=is_compound)

        _ensure_pioneer_foreground()
        drug_success, drug_found = drug_selection_direct.search_drug_direct(
            drug_ndc, is_compound=is_compound
        )

        if not drug_success:
            _add_to_retry(rx_number)
            raise config.SystemException("Drug search failed")
        if not drug_found:
            _add_to_retry(rx_number)
            update_api.update_skipped(api_id, f"Drug not found: NDC {drug_ndc}")
            update_sent = True
            raise config.BusinessRuleException(f"Drug not found: NDC {drug_ndc}")

        # ---- Step 5: Set quantity and unit ----
        if unit and not drug_unit.is_supported_unit(unit):
            update_api.update_skipped(api_id, f"Unsupported drug unit: {unit}")
            update_sent = True
            raise config.BusinessRuleException(f"Unsupported drug unit: {unit}")

        if drug_unit.is_ct_unit(unit):
            qty_with_ct = f"{quantity} ct" if quantity else ""
            if qty_with_ct:
                log_print(f"[PROCESS] Setting quantity (CT): {qty_with_ct}")
                drug_quantity.set_quantity(qty_with_ct)
        else:
            if quantity:
                log_print(f"[PROCESS] Setting quantity: {quantity}")
                drug_quantity.set_quantity(quantity)
            if unit:
                log_print(f"[PROCESS] Setting unit: {unit}")
                unit_success, _ = drug_unit.set_unit(unit)
                if not unit_success:
                    raise config.SystemException(f"Failed to set unit: {unit}")

        # ---- Step 6: Set SIG (only if valid value from API) ----
        if sig_text and sig_text.strip().upper() not in ("", "NA", "N/A"):
            log_print(f"[PROCESS] Setting SIG: {sig_text[:60]}...")
            drug_sig.set_sig(sig_text)
        else:
            log_print(f"[PROCESS] Skipping SIG (empty or NA)")

        # ---- Step 7: Select Pharmacist (RPh) ----
        log_print(f"[PROCESS] Setting RPh: {config.PHARMACIST_NAME}")
        dispense.set_rph()

        # ---- Step 8: Switch to Image tab and add annotation ----
        if annotation_text:
            log_print("[PROCESS] Switching to Image tab...")
            _click_image_tab()
            log_print(f"[PROCESS] Adding annotation: {annotation_text[:60]}...")
            annotation.add_annotation(annotation_text)

        # ---- Step 9: Save & Continue ----
        screenshot_path = take_screenshot("before_save")

        if not save_and_continue.click_save_by_config():
            raise config.SystemException("Failed to save")

        # ---- Step 9: Handle Equivalent Rx popup ----
        equivalent_rx.click_fill_anyway()

        # ---- Step 10: Handle Error/Warning List ----
        ew_success, non_bypassable, error_text = error_and_warning.handle_error_warning()
        if not ew_success and non_bypassable:
            error_lower = error_text.lower()
            has_third_party = "third party setup for primary claim submission only" in error_lower
            has_daw = "daw" in error_lower

            if has_third_party or has_daw:
                if has_third_party:
                    log_print("[PROCESS] Third Party error — setting Secondary to <None>")
                    dispense.clear_secondary_insurance()
                if has_daw:
                    log_print("[PROCESS] DAW error — toggling DAW checkbox")
                    dispense.toggle_daw()

                if not save_and_continue.click_save_by_config():
                    raise config.SystemException("Failed to save after error fix")
                equivalent_rx.click_fill_anyway()
                ew_success2, non_bypassable2, _ = error_and_warning.handle_error_warning()
                if not ew_success2 and non_bypassable2:
                    ew_screenshot = take_screenshot("non_bypassable_error")
                    cancel_prescription.click_cancel()
                    update_api.update_skipped(api_id, "Non-bypassable error after fix", screenshot_path=ew_screenshot)
                    update_sent = True
                    raise config.BusinessRuleException("Non-bypassable error — prescription skipped")
            else:
                ew_screenshot = take_screenshot("non_bypassable_error")
                cancel_prescription.click_cancel()
                update_api.update_skipped(api_id, "Non-bypassable error", screenshot_path=ew_screenshot)
                update_sent = True
                raise config.BusinessRuleException("Non-bypassable error — prescription skipped")

        # ---- Step 10.1: Handle Alerts popup ----
        error_and_warning.handle_alerts_popup()

        # ---- Step 10.2: Handle Equivalent Pending Rx popup ----
        equivalent_rx.click_ignore_and_continue()

        # ---- Step 11: Update API — success ----
        update_api.update_success(api_id, screenshot_path=screenshot_path)
        update_sent = True

        log_print(f"[PROCESS] Completed: Rx {rx_number}")

    except config.BusinessRuleException:
        cancel_prescription.click_cancel()
        if api_id and not update_sent:
            update_api.update_failed(api_id, "Business rule exception")
        raise
    except config.SystemException as exc:
        take_screenshot("system_error")
        cancel_prescription.click_cancel()
        _add_to_retry(rx_number)
        if api_id and not update_sent:
            update_api.update_failed(api_id, str(exc))
        raise
    except Exception as exc:
        take_screenshot("system_error")
        cancel_prescription.click_cancel()
        _add_to_retry(rx_number)
        if api_id and not update_sent:
            update_api.update_failed(api_id, str(exc))
        raise config.SystemException(f"Unexpected error in process: {exc}")
