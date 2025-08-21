# Social App Finder Scripts

This directory contains helper scripts for locating popular social media apps on an Android device. 

* `find_social_apps.sh` – main entry point that scans for packages such as TikTok or Facebook.
  * Supports OPSEC-friendly options like `--stealth`, jittered timing, noise budgets, and
    `--probe-exported` for light component recon.
  * Package profiles (`--profile social-extended`) and regex filters (`--filter '^com\.twitter\.'`) help
    tailor scans. Use `--require-found` for CI gating.
* `android_app_finder.lib.sh` – shared library used by the main script.

The scripts were moved out of the top-level `scripts` folder for easier maintenance and debugging.
