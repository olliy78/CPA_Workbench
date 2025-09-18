# ------------------------------------------------------------------------------
# Makefile für das CP/A BIOS-Projekt und die Systemdisketten-Erstellung
# ------------------------------------------------------------------------------
#
# Dieses Makefile steuert den Bau des CP/A-Betriebssystems (@OS.COM) und die
# Erstellung eines CP/M-kompatiblen Systemdisketten-Images. Es unterstützt die
# Varianten BC (A5120) und PC (PC1715) und bietet flexible Targets für beide.
#
# Wichtige Targets:
#   make os           - Baut das Betriebssystem (@OS.COM) für das gewählte TARGET
#   make diskImage    - Erstellt das Diskettenimage im build/-Verzeichnis
#   make writeImage   - Schreibt das Diskettenimage auf ein physikalisches Laufwerk
#   make clean        - Entfernt temporäre und finale Dateien
#
# TARGET-Auswahl:
#   Standard ist BC (A5120). Für PC1715: make PC os, make PC diskImage, ...
#   Alternativ: make TARGET=PC os
#
# Beispiele:
#   make os                # Baut @OS.COM für BC (A5120)
#   make PC os             # Baut @OS.COM für PC1715
#   make diskImage         # Erstellt Diskettenimage für BC
#   make PC diskImage      # Erstellt Diskettenimage für PC1715
#   make writeImage        # Schreibt Diskettenimage (BC) auf Laufwerk
#   make PC writeImage     # Schreibt Diskettenimage (PC) auf Laufwerk
#   make clean             # Entfernt alle temporären Dateien
#
# Hinweise:
#   - Die Quelltexte für BC liegen in src/bc_a5120, für PC in src/pc_1715
#   - Der Bootsektor liegt in src/boot_sector/bootsecBC.bin bzw. bootsecPC.bin
#   - Das Systemfile @OS.COM wird im build/-Verzeichnis erzeugt
#   - Das Diskettenimage wird als build/cpadisk.img abgelegt
# ------------------------------------------------------------------------------

# Default TARGET ist BC (A5120)
TARGET ?= BC

# Betriebssystem erkennen (für Wine unter Linux)
OS := $(shell uname)
# Name des CP/M-Emulators
CPMEXE = cpm.exe
# Arbeits- und Ausgabeverzeichnis für Build-Produkte
BUILD_DIR = build
# Verzeichnis mit Build-Tools (z.B. m80.com, linkmt.com)
TOOLS_DIR = tools
# Verzeichnisse je nach TARGET
ifeq ($(TARGET),PC)
SRC_DIR = src/pc_1715
PREBUILT_DIR = prebuilt/pc_17
BOOTSECTOR = src/boot_sector/bootsecPC.bin
else
SRC_DIR = src/bc_a5120
PREBUILT_DIR = prebuilt/bc_a5120
BOOTSECTOR = src/boot_sector/bootsecBC.bin
endif

# Name und Pfad der Zieldatei
OS_TARGET = $(BUILD_DIR)/@os.com

# CPM-Tool-Aufruf je nach Betriebssystem
ifeq ($(OS),Linux)
CPM = wine $(CPMEXE)
else
CPM = $(CPMEXE)
endif

# Systemdisk-Image-Konfiguration
TMP_IMAGE = $(BUILD_DIR)/cpa780fs.img
FINAL_IMAGE = $(BUILD_DIR)/cpadisk.img
SYSTEMNAME = 0:@os.com
DISKDEF = cpa780_withoutBoot
ADDITIONS_DIR = additions
CPMCP = $(TOOLS_DIR)/cpmcp
CPMLS = $(TOOLS_DIR)/cpmls
GW = gw
CFG = cpaFormates.cfg
FORMAT = cpa.780

# Targets für TARGET-Auswahl
.PHONY: BC PC
BC:
	@if [ -z "$(MAKECMDGOALS)" ] || [ "$(MAKECMDGOALS)" = "BC" ] || [ "$(MAKECMDGOALS)" = "PC" ]; then \
	  $(MAKE) help; \
	fi
PC:
	@if [ -z "$(MAKECMDGOALS)" ] || [ "$(MAKECMDGOALS)" = "BC" ] || [ "$(MAKECMDGOALS)" = "PC" ]; then \
	  $(MAKE) help; \
	fi


# Haupttargets
	BC:
		@if [ "$(filter-out BC PC,$(MAKECMDGOALS))" = "" ]; then \
.PHONY: help all os diskImage writeImage clean

# Standard-Target: Hilfe anzeigen
all: help
	PC:
		@if [ "$(filter-out BC PC,$(MAKECMDGOALS))" = "" ]; then \

# Hilfe-Target
help:
	@echo "Verfügbare Targets für das CP/A-Projekt:"
	@echo "  make os           - Baut das Betriebssystem (@os.com) für das gewählte TARGET (BC/PC)"
	@echo "  make diskImage    - Erstellt das Diskettenimage im build/-Verzeichnis"
	@echo "  make writeImage   - Schreibt das Diskettenimage auf ein physikalisches Laufwerk"
	@echo "  make clean        - Entfernt temporäre und finale Dateien"
	@echo "  make BC <target>  - Baut für BC (A5120) (z.B. make BC os)"
	@echo "  make PC <target>  - Baut für PC (PC1715) (z.B. make PC os)"
	@echo "  make help         - Zeigt diese Hilfe an"
	@echo ""
	@echo "Beispiele:"
	@echo "  make os                # Baut @os.com für BC (A5120)"
	@echo "  make PC os             # Baut @os.com für PC1715"
	@echo "  make diskImage         # Erstellt Diskettenimage für BC"
	@echo "  make PC diskImage      # Erstellt Diskettenimage für PC1715"
	@echo "  make writeImage        # Schreibt Diskettenimage (BC) auf Laufwerk"
	@echo "  make PC writeImage     # Schreibt Diskettenimage (PC) auf Laufwerk"
	@echo "  make clean             # Entfernt alle temporären Dateien"

