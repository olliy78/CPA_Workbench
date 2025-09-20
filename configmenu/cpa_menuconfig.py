import shutil
import glob

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

def run_patch_bios_mac(bios_mac_path, config_file, mode):
    """Führe patch_bios_mac.py im Modus 'extract' oder 'patch' aus."""
    try:
        subprocess.run([
            sys.executable, os.path.join("configmenu", "patch_bios_mac.py"), bios_mac_path, config_file, mode
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


def generate_kconfig_system(kconfig_path, src_dir):
    """Erzeuge Kconfig.system dynamisch aus sich selbst und src-Unterordnern."""
    # Lese aktuelle Kconfig.system ein
    with open(kconfig_path, "r") as f:
        lines = f.readlines()

    # Finde choice-Block
    choice_start = None
    choice_end = None
    for i, line in enumerate(lines):
        if line.strip().startswith("choice"):
            choice_start = i
        if line.strip() == "endchoice":
            choice_end = i
            break
    if choice_start is None or choice_end is None:
        raise RuntimeError("choice-Block in Kconfig.system nicht gefunden!")

    # Systemvarianten aus src-Unterordnern
    variants = []
    for entry in sorted(glob.glob(os.path.join(src_dir, "*"))):
        if os.path.isdir(entry):
            name = os.path.basename(entry)
            about_path = os.path.join(entry, "about.txt")
            if os.path.isfile(about_path):
                with open(about_path, "r") as af:
                    helptext = af.read().strip()
            else:
                helptext = "keine Hilfe vorhanden, da keine about.txt im Ordner gefunden"
            variants.append((name, helptext))

    # Baue neuen choice-Block
    choice_lines = []
    choice_lines.append("choice\n")
    choice_lines.append("    prompt \"Systemvariante\"\n")
    if variants:
        choice_lines.append(f"    default SYSTEM_{variants[0][0]}\n")
    choice_lines.append("    help\n")
    choice_lines.append("        Mit [?] kann zu jeder Systemvariante der Inhalt der about.txt Datei\n")
    choice_lines.append("        aus dem jeweiligen src Ordner angezeigt werden.\n")
    for name, helptext in variants:
        choice_lines.append(f"config SYSTEM_{name}\n")
        choice_lines.append(f"    bool \"{name}\"\n")
        choice_lines.append("    help\n")
        for line in helptext.splitlines():
            choice_lines.append(f"        {line}\n")
    choice_lines.append("endchoice\n")

    # Überschreibe Kconfig.system direkt
    with open(kconfig_path, "w") as f:
        f.writelines(lines[:choice_start])
        f.writelines(choice_lines)
        f.writelines(lines[choice_end+1:])

def main():
    config_file = ".config"
    src_dir = "src"
    kconfig_path = os.path.join("configmenu", "Kconfig.system")

    # Erzeuge dynamische Kconfig.system direkt aus sich selbst
    generate_kconfig_system(kconfig_path, src_dir)

    # Backup der Startkonfiguration
    if os.path.exists(config_file):
        shutil.copyfile(config_file, config_file + ".bak")


    # Menü 1: Systemtyp-Auswahl
    run_menu(kconfig_path, config_file)
    # Nach Menü 1: Systemtyp-Optionen mergen
    if os.path.exists(config_file+".old"):
        merge_config(config_file+".old", config_file, ["CONFIG_SYSTEM_"])
        shutil.move(config_file+".old", config_file)

    # Systemvariante aus .config ermitteln
    system_variant = None
    if os.path.exists(config_file):
        with open(config_file) as f:
            for line in f:
                m = None
                if line.startswith("CONFIG_SYSTEM_") and line.strip().endswith("=y"):
                    m = line.strip().split("=")[0]
                if m:
                    # z.B. CONFIG_SYSTEM_pc_1715 -> pc_1715
                    system_variant = m[len("CONFIG_SYSTEM_"):]
                    break
    if not system_variant:
        print("[FEHLER] Konnte Systemvariante nicht aus .config ermitteln!")
        sys.exit(1)

    bios_mac_path = os.path.join("src", system_variant, "bios.mac")
    if not os.path.exists(bios_mac_path):
        print(f"[FEHLER] bios.mac nicht gefunden: {bios_mac_path}")
        sys.exit(1)

    # Vor Hardwaremenü: bios.mac parsen (extract)
    run_patch_bios_mac(bios_mac_path, config_file, "extract")

    # Menü 2: Hardwarevariante & Diskettenlaufwerke
    run_menu(os.path.join("configmenu", "Kconfig.hardware"), config_file)
    # Nach Menü 2: Hardware- und Laufwerksoptionen mergen
    if os.path.exists(config_file+".old"):
        merge_config(config_file+".old", config_file, ["CONFIG_DEV_", "CONFIG_CPUCLK_", "CONFIG_CPU_", "CONFIG_FDC_", "CONFIG_CRT_", "CONFIG_RAM_", "CONFIG_DRIVE_", "CONFIG_RAMDISK_"])
        shutil.move(config_file+".old", config_file)

    # Nach Hardwaremenü: bios.mac patchen
    # Systemvariante ggf. erneut aus .config ermitteln (falls geändert)
    system_variant = None
    if os.path.exists(config_file):
        with open(config_file) as f:
            for line in f:
                m = None
                if line.startswith("CONFIG_SYSTEM_") and line.strip().endswith("=y"):
                    m = line.strip().split("=")[0]
                if m:
                    system_variant = m[len("CONFIG_SYSTEM_" ):]
                    break
    if not system_variant:
        print("[FEHLER] Konnte Systemvariante nicht aus .config ermitteln!")
        sys.exit(1)
    bios_mac_path = os.path.join("src", system_variant, "bios.mac")
    if not os.path.exists(bios_mac_path):
        print(f"[FEHLER] bios.mac nicht gefunden: {bios_mac_path}")
        sys.exit(1)
    run_patch_bios_mac(bios_mac_path, config_file, "patch")

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
