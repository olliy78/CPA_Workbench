#!/usr/bin/env python3
"""
Automatisiertes Test-Skript für patch_mac.py

Dieses Skript automatisiert die Überprüfung der Patch- und Extract-Funktionalität von patch_mac.py
für eine gegebene Systemvariante. Es testet für jeden konfigurierbaren Parameter, ob ein gesetzter Wert
korrekt in die .mac-Datei gepatcht und anschließend wieder ausgelesen werden kann.


Verwendung:
    python test_patch_mac.py <systemvariante> [loglevel=debug|loglevel=info] [step=xx|step=singlestep|step=all]

Optionale Argumente:
    loglevel=debug   Aktiviere ausführliche Debug-Ausgaben (wird an patch_mac.py durchgereicht)
    loglevel=info    Standard, weniger Ausgaben
    step=...         Einzelne Testschritte oder Step-Modi

Ablauf:
    1. Liest die Kconfig.system der Systemvariante und extrahiert alle konfigurierbaren Parameter.
    2. Ruft patch_mac.py im Modus 'extract' auf, um die aktuelle .config zu erzeugen.
    3. Für jeden Parameter:
        a) Setzt nur diesen Parameter auf '=y', alle anderen auf 'is not set'.
        b) Ruft patch_mac.py im Modus 'patch' auf, um die .mac-Datei zu ändern.
        c) Löscht die .config.
        d) Ruft patch_mac.py erneut im Modus 'extract' auf, um die Werte zurückzulesen.
        e) Prüft, ob der gesetzte Wert korrekt übernommen wurde.
        f) Gibt das Ergebnis (OK/Fehler) aus.
    4. Gibt eine Zusammenfassung aller Testergebnisse aus.
    5. Stellt am Ende die ursprüngliche Konfiguration wieder her.
"""
import os
import sys
import subprocess
import re
import shutil
from termcolor import colored

def parse_kconfig_system(path):
    """
    Extrahiere alle konfigurierbaren Parameter und deren Werte aus Kconfig.system.
    Liefert eine Liste von Dicts mit den Feldern:
        - config_name: Name des Parameters (ohne CONFIG_)
        - source: Ziel-Datei (z.B. bios.mac)
        - key: Name des Assembler-Labels
        - value: Wert, der für diesen Parameter gesetzt werden soll
    """
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
    """
    Liest die .config-Datei und gibt ein Dict mit allen CONFIG_*-Einträgen zurück.
    Key: CONFIG_<name>, Value: komplette Zeile (inkl. Kommentar, =y, is not set)
    """
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
    """
    Schreibt das gegebene Dict (Key: CONFIG_<name>, Value: Zeile) in die .config-Datei.
    Jede Zeile entspricht einem Konfigurationsparameter.
    """
    with open(path, "w", encoding="utf-8") as f:
        for v in vals.values():
            f.write(v + "\n")

def run_patch_mac(mode, config_path, system_variant):
    """
    Ruft patch_mac.py im angegebenen Modus (extract/patch) für die gegebene Systemvariante auf.
    Übergibt die .config-Datei und den loglevel als Argument.
    """
    args = [
        sys.executable, os.path.join("configmenu", "patch_mac.py"), mode, config_path, system_variant
    ]
    if loglevel:
        args.append(f"loglevel={loglevel}")
    subprocess.run(args, check=True)

