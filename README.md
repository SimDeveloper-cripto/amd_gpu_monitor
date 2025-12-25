# AMD GPU Monitor

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A professional, lightweight, and dependency-free terminal user interface (TUI) for monitoring AMD graphics cards on Linux. It reads directly from `sysfs`, requiring no complex driver libraries.

## Features

-   **Real-time Dashboard**: Monitor Temp, Load, VRAM, Power, Fan, and Clocks.
-   **Interactive TUI**: Navigate with arrow keys and mouse, view details with Enter.
-   **Dependencies**: Uses standard Python libraries (`curses`, `os`, `csv`, `json`, `textual`).

## Installation

### Quick Start (Recommended)

Simply use the provided helper script:

```bash
chmod +x run.sh
./run.sh
```

### Manual Installation (Virtual Environment)
Because system-wide installation is restricted on many Linux distros (PEP 668), it is recommended to use a virtual environment:

1.  **Install prerequisites** (Ubuntu/Debian):
    ```bash
    sudo apt install python3-venv
    ```

2.  **Create venv and install**:
    ```bash
    python3 -m venv venv
    ./venv/bin/pip install .
    ```

## Usage

If you installed manually via `venv`, run:

```bash
./venv/bin/python3 -m src.main
```

## License

MIT