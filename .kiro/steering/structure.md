# Project Structure

## Root Directory
- **`.kiro/`**: Contains steering documents and specifications for development.
- **`xengym/`**: The core source code for the simulation library.
- **`example/`**: Contains example scripts demonstrating how to use the `xengym` library.
- **`setup.py`**: The build and installation script for the package.
- **`README.md`**: Project overview and getting started guide.

## Core Library (`xengym/`)
- **`main.py`**: The main entry point for the `xengym-demo` command.
- **`assets/`**: Contains all static assets required for simulation, such as 3D models (`.obj`, `.STL`), URDF files, and data (`.npz`).
- **`ezgym/`**: Appears to be a high-level wrapper or utility library for creating simulation environments (`_env.py`, asset management).
- **`fem/`**: Contains the Finite Element Method simulation components (`simulation.py`).
- **`render/`**: Manages rendering and visualization (`robotScene.py`, `sensorScene.py`).

## Naming Conventions
- **Modules**: Lowercase with underscores (e.g., `robot_scene.py`) is inferred from the existing file names, although many are single words.
- **Packages**: Lowercase names (e.g., `ezgym`, `fem`).
