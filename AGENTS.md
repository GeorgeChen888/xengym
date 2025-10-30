# Repository Guidelines

## Project Structure & Module Organization
- `xengym/` hosts the simulator package: `render/` handles scenes and UI, `fem/` captures material models, `ezgym/` wraps robot and asset adapters, and `main.py` backs the `xengym-demo` entry point.
- `xengym/assets/` stores STL meshes and sensor resources; keep new files lightweight and document provenance in PRs.
- `calibration/` contains FEM post-processing utilities and data format helpers—align changes with `CALIBRATION_DATA_FORMAT.md` and `calibration_example.py`.
- `example/` offers runnable demos and data pipelines used in regression checks; treat them as living integration references.
- `quick_test.py` and `example/test*.py` are the current smoke tests—extend them when shipping new capabilities.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` prepares a Python 3.9+ environment.
- `pip install -e .` (or `uv pip install -e .`) installs the package in editable mode; rerun after adding assets or changing build metadata.
- `xengym-demo --show-left --object-file xengym/assets/obj/circle_r4.STL` launches the primary scene with a sample object and exposes CLI flags.
- `python quick_test.py` validates calibration imports, asset discovery, and parameter bounds.
- `python example/demo_main.py` or `python example/data_collection.py` exercises multi-sensor workflows before submitting feature work.

## Coding Style & Naming Conventions
- Target Python 3.9, four-space indentation, and PEP 8 naming (`snake_case` functions, `PascalCase` classes, uppercase constants).
- Favor explicit relative imports inside package modules; avoid wildcards to keep C/C++ bindings and plugins stable.
- Keep docstrings concise and in English by default; reserve inline comments for non-obvious math or calibration heuristics.

## Testing Guidelines
- Place new regression scripts alongside features (e.g., `example/test_new_modes.py`) and name files `test_<feature>.py`.
- Update `quick_test.py` whenever calibration parameters, asset search paths, or scene defaults change.
- For FEM adjustments, record baseline outputs under `calibration/` and summarize dataset provenance in the accompanying PR.
- Run demos headless when possible (`visible=False`) to keep automated smoke checks reliable.

## Commit & Pull Request Guidelines
- Follow the existing `<type>: <message>` format (`feat`, `fix`, `perf`, `docs`, `refactor`), e.g., `feat: add diff image api`.
- Ensure each commit builds and passes smoke tests; squash noisy WIP commits before review.
- PRs must include a behavior summary, manual or automated test evidence, asset updates, and linked issues or tasks.
- Attach short captures or depth-field diffs when UI or sensor outputs change, and note the calibration data version used.

## Calibration & Asset Notes
- Store large raw captures outside the repo; commit only processed assets required for reproduction and reference their location in the PR.
- Keep STL filenames descriptive (`<shape>_<metric>.STL`) and update defaults in `xengym/render/calibScene.py` when introducing new tooling.
