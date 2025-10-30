# Technology Stack

## Core Language
- **Python 3.9**: The primary language for the project.

## Key Libraries & Frameworks
- **setuptools**: Used for packaging and distribution of the `xengym` library.
- **cypack**: A setup requirement, suggesting that some Python code may be compiled into C for performance.
- **numpy**: A fundamental dependency for numerical operations, essential for physics and data manipulation.

## Development & Build
- **Packaging**: The project is structured as a Python package and can be installed using `setup.py`.
- **Entry Point**: A command-line demo is available via `xengym-demo`, which runs the `main` function in `xengym.main`.

## Asset Pipeline
- **Asset Handling**: The `setup.py` script includes a mechanism to package all assets located in `xengym/assets/`, making them available at runtime.
