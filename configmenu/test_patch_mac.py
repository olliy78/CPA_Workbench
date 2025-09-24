#!/usr/bin/env python3
"""
Automatisiertes Test-Skript für patch_mac.py

Verwendung:
    python test_patch_mac.py <systemvariante>

Ablauf:
- Liest die Kconfig.system der Systemvariante
- Ruft patch_mac.py extract auf
- Liest die entstandene .config
- Für jeden Parameter: Setzt systematisch den Wert auf den ersten zulässigen Wert
- Gibt Testschritt aus
- Ruft patch_mac.py patch auf
- Löscht .config
- Ruft patch_mac.py extract erneut auf
- Prüft, ob die Änderung übernommen wurde
- Gibt Ergebnis (OK/Fehler) aus
- Am Ende Zusammenfassung
"""
import os
import sys
import subprocess
import re
import shutil
from termcolor import colored

def parse_kconfig_system(path):
    """Extrahiere alle konfigurierbaren Parameter und deren Werte aus Kconfig.system."""
    params = []
    if not os.path.exists(path):
        print(f"[WARN] Kconfig.system nicht gefunden: {path}")
        return params
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("config "):
            config_name = line.split()[1]
            # Suche nach help block
            help_source = None
            help_key = None
            help_value = None
            j = i + 1
            while j < len(lines):
                l2 = lines[j].strip()
                if l2.startswith("help"):
                    k = j + 1
                    while k < len(lines):
                        l3 = lines[k].strip()
                        if l3.startswith("source="):
                            parts = l3.split()
                            src = None
                            key = None
                            value = None
                            for part in parts:
                                if part.startswith("source="):
                                    src = part.split("=",1)[1]
                                elif "=" in part:
                                    kv = part.split("=",1)
                                    key = kv[0]
                                    value = kv[1]
                            help_source = src
                            help_key = key
                            help_value = value
                            break
                        if l3 == "" or l3.startswith("bool") or l3.startswith("config "):
                            break
                        k += 1
                    break
                if l2.startswith("config "):
                    break
                j += 1
            if help_source and help_key and help_value:
                params.append({
                    "config_name": config_name,
                    "source": help_source,
                    "key": help_key,
                    "value": help_value
                })
        i += 1
    return params

def read_config(path):
    vals = {}
    if not os.path.exists(path):
        return vals
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r'^(# )?(CONFIG_\w+) ?(=y|=n|is not set)?', line)
            if m:
                vals[m.group(2)] = line.strip()
    return vals

def write_config(path, vals):
    with open(path, "w", encoding="utf-8") as f:
        for v in vals.values():
            f.write(v + "\n")

def run_patch_mac(mode, config_path, system_variant):
    subprocess.run([
        sys.executable, os.path.join("configmenu", "patch_mac.py"), mode, config_path, system_variant
    ], check=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: test_patch_mac.py <systemvariante> [step=xx|step=singlestep|step=all]")
        sys.exit(1)
    system_variant = sys.argv[1]
    step_mode = None
    step_idx = None
    if len(sys.argv) > 2 and sys.argv[2].startswith("step="):
        step_mode = sys.argv[2][5:]
        if step_mode.isdigit():
            step_idx = int(step_mode) - 1
    kconfig_path = os.path.join("configmenu", system_variant, "Kconfig.system")
    config_path = ".config"
    params = parse_kconfig_system(kconfig_path)
    if not params:
        print("Keine Parameter gefunden!")
        sys.exit(1)
    run_patch_mac("extract", config_path, system_variant)
    orig_config = read_config(config_path)
    test_results = []
    total_steps = len(params)
    def pause():
        input("Weiter mit beliebiger Taste ...")

    # Bestimme zu testende Schritte
    if step_mode == "all":
        step_range = range(total_steps)
    elif step_mode == "singlestep":
        step_range = range(total_steps)
    elif step_idx is not None:
        step_range = [step_idx]
    else:
        step_range = range(total_steps)

    for idx in step_range:
        param = params[idx]
        config_key = f"CONFIG_{param['config_name']}"
        new_config = orig_config.copy()
        for k in new_config:
            if k == config_key:
                new_config[k] = f"{config_key}=y"
            elif k.startswith("CONFIG_"):
                new_config[k] = f"# {k} is not set"
        write_config(config_path, new_config)
        print(f"Testschritt {idx+1}: Setze {config_key} -> {param['key']}={param['value']}")
        run_patch_mac("patch", config_path, system_variant)
        os.remove(config_path)
        run_patch_mac("extract", config_path, system_variant)
        result_config = read_config(config_path)
        ok = result_config.get(config_key, "").endswith("=y")
        if ok:
            print(colored(f"Testschritt {idx+1} OK", "green"))
        else:
            print(colored(f"Testschritt {idx+1} NICHT OK", "red"))
        test_results.append(ok)
        # Pausenlogik
        if step_mode == "singlestep":
            pause()
        elif step_mode is None and not ok:
            pause()

    # Zusammenfassung
    total = len(test_results)
    ok_count = sum(test_results)
    fail_count = total - ok_count
    print("\nZusammenfassung:")
    print(f"Testschritte: {total}")
    print(colored(f"OK: {ok_count}", "green"))
    print(colored(f"Fehler: {fail_count}", "red"))

    print("\nStelle ursprüngliche Konfiguration wieder her ...")
    write_config(config_path, orig_config)
    run_patch_mac("patch", config_path, system_variant)
    print(colored("Ursprüngliche Konfiguration wurde wiederhergestellt.", "cyan"))

if __name__ == "__main__":
    main()
