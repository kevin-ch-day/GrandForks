# Benchmarking APK Packaging

This directory contains a small reference set of apps that exhibit known packaging or configuration differences.
It also includes utilities to verify that our feature extraction behaves consistently across device-specific builds.

## Reference Apps
`reference_apps.json` enumerates each app and two APK variants.
The APKs themselves live in `reference_apks/` and represent examples such as:
- F-Droid vs Play Store builds
- Architecture-specific packages (ARM vs x86)

## Running the Benchmark
Run:

```bash
python3 scripts/benchmark/benchmark.py
```

For each app, feature extraction is executed on both APK variants. The results are written to `logs/benchmark/`:
- `<app>_type_a.json` and `<app>_type_b.json` contain the raw feature data.
- `diff.log` is a human-readable summary of mismatches.
- `report.json` mirrors the diff data in a machine-readable form for dashboards or further analysis.

If the script warns that `aapt2` is missing, install it (Fedora) via `scripts/install-aapt2.sh` for full manifest parsing.

## Extending
Add additional apps by editing `reference_apps.json` with new entries pointing to the relevant APK paths.
The benchmark helps validate cross-device packaging assumptions and can feed into regression tests or visualization tools via `report.json`.
