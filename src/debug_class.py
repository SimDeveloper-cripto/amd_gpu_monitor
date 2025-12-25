import os
import sys

sys.path.append(os.getcwd())

from src.monitor import get_amd_gpus

def check():
    print("Checking GPUs via AMDGPU class...")
    gpus = get_amd_gpus()
    print(f"Found {len(gpus)} GPUs.")

    for gpu in gpus:
        print(f"\nID       : {gpu.id}")
        print(f"Path       : {gpu.card_path}")
        print(f"Device Path: {gpu.device_path}")

        gpu.refresh()
        m = gpu.get_metrics_dict()

        print(f"Metrics  : {m}")
        print(f"Load raw : {gpu.get_load()}")
        print(f"Temp raw : {gpu.get_temp()}")
        print(f"Power raw: {gpu.get_power()}")

if __name__ == "__main__":
    check()