# device/device_menu.py

import sys
import subprocess

from utils.adb_utils import adb_ip_lookup
from utils.adb_utils.adb_devices import DeviceInfo
from device import vendor_normalizer
from utils.display_utils import prompt_utils, menu_utils
from analysis.static_analysis import run_static_analysis   # <-- import
import utils.logging_utils.logging_engine as log


def interactive_device_menu(device: DeviceInfo):
    """Interactive menu after connecting to a device."""
    serial = device.serial
    details = device.details
    vendor = vendor_normalizer.normalize_vendor(details)
    model = details.get("model", "unknown")

    ip = adb_ip_lookup.get_ip_for_device(serial)
    log.info(
        f"Opened device menu for {serial} (vendor={vendor}, model={model}, ip={ip or 'N/A'})"
    )

    # Device info header
    print("\n📱 Connected to Device")
    print("----------------------")
    print(f"Serial   : {serial}")
    print(f"Vendor   : {vendor}")
    print(f"Model    : {model}")
    if ip:
        print(f"IP Addr  : {ip}")

    # Device actions
    def show_info():
        print("\n[INFO] Device Details")
        print("----------------------")
        print(f"Serial   : {serial}")
        print(f"Vendor   : {vendor}")
        print(f"Model    : {model}")
        print(f"IP Addr  : {ip or 'N/A'}")
        log.debug(f"Displayed device info for {serial}")

    def open_shell():
        if prompt_utils.ask_yes_no(f"Open adb shell for {serial}?", default="y"):
            print(f"\n[ADB SHELL] Opening shell for {serial}...\n")
            subprocess.run(["adb", "-s", serial, "shell"])
            log.info(f"ADB shell opened for {serial}")

    def run_static():
        print("\n🔍 Running static analysis...\n")
        try:
            log.info(f"Launching static analysis for {serial}")
            run_static_analysis.analyze_device(serial)   # <-- call into analysis
            log.info(f"Static analysis finished for {serial}")
        except KeyboardInterrupt:
            print("\n⚠️  Static analysis interrupted. Returning to menu.\n")
            log.warning(f"Static analysis interrupted for {serial}")
        except Exception as e:
            print(f"❌ Static analysis failed: {e}")
            log.error(f"Static analysis failed for {serial}: {e}")

    def disconnect():
        if prompt_utils.ask_yes_no(f"Disconnect from {serial}?", default="y"):
            print(f"\n🔌 Disconnected from {serial}")
            log.info(f"Disconnected from {serial}")
            return True
        return False

    def reboot():
        if prompt_utils.ask_yes_no(f"Reboot {serial}?", default="y"):
            subprocess.run(["adb", "-s", serial, "reboot"])
            print(f"\n🔄 Rebooted {serial}")
            log.info(f"Reboot command issued for {serial}")

    def exit_program():
        if prompt_utils.ask_yes_no("Exit program?", default="n"):
            print("\n👋 Exiting.")
            log.critical("User requested program exit from device menu")
            sys.exit(0)

    options = {
        "1": ("Show device info", show_info),
        "2": ("Open adb shell", open_shell),
        "3": ("Run static analysis", run_static),  # <-- new
        "4": ("Disconnect", disconnect),
        "5": ("Reboot device", reboot),
        "6": ("Exit program", exit_program),
    }

    while True:
        choice = menu_utils.show_menu("Device Menu", options, exit_label="Back")
        log.debug(f"Menu choice {choice} selected for device {serial}")
        if choice == "4" and disconnect():
            break
    log.info(f"Exiting device menu for {serial}")
