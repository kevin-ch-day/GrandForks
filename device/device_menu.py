# device/device_menu.py

import sys
import subprocess
from utils.adb_utils import adb_ip_lookup
from device import vendor_normalizer
from utils.display_utils import prompt_utils, menu_utils
from analysis.static_analysis import run_static_analysis   # <-- import

def interactive_device_menu(device: dict):
    """Interactive menu after connecting to a device."""
    serial = device.get("serial", "unknown")
    details = device.get("details", {}) if isinstance(device.get("details"), dict) else {}
    vendor = vendor_normalizer.normalize_vendor(details)
    model = details.get("model", "unknown")

    ip_info = adb_ip_lookup.get_ip_for_device(serial)
    ip = ip_info.get("ip") if isinstance(ip_info, dict) else ip_info

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

    def open_shell():
        if prompt_utils.ask_yes_no(f"Open adb shell for {serial}?", default="y"):
            print(f"\n[ADB SHELL] Opening shell for {serial}...\n")
            subprocess.run(["adb", "-s", serial, "shell"])

    def run_static():
        print("\n🔍 Running static analysis...\n")
        try:
            run_static_analysis.analyze_device(serial)   # <-- call into analysis
        except Exception as e:
            print(f"❌ Static analysis failed: {e}")

    def disconnect():
        if prompt_utils.ask_yes_no(f"Disconnect from {serial}?", default="y"):
            print(f"\n🔌 Disconnected from {serial}")
            return True
        return False

    def reboot():
        if prompt_utils.ask_yes_no(f"Reboot {serial}?", default="y"):
            subprocess.run(["adb", "-s", serial, "reboot"])
            print(f"\n🔄 Rebooted {serial}")

    def exit_program():
        if prompt_utils.ask_yes_no("Exit program?", default="n"):
            print("\n👋 Exiting.")
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
        if choice == "4" and disconnect():
            break
