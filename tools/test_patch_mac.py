#!/usr/bin/env python3
# Copyright (c) 2026 Olaf Krieger
# SPDX-License-Identifier: MIT
"""
test_patch_mac.py - Automatisierte Roundtrip-Tests für patch_mac.py

Dieses Skript überprüft die Patch- und Extract-Funktionalität von patch_mac.py
für eine gegebene Systemvariante. Für jeden konfigurierbaren Parameter wird
getestet, ob ein gesetzter Wert korrekt in die .mac-Datei gepatcht und danach
wieder korrekt extrahiert werden kann (Roundtrip-Test).

Testablauf für jeden Parameter:
    1. Nur diesen Parameter in der .config setzen, alle anderen auf 'is not set'
    2. patch_mac.py patch aufrufen (Wert in .mac schreiben)
    3. .config löschen
    4. patch_mac.py extract aufrufen (Wert aus .mac lesen)
    5. Prüfen ob der gelesene Wert dem gesetzten Wert entspricht

Spezielle Testfälle:
    - bool: Setzt CONFIG_KEY=y, erwartet =y nach Extract
    - string: Setzt CONFIG_KEY="Test Kommand", erwartet gleichen Wert
    - hexstring: Testet zwei Werte: '123CAFFEh' (gesetzt) und 'is not set' (=0)

Ergebnis:
    - Ausgabe OK/Fehler für jeden Testschritt (farbig mit termcolor)
    - Zusammenfassung aller Testergebnisse am Ende
    - Automatische Wiederherstellung der ursprünglichen Konfiguration

Autor:   Olaf Krieger
Lizenz:  MIT (siehe LICENSE)

Verwendung:
    python test_patch_mac.py <systemvariante> [loglevel=debug|loglevel=info] [step=xx|step=singlestep|step=all]

Optionale Argumente:
    loglevel=debug   Ausführliche Debug-Ausgaben (wird an patch_mac.py durchgereicht)
    step=3           Nur Testschritt 3 ausführen
    step=singlestep  Alle Schritte mit Pause nach jedem Schritt
    step=all         Alle Schritte ohne Pause
"""
import os
import sys
import subprocess
import re
import shutil
from termcolor import colored

# ============================================================================
# Kconfig.system-Parser (vereinfachte Version für Testparameter)
# ============================================================================

