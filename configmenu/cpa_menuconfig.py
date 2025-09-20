import shutil

# Merge-Logik: Nach jedem Menü die neuen Werte in die bestehende .config übernehmen
def merge_config(old_config, new_config, relevant_prefixes):
    """Mische nur die Werte mit den relevanten Prefixen aus new_config in old_config."""
    def parse_config(path):
        vals = {}
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if line.startswith("CONFIG_") or line.startswith("# CONFIG_"):
                        key = line.split()[1] if line.startswith("# ") else line.split("=")[0]
                        vals[key] = line.rstrip("\n")
        return vals
    old_vals = parse_config(old_config)
    new_vals = parse_config(new_config)
    # Überschreibe nur relevante Keys
    for key, val in new_vals.items():
        if any(key.startswith(prefix) for prefix in relevant_prefixes):
            old_vals[key] = val
    # Schreibe gemergte .config
    with open(old_config, "w") as f:
        for val in old_vals.values():
            f.write(val + "\n")
#!/usr/bin/env python3
"""
CPA Konfigurations-Workflow-Wrapper
- Menü 1: Systemtyp-Auswahl (Kconfig.system)
- Menü 2: Hardwarevariante & Diskettenlaufwerke (Kconfig.hardware)
- Menü 3: Build-Ausgabeformat (Kconfig.build)
- Nach jedem Schritt: ggf. patch_bios_mac.py und Build starten
"""
import subprocess
import sys
import os

def run_menu(kconfig_file, config_file):
    """Starte menuconfig für eine bestimmte Kconfig-Datei."""
    try:
        env = os.environ.copy()
        env["KCONFIG_CONFIG"] = config_file
        subprocess.run([
            sys.executable, os.path.join("configmenu", "menuconfig.py"), kconfig_file
        ], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"[FEHLER] menuconfig für {kconfig_file} fehlgeschlagen: {e}")
        sys.exit(1)

def run_patch_bios_mac(config_file, mode):
    """Führe patch_bios_mac.py im Modus 'extract' oder 'patch' aus (auto)."""
    try:
        subprocess.run([
            sys.executable, os.path.join("configmenu", "patch_bios_mac.py"), "auto", config_file, mode
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[FEHLER] patch_bios_mac.py fehlgeschlagen: {e}")
        sys.exit(1)

def run_build(target):
    """Starte den Build-Prozess mit make <target>."""
    try:
        cmd = ["make", "config", target]
        print(f"[DEBUG] Starte Build mit: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[FEHLER] Build für Target {target} fehlgeschlagen: {e}")
        sys.exit(1)

def main():
    config_file = ".config"
    # Backup der Startkonfiguration
    if os.path.exists(config_file):
        shutil.copyfile(config_file, config_file + ".bak")

    # Menü 1: Systemtyp-Auswahl
    run_menu(os.path.join("configmenu", "Kconfig.system"), config_file)
    # Nach Menü 1: Systemtyp-Optionen mergen
    if os.path.exists(config_file+".old"):
        merge_config(config_file+".old", config_file, ["CONFIG_SYSTEM_"])
        shutil.move(config_file+".old", config_file)

    # Menü 2: Hardwarevariante & Diskettenlaufwerke
    run_menu(os.path.join("configmenu", "Kconfig.hardware"), config_file)
    # Nach Menü 2: Hardware- und Laufwerksoptionen mergen
    if os.path.exists(config_file+".old"):
        merge_config(config_file+".old", config_file, ["CONFIG_DEV_", "CONFIG_CPUCLK_", "CONFIG_CPU_", "CONFIG_FDC_", "CONFIG_CRT_", "CONFIG_RAM_", "CONFIG_DRIVE_", "CONFIG_RAMDISK_"])
        shutil.move(config_file+".old", config_file)

    # Nach Hardwaremenü: bios.mac patchen
    run_patch_bios_mac(config_file, "patch")

    # Menü 3: Build-Ausgabeformat
    run_menu(os.path.join("configmenu", "Kconfig.build"), config_file)
    # Nach Menü 3: Build-Optionen mergen
    if os.path.exists(config_file+".old"):
        merge_config(config_file+".old", config_file, ["CONFIG_BUILD_"])
        shutil.move(config_file+".old", config_file)

    # Build-Target aus .config auslesen
    build_target = "os"  # Default
    if os.path.exists(config_file):
        with open(config_file) as f:
            for line in f:
                if line.startswith("CONFIG_BUILD_DISKIMAGE=y"):
                    build_target = "diskImage"
                elif line.startswith("CONFIG_BUILD_WRITEIMAGE=y"):
                    build_target = "writeImage"
    run_build(build_target)

if __name__ == "__main__":
    main()
