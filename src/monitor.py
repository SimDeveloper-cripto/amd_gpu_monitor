
import os
import re
from collections import deque
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any, Deque

class AMDGPU:
    def __init__(self, card_path: str, history_len: int = 60):
        self.card_path    : str = card_path
        self.device_path  : str = os.path.join(card_path, "device")
        self.id           : str = os.path.basename(card_path)
        self.device_id    : str = self._read_file("device").strip()
        self.vendor_id    : str = self._read_file("vendor").strip()
        self.model_name   : str = self._get_pci_name()

        self.current_load : int   = 0
        self.current_temp : float = 0.0
        self.current_power: float = 0.0

        self.history_load : Deque[int]   = deque(maxlen=history_len)
        self.history_temp : Deque[float] = deque(maxlen=history_len)
        self.history_power: Deque[float] = deque(maxlen=history_len)

    def _read_file(self, filename: str, path: Optional[str] = None) -> str:
        if path is None:
            path = self.device_path

        full_path = os.path.join(path, filename)
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read().strip()
            except Exception:
                pass
        return ""

    def _get_pci_name(self) -> str:
        pci_ids_path = "/usr/share/misc/pci.ids"
        default_name = f"AMD GPU ({self.device_id})"

        if not os.path.exists(pci_ids_path):
            return default_name

        v_id = self.vendor_id.replace("0x", "").lower()
        d_id = self.device_id.replace("0x", "").lower()

        try:
            with open(pci_ids_path, "r", encoding="utf-8", errors="ignore") as f:
                found_vendor = False
                for line in f:
                    if line.startswith(v_id):
                        found_vendor = True
                        continue
                    if found_vendor and line.startswith("\t" + d_id):
                        raw_name = line.strip().split("  ")[-1]
                        if "[" in raw_name:
                            clean_name = re.sub(r'.*?\[', '', raw_name).replace(']', '')
                            return f"Radeon {clean_name}"
                        return raw_name
                    if found_vendor and re.match(r'^[0-9a-f]{4}', line):
                        break
        except Exception:
            pass
        return default_name

    def refresh(self) -> None:
        self.current_load  = self.get_load()
        self.current_temp  = self.get_temp()
        self.current_power = self.get_power()

        self.history_load.append(self.current_load)
        self.history_temp.append(self.current_temp)
        self.history_power.append(self.current_power)

    def get_metrics_dict(self) -> Dict[str, Any]:
        vram_used, vram_total = self.get_vram_usage()
        junction              = self.get_junction_temp()
        mem_temp              = self.get_mem_temp()

        return {
            "id"           : self.id,
            "model"        : self.model_name,
            "temp"         : self.get_temp(),
            "temp_junction": junction,
            "temp_mem"     : mem_temp,
            "load"         : self.get_load(),
            "vram_used"    : vram_used,
            "vram_total"   : vram_total,
            "power"        : self.get_power(),
            "power_cap"    : self.get_power_cap(),
            "voltage"      : self.get_voltage(),
            "fan"          : self.get_fan(),
            "sclk"         : self.get_sclk(),
            "mclk"         : self.get_mclk(),
            "pcie"         : self.get_pcie_bw(),
            "timestamp"    : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def get_junction_temp(self) -> float:
        return self._find_temp_by_label(["junction", "hotspot", "edge"])

    def get_mem_temp(self) -> float:
        return self._find_temp_by_label(["mem", "memory"])

    def _find_temp_by_label(self, labels: List[str]) -> float:
        hwmon_root = os.path.join(self.device_path, "hwmon")
        if os.path.exists(hwmon_root):
            for h in os.listdir(hwmon_root):
                h_path = os.path.join(hwmon_root, h)
                for f in os.listdir(h_path):
                    if f.endswith("_label") and f.startswith("temp"):
                        try:
                            label_val = self._read_file(f, path=h_path).lower()
                            if any(l in label_val for l in labels):
                                prefix = f.split("_")[0]
                                val    = self._read_file(f"{prefix}_input", path=h_path)
                                if val:
                                    return float(val) / 1000.0
                        except:
                            pass
        return 0.0

    def get_voltage(self) -> float:
        hwmon_root = os.path.join(self.device_path, "hwmon")
        if os.path.exists(hwmon_root):
             for h in os.listdir(hwmon_root):
                 val = self._read_file("in0_input", path=os.path.join(hwmon_root, h))
                 if val:
                     return float(val) / 1000.0
        return 0.0

    def get_power_cap(self) -> float:
        hwmon_root = os.path.join(self.device_path, "hwmon")
        if os.path.exists(hwmon_root):
             for h in os.listdir(hwmon_root):
                 val = self._read_file("power1_cap", path=os.path.join(hwmon_root, h))
                 if val:
                     return float(val) / 1000000.0
        return 0.0

    def get_pcie_bw(self) -> str:
        speed = self._read_file("current_link_speed")
        width = self._read_file("current_link_width")
        if speed and width:
            return f"{speed} x{width}"
        return "N/A"

    def get_temp(self) -> float:
        hwmon_root = os.path.join(self.device_path, "hwmon")
        if os.path.exists(hwmon_root):
            for h in os.listdir(hwmon_root):
                t_file = os.path.join(hwmon_root, h, "temp1_input")
                val = self._read_file(t_file, path="") 
                if val:
                    return float(val) / 1000.0
        return 0.0

    def get_load(self) -> int:
        val = self._read_file("gpu_busy_percent")
        return int(val) if val else 0

    def get_vram_usage(self) -> Tuple[int, int]:
        try:
            total_str = self._read_file("mem_info_vram_total")
            used_str  = self._read_file("mem_info_vram_used")
            total     = int(total_str) if total_str else 0
            used      = int(used_str) if used_str else 0

            if total > 0:
                return used // (1024**2), total // (1024**2)
        except Exception:
            pass
        return 0, 0

    def get_power(self) -> float:
        hwmon_root = os.path.join(self.device_path, "hwmon")
        if os.path.exists(hwmon_root):
            for h in os.listdir(hwmon_root):
                p_file = os.path.join(hwmon_root, h, "power1_average")
                val    = self._read_file(p_file, path="")
                if not val:
                    p_file = os.path.join(hwmon_root, h, "power1_input")
                    val    = self._read_file(p_file, path="")
                if val:
                    return float(val) / 1000000.0
        return 0.0

    def get_fan(self) -> int:
        hwmon_root = os.path.join(self.device_path, "hwmon")
        if os.path.exists(hwmon_root):
            for h in os.listdir(hwmon_root):
                f_file = os.path.join(hwmon_root, h, "fan1_input")
                val    = self._read_file(f_file, path="")
                if val:
                    return int(val)
        return 0

    def get_sclk(self) -> int:
        content = self._read_file("pp_dpm_sclk")
        if content:
            match = re.search(r'\d+:\s+(\d+)Mhz\s+\*', content)
            if match:
                return int(match.group(1))
        return 0

    def get_mclk(self) -> int:
        content = self._read_file("pp_dpm_mclk")
        if content:
            match = re.search(r'\d+:\s+(\d+)Mhz\s+\*', content)
            if match:
                return int(match.group(1))
        return 0

    def get_processes(self) -> List[Dict[str, str]]:
        render_node = None
        drm_path    = os.path.join(self.card_path, "device", "drm")
        if os.path.exists(drm_path):
             for item in os.listdir(drm_path):
                 if item.startswith("render"):
                     render_node = f"/dev/dri/{item}"
                     break

        if not render_node:
            return []

        procs = []
        try:
            pass
        except Exception:
            pass

        return procs

def get_amd_gpus() -> List[AMDGPU]:
    base_path = "/sys/class/drm/"
    gpus      = []
    if not os.path.exists(base_path):
        return gpus
    cards = sorted([d for d in os.listdir(base_path) if re.match(r'card[0-9]+$', d)])

    for card in cards:
        full_path   = os.path.join(base_path, card)
        vendor_file = os.path.join(full_path, "device", "vendor")
        if os.path.exists(vendor_file):
            try:
                with open(vendor_file, "r") as f:
                    if "1002" in f.read():
                        gpus.append(AMDGPU(full_path))
            except Exception:
                pass
    return gpus