def parse_kconfig_system(path):
    """Konfigurierbare Parameter aus Kconfig.system für Tests extrahieren.

    Im Gegensatz zu patch_mac.parse_kconfig_system() wird hier für jeden
    Parameter nur ein einzelnes key=value-Paar extrahiert (nicht alle),
    da die Tests jeden Parameter isoliert testen.

    Returns:
        list: Liste von Dicts mit config_name, source, key, value
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
            # Suche nach dem help-Block mit source=-Zeile
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

# ============================================================================
# Hilfs-Funktionen für .config-Datei und patch_mac.py-Aufruf
# ============================================================================

def read_config(path):
    """Konfigurationsdatei (.config) lesen und als Dict zurückgeben.

    Erkennt alle CONFIG_*-Zuweisungen einschließlich Strings, Bool-Werten
    und 'is not set'-Markierungen.

    Returns:
        dict: CONFIG_KEY → vollständige Zeile (z.B. 'CONFIG_X=y' oder '# CONFIG_X is not set')
    """
    vals = {}
    if not os.path.exists(path):
        return vals
    with open(path, encoding="utf-8") as f:
        for line in f:
            # Erkenne alle Zuweisungen, inkl. ="...", =..., =y, =n, is not set
            m = re.match(r'^(# )?(CONFIG_\w+)\s*(=.*| is not set)?', line)
            if m:
                vals[m.group(2)] = line.strip()
    return vals

def write_config(path, vals):
    """Config-Dict als .config-Datei schreiben (sortiert nach Schlüsselname)."""
    with open(path, "w", encoding="utf-8") as f:
        for k in sorted(vals.keys()):
            f.write(vals[k] + "\n")

def run_patch_mac(mode, config_path, system_variant):
    """patch_mac.py im angegebenen Modus als Unterprozess aufrufen.

    Leitet den aktuellen loglevel an patch_mac.py weiter.
    Wirft subprocess.CalledProcessError bei Fehlern.
    """
    args = [
        sys.executable, os.path.join("tools", "patch_mac.py"), mode, config_path, system_variant
    ]
    if loglevel:
        args.append(f"loglevel={loglevel}")
    subprocess.run(args, check=True)

# ============================================================================
# Hauptfunktion - Teststeuerung und Ergebnisausgabe
# ============================================================================

def main():
    """Gesamten Testablauf steuern:

    1. Systemvariante und Kommandozeilenoptionen parsen
    2. Alle konfigurierbaren Parameter aus Kconfig.system extrahieren
    3. Ausgangskonfiguration sichern (für spätere Wiederherstellung)
    4. Für jeden Parameter: Roundtrip-Test (setzen → patchen → extrahieren → prüfen)
    5. Zusammenfassung ausgeben und Originalkonfiguration wiederherstellen
    """
    if len(sys.argv) < 2:
        print("Usage: test_patch_mac.py <systemvariante> [loglevel=debug|loglevel=info] [step=xx|step=singlestep|step=all]")
        sys.exit(1)
    system_variant = sys.argv[1]
    global loglevel
    loglevel = "info"
    step_mode = None
    step_idx = None
    # Kommandozeilen-Argumente parsen: loglevel und step-Optionen erkennen
    for arg in sys.argv[2:]:
        if arg.startswith("loglevel="):
            loglevel = arg.split("=",1)[1].lower()
        elif arg.startswith("step="):
            step_mode = arg[5:]
            if step_mode.isdigit():
                step_idx = int(step_mode) - 1
    # Kconfig.system parsen und alle testbaren Parameter extrahieren
    kconfig_path = os.path.join("config", system_variant, "Kconfig.system")
    config_path = ".config"
    # Extrahiere alle konfigurierbaren Parameter
    params = parse_kconfig_system(kconfig_path)
    if not params:
        print("Keine Parameter gefunden!")
        sys.exit(1)
    # Aktuelle Konfiguration als Ausgangsbasis sichern
    run_patch_mac("extract", config_path, system_variant)
    orig_config = read_config(config_path)

    test_results = []   # Ergebnisliste: True=OK, False=Fehler
    total_steps = len(params)
    def pause():
        """Warten auf Benutzereingabe (für Singlestep-Modus)."""
        input("Weiter mit Enter Taste ...")

    # Bestimme, welche Testschritte ausgeführt werden sollen (alle, einzeln oder Singlestep)
    if step_mode == "all":
        step_range = range(total_steps)
    elif step_mode == "singlestep":
        step_range = range(total_steps)
    elif step_idx is not None:
        step_range = [step_idx]
    else:
        step_range = range(total_steps)


    # Initial-Zustand: Alle Parameter auf 'is not set' setzen und .mac patchen
    # Dies schafft eine saubere Ausgangsbasis für die einzelnen Tests
    all_is_not_set = orig_config.copy()
    for k in all_is_not_set:
        if k.startswith("CONFIG_"):
            all_is_not_set[k] = f"# {k} is not set"
    write_config(config_path, all_is_not_set)
    run_patch_mac("patch", config_path, system_variant)

    # Haupt-Testschleife: Jeden Parameter einzeln testen (Roundtrip)
    for idx in step_range:
        param = params[idx]
        config_key = f"CONFIG_{param['config_name']}"
        new_config = all_is_not_set.copy()
        is_string = (param.get('value', None) == 'string')
        is_hexstring = (param.get('value', None) == 'hexstring')

        # Hexstring-Typ: Zwei Testfälle (Wert gesetzt + Wert nicht gesetzt)
        if is_hexstring:
            # Testfall 1: Hexstring-Wert setzen (123CAFFEh)
            new_config[config_key] = f'{config_key}="123CAFFEh"'
            write_config(config_path, new_config)
            if loglevel == "debug":
                print(f"[DEBUG] .config vor Patch: {config_key} = {new_config[config_key]}")
                mac_path = os.path.join("src", system_variant, param['source'] if param.get('source') else "bios.mac")
                if os.path.exists(mac_path):
                    with open(mac_path, encoding="utf-8") as f:
                        for line in f:
                            if param['key'] in line and not line.lstrip().startswith(';'):
                                print(f"[DEBUG] .mac vor Patch: {line.rstrip()}")
                                break
            print(f"Testschritt {idx+1}a: Setze {config_key}='123CAFFEh' (hexstring)")
            run_patch_mac("patch", config_path, system_variant)
            os.remove(config_path)
            run_patch_mac("extract", config_path, system_variant)
            result_config = read_config(config_path)
            ok = result_config.get(config_key, "") == f'{config_key}="123CAFFEh"'
            if ok:
                print(colored(f"Testschritt {idx+1}a OK", "green"))
            else:
                print(colored(f"Testschritt {idx+1}a NICHT OK", "red"))
            test_results.append(ok)
            if step_mode == "singlestep":
                pause()
            elif step_mode is None and not ok:
                pause()
            elif step_idx is not None and not ok:
                pause()
            # Testfall 2: Hexstring-Wert auf 'is not set' (soll als 0 in .mac erscheinen)
            new_config = all_is_not_set.copy()
            new_config[config_key] = f'# {config_key} is not set'
            write_config(config_path, new_config)
            if loglevel == "debug":
                print(f"[DEBUG] .config vor Patch: {config_key} = {new_config[config_key]}")
                mac_path = os.path.join("src", system_variant, param['source'] if param.get('source') else "bios.mac")
                if os.path.exists(mac_path):
                    with open(mac_path, encoding="utf-8") as f:
                        for line in f:
                            if param['key'] in line and not line.lstrip().startswith(';'):
                                print(f"[DEBUG] .mac vor Patch: {line.rstrip()}")
                                break
            print(f"Testschritt {idx+1}b: Setze {config_key} is not set (hexstring)")
            run_patch_mac("patch", config_path, system_variant)
            os.remove(config_path)
            run_patch_mac("extract", config_path, system_variant)
            result_config = read_config(config_path)
            ok = result_config.get(config_key, "") == f'# {config_key} is not set'
            if ok:
                print(colored(f"Testschritt {idx+1}b OK", "green"))
            else:
                print(colored(f"Testschritt {idx+1}b NICHT OK", "red"))
            test_results.append(ok)
            if step_mode == "singlestep":
                pause()
            elif step_mode is None and not ok:
                pause()
            elif step_idx is not None and not ok:
                pause()
            continue

        # String-Parameter: Testtext "Test Kommand" setzen
        # Bool-Parameter: Auf =y setzen
        if is_string:
            new_config[config_key] = f'{config_key}="Test Kommand"'
        else:
            new_config[config_key] = f"{config_key}=y"
        write_config(config_path, new_config)
        if loglevel == "debug":
            print(f"[DEBUG] .config vor Patch: {config_key} = {new_config[config_key]}")
            mac_path = os.path.join("src", system_variant, param['source'] if param.get('source') else "bios.mac")
            if os.path.exists(mac_path):
                with open(mac_path, encoding="utf-8") as f:
                    for line in f:
                        if param['key'] in line and not line.lstrip().startswith(';'):
                            print(f"[DEBUG] .mac vor Patch: {line.rstrip()}")
                            break
        print(f"Testschritt {idx+1}: Setze {config_key} (loglevel={loglevel})")
        run_patch_mac("patch", config_path, system_variant)
        os.remove(config_path)
        run_patch_mac("extract", config_path, system_variant)
        result_config = read_config(config_path)
        if is_string:
            ok = result_config.get(config_key, "").startswith(f'{config_key}="Test Kommand"')
        else:
            ok = result_config.get(config_key, "").endswith("=y")
        if ok:
            print(colored(f"Testschritt {idx+1} OK", "green"))
        else:
            print(colored(f"Testschritt {idx+1} NICHT OK", "red"))
        test_results.append(ok)
        if step_mode == "singlestep":
            pause()
        elif step_mode is None and not ok:
            pause()
        elif step_idx is not None and not ok:
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
