# Social App Finder Scripts

Helper components for locating popular social media apps on an Android device.

* `android_app_finder.lib.sh` – core helpers (ADB queries, reporting, collectors).
* `opsec.lib.sh` – jitter, randomization, and defense-sensor sweeps.
* `scan.lib.sh` – per-user scanning routine consumed by the main script.

Run `../find_social_apps.sh` from this directory or the repository root to scan a connected device.

