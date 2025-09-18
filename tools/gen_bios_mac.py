#!/usr/bin/env python3
"""
Generiert eine konfigurierte bios.mac aus einer Vorlage und einer Kconfig .config
Nutzt Platzhalter wie @RAMKB@, @CRT@, ... in der Vorlage und ersetzt sie durch Werte aus .config
"""
import sys
import re

if len(sys.argv) != 3:
    print("Usage: gen_bios_mac.py <template_bios.mac> <.config>")
    sys.exit(1)

template_path = sys.argv[1]
config_path = sys.argv[2]

# Lese Kconfig .config
config = {}
with open(config_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith('CONFIG_'):
            key, val = line.split('=', 1)
            config[key[7:]] = val.strip('"')

# Ersetze Platzhalter in bios.mac
with open(template_path) as f:
    for line in f:
        def repl(m):
            var = m.group(1)
            return config.get(var, m.group(0))
        print(re.sub(r'@([A-Z0-9_]+)@', repl, line), end='')