# OS bauen (Betriebssystem @OS.COM)
os: $(OS_TARGET)

# Build-Regel: Erzeuge @OS.COM im build/-Verzeichnis
# Abhaengigkeiten: Quelltexte und vorgefertigte ERL
$(OS_TARGET): $(SRC_DIR)/bios.mac $(PREBUILT_DIR)/bdos.erl $(PREBUILT_DIR)/ccp.erl $(PREBUILT_DIR)/cpabas.erl
	@echo "---------------------------------------------------"
	@echo "Generieren von CP/A ... @OS.COM (TARGET=$(TARGET))"
	@echo "---------------------------------------------------"
	cp $(SRC_DIR)/*.mac $(BUILD_DIR)/
	cp $(PREBUILT_DIR)/*.erl $(BUILD_DIR)/
	cp $(TOOLS_DIR)/m80.com $(TOOLS_DIR)/linkmt.com $(TOOLS_DIR)/cpm.exe $(BUILD_DIR)/ 2>/dev/null || true
	cd $(BUILD_DIR) && $(CPM) m80 =bios/L | tee bios.log
	cd $(BUILD_DIR) && $(CPM) m80 bios.erl=bios
	@diff=$$(grep '/p:' $(BUILD_DIR)/bios.log | sed 's/[^[:print:]]//g' | sed -n 's/.*\/p:[[:space:]]*\([0-9A-Fa-f]\{4,\}\).*/\1/p' | head -1); \
	if [ -z "$$diff" ]; then echo "Fehler: Kein /p:-Wert in bios.log gefunden!"; exit 1; fi; \
	echo "Verwende berechneten Linkwert: $$diff"; \
	cd $(BUILD_DIR) && $(CPM) linkmt @OS=cpabas,ccp,bdos,bios/p:$$diff
	rm -f $(BUILD_DIR)/*.syp $(BUILD_DIR)/*.rel $(BUILD_DIR)/*.mac $(BUILD_DIR)/*.erl $(BUILD_DIR)/bios.log $(BUILD_DIR)/$(CPMEXE) $(BUILD_DIR)/m80.com $(BUILD_DIR)/linkmt.com
	@echo "..................................................."
	@echo "Fertig !!!!!!"

# Diskettenimage erzeugen
diskImage: $(FINAL_IMAGE)
	@echo "[INFO] Target 'diskImage' abgeschlossen. Diskettenimage ist bereit für TARGET=$(TARGET)."

# Image bauen: Abhängigkeit von OS und Bootsektor
$(FINAL_IMAGE): $(BOOTSECTOR) $(OS_TARGET)
	@echo "[STEP 1] Erzeuge leeres temporäres Image: $(TMP_IMAGE)"
	dd if=/dev/zero bs=1024 count=780 2>/dev/null | tr '\0' '\345' | dd of=$(TMP_IMAGE) bs=1024 count=780 2>/dev/null
	@echo "[STEP 2] Kopiere CPA-System (@os.com) ins Image"
	$(CPMCP) -f $(DISKDEF) $(TMP_IMAGE) $(OS_TARGET) $(SYSTEMNAME)
	@echo "[STEP 3] Kopiere Dateien aus '$(ADDITIONS_DIR)' ins Image"
	@for f in $(ADDITIONS_DIR)/*; do \
	  if [ -f "$$f" ]; then \
	    fname=$$(basename "$$f"); \
	    echo "  [ADD] $$fname"; \
	    $(CPMCP) -f $(DISKDEF) $(TMP_IMAGE) $$f 0:$$fname; \
	  fi; \
	done
	@echo "[STEP 4] Zeige Dateien im Image (nach dem Kopieren):"
	$(CPMLS) -Ff $(DISKDEF) $(TMP_IMAGE)
	@echo "[STEP 5] Füge Bootsektor hinzu und erstelle finales Image: $(FINAL_IMAGE)"
	(dd if=$(BOOTSECTOR) bs=128 2>/dev/null; dd if=$(TMP_IMAGE) bs=1024 2>/dev/null) > $(FINAL_IMAGE)
	rm -f $(TMP_IMAGE)
	@echo "[DONE] Diskettenimage erstellt: $(FINAL_IMAGE)"

# Diskettenimage auf physikalisches Laufwerk schreiben
writeImage: $(FINAL_IMAGE)
	@echo "[STEP] Schreibe Diskettenimage mit gw auf physikalisches Laufwerk (TARGET=$(TARGET))"
	$(GW) write --diskdefs=$(CFG) --format=$(FORMAT) $(FINAL_IMAGE)
	@echo "[FERTIG] Diskettenimage mit gw auf Laufwerk geschrieben."

# Aufräumen
clean:
	@echo "[STEP] Entferne temporäre und finale Dateien..."
	rm -f $(TMP_IMAGE) $(FINAL_IMAGE) $(BUILD_DIR)/* $(SRC_DIR)/*.erl $(SRC_DIR)/*.rel $(SRC_DIR)/*.syp
	@echo "[FERTIG] Aufgeräumt."
