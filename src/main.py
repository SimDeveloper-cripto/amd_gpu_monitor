#!/usr/bin/env python3

import os
import sys
import argparse

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
libs_path    = os.path.join(project_root, ".libs")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

from .ui import MonitorApp

def main() -> None:
    parser = argparse.ArgumentParser(description="AMD GPU Monitor Professional")
    parser.add_argument("--version", action="version", version="amd_gpu_monitor v2.0.0")
    
    args = parser.parse_args()
    
    if not sys.stdout.isatty():
        print("Error: This tool must be run in a terminal.")
        sys.exit(1)

    app = MonitorApp()
    app.run()

if __name__ == "__main__":
    main()