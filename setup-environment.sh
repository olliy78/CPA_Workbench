#!/bin/bash
# CP/A Build Environment Setup für Git Bash
# Setzt alle benötigten PATH-Variablen und startet eine interaktive Shell

# Locale für UTF-8-Umlaute setzen
export LANG=de_DE.UTF-8
export LC_ALL=de_DE.UTF-8

# Farben für schönere Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=============================================${NC}"
echo -e "${YELLOW}  CP/A Build Environment Setup (Git Bash)${NC}"
echo -e "${CYAN}=============================================${NC}"
echo ""

# Zum Script-Verzeichnis wechseln (funktioniert auch wenn von woanders aufgerufen)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}[INFO] Arbeitsverzeichnis: $(pwd)${NC}"
echo ""

# Originalen PATH sichern
export ORIGINAL_PATH="$PATH"

# CP/A Tools zum PATH hinzufügen (Windows-Pfade in Unix-Format konvertieren)
PROJECT_DIR="$(pwd)"

# Unix-Tools ZUERST (für rm, awk, grep, sed), dann selektiv Windows-Tools
export PATH="/usr/bin:/bin:$PROJECT_DIR/tools/greaseweazle:$PROJECT_DIR/tools/python3/Scripts:$PROJECT_DIR/tools/python3:$PROJECT_DIR/tools/gnu:./:$PATH"

# Ausgabe des aktuellen PATH
echo -e "${YELLOW}[INFO] PATH: $PATH${NC}"

# Make testen
echo ""
echo -e "${YELLOW}[INFO] Teste make, Python und Greanweazle ... ${NC}"


if command -v make &> /dev/null; then
    MAKE_VERSION=$(make --version 2>/dev/null | head -1)
    echo -e "  ${GREEN}[✓] make: $MAKE_VERSION${NC}"
else
    echo -e "  ${RED}[✗] make: Nicht im PATH verfügbar${NC}"
fi

# Python testen
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo -e "  ${GREEN}[✓] python: $PYTHON_VERSION${NC}"
else
    echo -e "  ${RED}[✗] python: Nicht verfügbar${NC}"
fi

# greaseweazle testen
if command -v gw &> /dev/null; then
    GREASEWEAZLE_VERSION=$(gw info 2>&1)
    echo -e "  ${GREEN}[✓] greaseweazle: $GREASEWEAZLE_VERSION${NC}"
else
    echo -e "  ${RED}[✗] greaseweazle: Nicht verfügbar${NC}"
fi

# Alias setzen
alias python=python3
alias ll="ls -alh"


echo ""
echo -e "${CYAN}=============================================${NC}"
echo -e "${YELLOW}  Umgebung bereit! make help:\n\n"
make help
echo -e "${CYAN}=============================================${NC}"
echo ""

echo ""

# PS1 (Prompt) anpassen um zu zeigen, dass wir in der CP/A-Umgebung sind
export PS1="\[\033[1;32m\][CP/A]\[\033[0m\] \[\033[1;34m\]\w\[\033[0m\]\$ "

# Neue interaktive Bash-Session (ersetzt das Skript, Fenster bleibt offen)
exec bash --rcfile <(echo "
# CP/A Build Environment
alias ll='ls -alh'
export PS1='\[\033[1;32m\][CP/A]\[\033[0m\] \[\033[1;34m\]\w\[\033[0m\]$ '
echo -e '\033[1;32m[CP/A Build Environment aktiv]\033[0m'
echo -e 'Verwenden Sie \"exit\" um die Umgebung zu verlassen.'
")

# Diese Zeile wird nach exec nicht mehr ausgeführt
# echo ""
# echo -e "${GREEN}[INFO] CP/A Build Environment beendet${NC}"
