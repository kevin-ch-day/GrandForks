# device/device_menu.py
"""Interactive device menu implemented with an object-oriented design."""

import sys
import subprocess

from utils.adb_utils import adb_ip_lookup
from utils.adb_utils import adb_runner
from utils.adb_utils.adb_client import ADBClient
from utils.adb_utils.adb_devices import DeviceInfo
from utils.adb_utils.adb_root import attempt_root
from device import vendor_normalizer
from utils.display_utils import prompt_utils
from utils.display_utils.menu_utils import MenuExit
from menus.base import BaseMenu, MenuAction
from analysis.static_analysis import run_static_analysis
from config import app_config
import utils.logging_utils.logging_engine as log


class DeviceMenu(BaseMenu):
    """Menu shown after connecting to a specific device."""

    def __init__(self, device: DeviceInfo) -> None:
        self.device = device
        self.serial = device.serial
        self.adb = ADBClient(self.serial)
        self.details = device.details
        self.vendor = vendor_normalizer.normalize_vendor(self.details)
        self.model = self.details.get("model", "unknown")
        self.ip = adb_ip_lookup.get_ip_for_device(self.serial)
        super().__init__(title="Device Menu", exit_label="Back")
        self.actions = {
            "1": MenuAction("Show device info", self.show_info),
            "2": MenuAction("Open adb shell", self.open_shell),
            "3": MenuAction("Run static analysis", self.run_static_analysis),
            "4": MenuAction("Gain root access", self.gain_root_access),
            "5": MenuAction("Disconnect", self.disconnect),
            "6": MenuAction("Reboot device", self.reboot_device),
            "7": MenuAction("Exit program", self.exit_program),
        }
        log.info(
            f"Opened device menu for {self.serial} (vendor={self.vendor}, model={self.model}, ip={self.ip or 'N/A'})"
        )

    def show(self) -> None:  # type: ignore[override]
        """Display header info before rendering menu."""
        print("\n📱 Connected to Device")
        print("----------------------")
        print(f"Serial   : {self.serial}")
        print(f"Vendor   : {self.vendor}")
        print(f"Model    : {self.model}")
        if self.ip:
            print(f"IP Addr  : {self.ip}")
        super().show()
        log.info(f"Exiting device menu for {self.serial}")

    # ----- Action handlers -----
    def show_info(self) -> None:
        print("\n[INFO] Device Details")
        print("----------------------")
        print(f"Serial   : {self.serial}")
        print(f"Vendor   : {self.vendor}")
        print(f"Model    : {self.model}")
        print(f"IP Addr  : {self.ip or 'N/A'}")
        log.debug(f"Displayed device info for {self.serial}")

    def open_shell(self) -> None:
        if prompt_utils.ask_yes_no(f"Open adb shell for {self.serial}?", default="y"):
            res = self.adb.interactive_shell()
            if res.get("success"):
                print(f"\n[ADB SHELL] Opening shell for {self.serial}...\n")
                log.info(f"ADB shell opened for {self.serial}")
            else:
                print(f"❌ Device {self.serial} not ready: {res.get('error')}")
                log.error(f"Device {self.serial} not ready: {res.get('error')}")

    def run_static_analysis(self) -> None:
        print("\n🔍 Running static analysis...\n")
        try:
            log.info(f"Launching static analysis for {self.serial}")
            limit = getattr(app_config, "ARTIFACT_LIMIT", 3)
            run_static_analysis.analyze_device(self.serial, artifact_limit=limit)
            log.info(f"Static analysis finished for {self.serial}")
        except KeyboardInterrupt:
            print("\n⚠️  Static analysis interrupted. Returning to menu.\n")
            log.warning(f"Static analysis interrupted for {self.serial}")
        except Exception as e:
            print(f"❌ Static analysis failed: {e}")
            log.error(f"Static analysis failed for {self.serial}: {e}")

    def gain_root_access(self) -> None:
        if prompt_utils.ask_yes_no(f"Attempt root access for {self.serial}?", default="n"):
            success = attempt_root(self.serial)
            msg = "Root access granted" if success else "Root access denied"
            print(f"\n{msg} for {self.serial}")

    def disconnect(self) -> None:
        if prompt_utils.ask_yes_no(f"Disconnect from {self.serial}?", default="y"):
            print(f"\n🔌 Disconnected from {self.serial}")
            log.info(f"Disconnected from {self.serial}")
            raise MenuExit

    def reboot_device(self) -> None:
        if prompt_utils.ask_yes_no(f"Reboot {self.serial}?", default="y"):
            res = self.adb.reboot()
            if res.get("success"):
                print(f"\n🔄 Rebooted {self.serial}")
                log.info(f"Reboot command issued for {self.serial}")
            else:
                print(f"❌ Device {self.serial} not ready: {res.get('error')}")
                log.error(f"Failed to reboot {self.serial}: {res.get('error')}")

    def exit_program(self) -> None:
        if prompt_utils.ask_yes_no("Exit program?", default="n"):
            print("\n👋 Exiting.")
            log.critical("User requested program exit from device menu")
            sys.exit(0)


def interactive_device_menu(device: DeviceInfo) -> None:
    """Wrapper for backward compatibility."""
    DeviceMenu(device).show()
