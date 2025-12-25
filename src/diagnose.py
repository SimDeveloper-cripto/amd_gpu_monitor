import os
import glob

def diagnose():
    base = "/sys/class/drm"
    print(f"Scanning {base}...")

    if not os.path.exists(base):
        print("Error: /sys/class/drm does not exist.")
        return

    cards = glob.glob(os.path.join(base, "card*"))
    if not cards:
        print("No cards found in /sys/class/drm.")
        return

    for card in cards:
        print(f"\n--- Analyzing {os.path.basename(card)} ---")
        print(f"Path: {card}")
        
        dev_path      = os.path.join(card, "device")
        real_dev_path = os.path.realpath(dev_path) if os.path.exists(dev_path) else "MISSING"
        print(f"Device Symlink: {dev_path} -> {real_dev_path}")

        try:
            with open(os.path.join(dev_path, "vendor"), "r") as f:
                print(f"Vendor: {f.read().strip()}")
        except Exception as e:
            print(f"Could not read vendor: {e}")

        load_files = ["gpu_busy_percent", "pp_dpm_sclk", "amdgpu_pm_info"]
        print("\n[Load Candidates]")
        for lf in load_files:
            p       = os.path.join(dev_path, lf)
            exists  = os.path.exists(p)
            content = "N/A"
            if exists:
                try:
                    with open(p, "r") as f:
                        content = f.read().strip().replace("\n", " ")[:50]
                except Exception as e:
                    content = f"Error: {e}"
            print(f"  {lf}: {'FOUND' if exists else 'MISSING'} -> {content}")

        print("\n[Hwmon Search]")
        hwmon = os.path.join(dev_path, "hwmon")
        if os.path.exists(hwmon):
            for h in os.listdir(hwmon):
                hpath = os.path.join(hwmon, h)
                print(f"  Found hwmon subdirectory: {h}")

                temps = glob.glob(os.path.join(hpath, "temp*_input"))
                for t in temps:
                    try:
                        val = open(t).read().strip()
                        print(f"    {os.path.basename(t)}: {val} (div 1000 = {float(val)/1000} C)")
                    except Exception as e:
                        print(f"    {os.path.basename(t)}: Error {e}")
        else:
            print("  No hwmon directory found in device path.")

if __name__ == "__main__":
    diagnose()