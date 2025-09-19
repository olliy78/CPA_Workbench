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
        subprocess.run([
            sys.executable, os.path.join("configmenu", "menuconfig.py"), kconfig_file,
        ], check=True)
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
        subprocess.run(["make", target], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[FEHLER] Build für Target {target} fehlgeschlagen: {e}")
        sys.exit(1)

def main():
    config_file = ".config"
    # Menü 1: Systemtyp-Auswahl
    run_menu(os.path.join("configmenu", "Kconfig.system"), config_file)
    # Nach Systemtyp-Auswahl: bios.mac und .config synchronisieren
    run_patch_bios_mac(config_file, "extract")
    # Menü 2: Hardwarevariante & Diskettenlaufwerke
    run_menu(os.path.join("configmenu", "Kconfig.hardware"), config_file)
    # Nach Hardwaremenü: bios.mac patchen
    run_patch_bios_mac(config_file, "patch")
    # Menü 3: Build-Ausgabeformat
    run_menu(os.path.join("configmenu", "Kconfig.build"), config_file)
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
