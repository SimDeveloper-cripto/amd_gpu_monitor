# AMD GPU Monitor

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A professional, lightweight, and dependency-free terminal user interface (TUI) for monitoring AMD graphics cards on Linux. It reads directly from `sysfs`, requiring no complex driver libraries.

TODO
- **Detailed View**: Inspect PCIe link speed, driver version, and all sensor inputs. [Not implemented]

## Features

-   **Real-time Dashboard**: Monitor Temp, Load, VRAM, Power, Fan, and Clocks.
-   **Interactive TUI**: Navigate with arrow keys and mouse, view details with Enter.
-   **Dependencies**: Uses standard Python libraries (`curses`, `os`, `csv`, `json`, `textual`).

## Installation

### From Source

```bash
git clone https://github.com/example/amd_gpu_monitor.git
cd amd_gpu_monitor
```

## Usage

Once installed, run:

```bash
python3 -m src.main
```

### CLI Arguments

| Argument | Description |

### Keyboard Shortcuts

-   **UP / DOWN** : Select GPU.
-   **ENTER**     : Show detailed information for selected GPU.
-   **q**         : Quit.

## JSON API



## License

MIT