def main():
    """
    Hauptfunktion: Steuert den gesamten Testablauf.
    - Liest die Systemvariante und extrahiert alle Parameter.
    - Führt für jeden Parameter einen Patch- und Extract-Test durch.
    - Prüft, ob die Änderung korrekt übernommen wurde.
    - Gibt eine Zusammenfassung aus und stellt die ursprüngliche Konfiguration wieder her.
    """
    if len(sys.argv) < 2:
        print("Usage: test_patch_mac.py <systemvariante> [loglevel=debug|loglevel=info] [step=xx|step=singlestep|step=all]")
        sys.exit(1)
    system_variant = sys.argv[1]
    global loglevel
    loglevel = "info"
    step_mode = None
    step_idx = None
    # Argument-Parsing: loglevel und step-Optionen erkennen
    for arg in sys.argv[2:]:
        if arg.startswith("loglevel="):
            loglevel = arg.split("=",1)[1].lower()
        elif arg.startswith("step="):
            step_mode = arg[5:]
            if step_mode.isdigit():
                step_idx = int(step_mode) - 1
    kconfig_path = os.path.join("configmenu", system_variant, "Kconfig.system")
    config_path = ".config"
    # Extrahiere alle konfigurierbaren Parameter
    params = parse_kconfig_system(kconfig_path)
    if not params:
        print("Keine Parameter gefunden!")
        sys.exit(1)
    # Extrahiere die aktuelle .config als Ausgangsbasis
    run_patch_mac("extract", config_path, system_variant)
    orig_config = read_config(config_path)
    test_results = []
    total_steps = len(params)
    def pause():
        input("Weiter mit Enter Taste ...")

    # Bestimme, welche Testschritte ausgeführt werden sollen
    if step_mode == "all":
        step_range = range(total_steps)
    elif step_mode == "singlestep":
        step_range = range(total_steps)
    elif step_idx is not None:
        step_range = [step_idx]
    else:
        step_range = range(total_steps)


    # Initial: Setze alle Parameter auf 'is not set' und patche .mac
    all_is_not_set = orig_config.copy()
    for k in all_is_not_set:
        if k.startswith("CONFIG_"):
            all_is_not_set[k] = f"# {k} is not set"
    write_config(config_path, all_is_not_set)
    pause()
    run_patch_mac("patch", config_path, system_variant)
    pause()

    # Haupt-Testschleife: Für jeden Parameter einzeln testen
    for idx in step_range:
        param = params[idx]
        config_key = f"CONFIG_{param['config_name']}"
        # Setze nur diesen Parameter auf '=y' (oder String), alle anderen auf 'is not set'
        new_config = all_is_not_set.copy()
        is_string = (param.get('value', None) == 'string')
        if is_string:
            new_config[config_key] = f'{config_key}="Test Kommand"'
        else:
            new_config[config_key] = f"{config_key}=y"
        write_config(config_path, new_config)
        # Debug: Zeige Wert in .config und .mac vor Patch
        if loglevel == "debug":
            print(f"[DEBUG] .config vor Patch: {config_key} = {new_config[config_key]}")
            # Zeige relevante Zeile aus .mac
            mac_path = os.path.join("src", system_variant, "bios.mac")
            if os.path.exists(mac_path):
                with open(mac_path, encoding="utf-8") as f:
                    for line in f:
                        if param['key'] in line:
                            print(f"[DEBUG] .mac vor Patch: {line.rstrip()}")
                            break
        print(f"Testschritt {idx+1}: Setze {config_key} (loglevel={loglevel})")
        # Patche die .mac-Datei
        run_patch_mac("patch", config_path, system_variant)
        # Lösche die .config, um einen frischen Extract zu erzwingen
        os.remove(config_path)
        # Extrahiere die Werte erneut aus der .mac-Datei
        run_patch_mac("extract", config_path, system_variant)
        result_config = read_config(config_path)
        # Prüfe, ob der gesetzte Wert korrekt übernommen wurde
        if is_string:
            ok = result_config.get(config_key, "").startswith(f'{config_key}="Test Kommand"')
        else:
            ok = result_config.get(config_key, "").endswith("=y")
        if ok:
            print(colored(f"Testschritt {idx+1} OK", "green"))
        else:
            print(colored(f"Testschritt {idx+1} NICHT OK", "red"))
        test_results.append(ok)
        # Pausenlogik: Bei singlestep oder Fehler anhalten
        if step_mode == "singlestep":
            pause()
        elif step_mode is None and not ok:
            pause()

    # Zusammenfassung aller Testergebnisse
    total = len(test_results)
    ok_count = sum(test_results)
    fail_count = total - ok_count
    print("\nZusammenfassung:")
    print(f"Testschritte: {total}")
    print(colored(f"OK: {ok_count}", "green"))
    print(colored(f"Fehler: {fail_count}", "red"))

    # Ursprüngliche Konfiguration wiederherstellen
    print("\nStelle ursprüngliche Konfiguration wieder her ...")
    write_config(config_path, orig_config)
    run_patch_mac("patch", config_path, system_variant)
    print(colored("Ursprüngliche Konfiguration wurde wiederhergestellt.", "cyan"))

if __name__ == "__main__":
    main()
