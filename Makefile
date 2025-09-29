# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Makefile fuer das CP/A BIOS-Projekt und die Systemdisketten-Erstellung
# ------------------------------------------------------------------------------
#
# Dieses Makefile steuert den Bau des CP/A-Betriebssystems (@OS.COM) und die
# Erstellung eines CP/M-kompatiblen Systemdisketten-Images. Es unterstuetzt beliebige
# Systemvarianten, die als Unterordner in src/<systemvariante> und prebuilt/<systemvariante> existieren.
#
# WICHTIG: Wenn du NICHT das Konfigurationsmenue oder die .config verwenden moechtest,
# kannst du die Zeile
#   DEFAULT_SYSTEMVAR := <dein_systemname>
# am Anfang dieses Makefiles anpassen, um die gewuenschte Systemvariante festzulegen.
# Beispiel: DEFAULT_SYSTEMVAR := pc_1715
#
# Die Namen der verwendeten Ordner leiten sich direkt vom Namen der Systemvariante ab:
#   - Quelltexte:      src/<systemvariante> (z.B. src/pc_1715)
#   - Prebuilt-Files:  prebuilt/<systemvariante> (z.B. prebuilt/pc_1715)
#   - Bootsektor:      prebuilt/<systemvariante>/bootsec.bin
#
# Das Buildsystem verwendet diese Ordner automatisch, sobald du z.B. 'make pc_1715 os' aufrufst
# oder DEFAULT_SYSTEMVAR entsprechend setzt.
#
# Konfigurationsmenue:
#   make menuconfig   - Startet das mehrstufige Konfigurationsmenue fuer Systemtyp,
#                       Hardware- und Laufwerksauswahl sowie Build-Optionen.
#                       Die Konfiguration wird in .config gespeichert und die
#                       passenden BIOS-Quellen werden automatisch angepasst.
#   Das Menue bietet:
#     1. Auswahl des Systemtyps (z.B. A5120, PC1715)
#     2. Auswahl der Hardware- und Diskettenlaufwerks-Varianten
#     3. Auswahl des Build-Ausgabeformats
#     4. Hilfetexte zu allen Optionen (mit [?] im Menue)
#     5. Wizard-aehnliche Navigation durch die Konfigurationsschritte
#
# Wichtige Targets:
#   make config <target>      - Baut das gewuenschte Target (os, diskimage, diskimagehfe, diskimagescp, writeimage, ...) gemaess .config (empfohlen, reproduzierbar)
#   make os                   - Baut das Betriebssystem (@OS.COM) fuer das gewaehlte TARGET (Standard: BC, ggf. Warnung)
#   make diskimage            - Erstellt das Diskettenimage im build/-Verzeichnis (IMG-Format)
#   make diskimagehfe         - Erstellt ein HFE-Diskettenimage im build/-Verzeichnis
#   make diskimagescp         - Erstellt ein SCP-Diskettenimage im build/-Verzeichnis
#   make writeimage           - Schreibt das Diskettenimage auf ein physikalisches Laufwerk
#   make clean                - Entfernt temporaere und finale Dateien
#
# Systemvarianten:
#   Der Name der Systemvariante entspricht dem Unterordner in src/<system> und prebuilt/<system>.
#   Beispiel: make pc_1715 os verwendet src/pc_1715 und prebuilt/pc_1715.
#
# Beispiele:
#   make config os                # Baut @os.com gemaess .config (empfohlen)
#   make config diskimage         # Erstellt Diskettenimage gemaess .config
#   make config diskimagehfe      # Erstellt HFE-Image gemaess .config (wenn aktiviert)
#   make config diskimagescp      # Erstellt SCP-Image gemaess .config (wenn aktiviert)
#   make config pc_1715 os        # Baut @os.com fuer pc_1715 (ueberschreibt .config)
#   make pc_1715 os               # Baut @os.com fuer pc_1715
#   make menuconfig               # Startet das Konfigurationsmenue
#
# Hinweise:
#   - Die Quelltexte liegen in src/<systemvariante> (z.B. src/pc_1715)
#   - Der Bootsektor liegt in prebuilt/<systemvariante>/bootsec.bin
#   - Das Systemfile @OS.COM wird im build/-Verzeichnis erzeugt
#   - Das Diskettenimage wird als build/cpadisk.img abgelegt
#   - HFE- und SCP-Images werden als build/cpadisk.hfe bzw. build/cpadisk.scp abgelegt (wenn aktiviert)
#   - Die Konfiguration erfolgt ueber das Menue (menuconfig) und wird in .config gespeichert
#   - Nach Aenderung der Konfiguration sollte das System neu gebaut werden
#   - Fuer reproduzierbare Builds immer 'make config <target>' verwenden!
# ------------------------------------------------------------------------------

# Zentraler Default fuer Systemvariante (wird ueberall als Fallback verwendet)
DEFAULT_SYSTEMVAR := pc_1715
# Systemdisk-Image-Konfiguration
TMP_IMAGE = $(BUILD_DIR)/cpadisk.img.tmp
FINAL_IMAGE = $(BUILD_DIR)/cpadisk.img
HFE_IMAGE = $(BUILD_DIR)/cpadisk.hfe
SCP_IMAGE = $(BUILD_DIR)/cpadisk.scp
SYSTEMNAME = 0:@os.com
ADDITIONS_DIR = additions
GW = gw
CFG = cpaFormates.cfg
# Default Diskettenformat (wird ggf. durch .config ueberschrieben)
DEFAULT_FORMAT = cpa780
DEFAULT_IMAGE_SIZE = 780
DEFAULT_DISKDEF = cpa780_withoutBoot

# SYSTEMVAR: Name der Systemvariante (z.B. bc_a5120, pc_1715, ...)
SYSTEMVAR :=
ifeq ($(firstword $(MAKECMDGOALS)),config)
	# make config <system> <target> → Systemvariante aus .config lesen
	ifeq ($(wildcard .config),)
		SYSTEMVAR := $(DEFAULT_SYSTEMVAR)
	else
		SYSTEMVAR := $(shell awk -F'CONFIG_VARIANT_' '/^CONFIG_VARIANT_/ && $$2 ~ /=y/ {sub(/=y/,"",$$2); print tolower($$2)}' .config | head -1)
		ifeq ($(SYSTEMVAR),)
			SYSTEMVAR := $(DEFAULT_SYSTEMVAR)
		endif
	endif
else
	# make <system> <target> → Systemvariante ist erstes Argument, falls kein bekanntes Target
	ifneq ($(filter-out os diskimage diskimagehfe diskimagescp writeimage clean help all menuconfig,$(firstword $(MAKECMDGOALS))),)
		SYSTEMVAR := $(firstword $(MAKECMDGOALS))
		override MAKECMDGOALS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
	else
		# Fallback: aus .config
		ifeq ($(wildcard .config),)
			SYSTEMVAR := $(DEFAULT_SYSTEMVAR)
		else
			SYSTEMVAR := $(shell awk -F'CONFIG_VARIANT_' '/^CONFIG_VARIANT_/ && $$2 ~ /=y/ {sub(/=y/,"",$$2); print tolower($$2)}' .config | head -1)
			ifeq ($(SYSTEMVAR),)
				SYSTEMVAR := $(DEFAULT_SYSTEMVAR)
			endif
		endif
	endif
endif

# Konfigurations-Wrapper: explizit aus .config bauen
.PHONY: config
config:
	@user_target=$(word 2,$(MAKECMDGOALS)); \
	if [ -z "$$user_target" ]; then \
		echo "[INFO] Bitte gib ein Target an, z.B. 'make config os' oder 'make config diskImage'"; exit 1; \
	fi; \
	echo "[INFO] Baue explizit mit Target von Kommandozeile: Target='$$user_target'"; \
	exec $(MAKE) FROM_CONFIG=1 $$user_target;

# Warnung bei direktem Aufruf ohne config (aber nicht aus config-Target oder Wrapper heraus)
ifeq ($(FROM_CONFIG)$(FROM_WRAPPER),)
ifneq ($(MAKECMDGOALS),)
ifneq ($(firstword $(MAKECMDGOALS)),config)
$(info [INFO] Du hast 'make $(MAKECMDGOALS)' aufgerufen.)
endif
endif
endif

# Betriebssystem erkennen (fuer Wine unter Linux)
OS := $(shell uname)
# Name des CP/M-Emulators
CPMEXE = cpm.exe
# Wie CP/M-Tools auf diesem Host gestartet werden (unter Linux via wine)
ifeq ($(OS),Linux)
CPM = wine $(CPMEXE)
else
CPM = $(CPMEXE)
endif
# Arbeits- und Ausgabeverzeichnis fuer Build-Produkte
BUILD_DIR = build
# Verzeichnis mit Build-Tools (z.B. m80.com, linkmt.com)
TOOLS_DIR = tools
# Quell- und Prebuilt-Verzeichnisse dynamisch
SRC_DIR = src/$(SYSTEMVAR)
PREBUILT_DIR = prebuilt/$(SYSTEMVAR)
BOOTSECTOR = prebuilt/$(SYSTEMVAR)/bootsec.bin

# Name und Pfad der Zieldatei
OS_TARGET = $(BUILD_DIR)/@os.com

# CPM-Tool-Aufruf je nach Betriebssystem
ifeq ($(OS),Linux)
CPMCP = $(TOOLS_DIR)/cpmcp
CPMLS = $(TOOLS_DIR)/cpmls
else
CPMCP = $(TOOLS_DIR)/cpmcp.exe
CPMLS = $(TOOLS_DIR)/cpmls.exe
endif

# Keine expliziten Targets fuer Systemvarianten mehr noetig

# menuconfig: Wrapper fuer den mehrstufigen Konfigurationsprozess
.PHONY: menuconfig
menuconfig:
	@echo "Starte CPA-Mehrstufen-Konfigurationsmenue..."
	python3 config/cpa_menuconfig.py


# Haupttargets
.PHONY: help all os diskimage diskimagehfe diskimagescp writeimage clean menuconfig

# Standard-Target: Hilfe anzeigen
all: help


# Hilfe-Target
help:
	@echo "Verfuegbare Targets fuer das CP/A-Projekt:"
	@echo "  make config <target>      - Baut das gewuenschte Target (os, diskimage, diskimagehfe, diskimagescp, writeimage, ...) gemaess .config (empfohlen, reproduzierbar)"
	@echo "  make <system> <target>    - Baut fuer die angegebene Systemvariante (z.B. make pc_1715 os)"
	@echo "  make os                   - Baut das Betriebssystem (@OS.COM) fuer die Standard-Variante ($(DEFAULT_SYSTEMVAR))"
	@echo "  make diskimage            - Erstellt das Diskettenimage im build/-Verzeichnis (IMG-Format)"
	@echo "  make diskimagehfe         - Erstellt ein HFE-Diskettenimage im build/-Verzeichnis"
	@echo "  make diskimagescp         - Erstellt ein SCP-Diskettenimage im build/-Verzeichnis"
	@echo "  make writeimage           - Schreibt das Diskettenimage auf ein physikalisches Laufwerk"
	@echo "  make clean                - Entfernt temporaere und finale Dateien"
	@echo "  make menuconfig           - Startet das mehrstufige Konfigurationsmenue (Systemtyp, Hardware, Build-Optionen)"
	@echo "  make help                 - Zeigt diese Hilfe an"
	@echo ""
	@echo "Hinweis: Wenn du nicht das Menue oder die .config verwenden moechtest, setze die Zeile DEFAULT_SYSTEMVAR := <dein_systemname> am Anfang dieses Makefiles."
	@echo "Die verwendeten Ordner leiten sich direkt vom Namen der Systemvariante ab:"
	@echo "  - Quelltexte:      src/<systemvariante> (z.B. src/pc_1715)"
	@echo "  - Prebuilt-Files:  prebuilt/<systemvariante> (z.B. prebuilt/pc_1715)"
	@echo "  - Bootsektor:      prebuilt/<systemvariante>/bootsec.bin"
	@echo ""
	@echo "Konfigurationsmenue (menuconfig):"
	@echo "  - Interaktives Menue zur Auswahl von Systemtyp, Hardware und Build-Optionen"
	@echo "  - Hilfetexte zu allen Optionen mit [?] im Menue aufrufbar"
	@echo "  - Wizard-aehnliche Navigation durch die Konfigurationsschritte"
	@echo "  - Aenderungen werden in .config gespeichert und automatisch uebernommen"
	@echo ""
	@echo "Beispiele:"
	@echo "  make config os                # Baut @os.com gemaess .config (empfohlen)"
	@echo "  make config diskimage         # Erstellt Diskettenimage gemaess .config"
	@echo "  make config diskimagehfe      # Erstellt HFE-Image gemaess .config (wenn aktiviert)"
	@echo "  make config diskimagescp      # Erstellt SCP-Image gemaess .config (wenn aktiviert)"
	@echo "  make config pc_1715 os        # Baut @os.com fuer pc_1715 (ueberschreibt .config)"
	@echo "  make pc_1715 os               # Baut @os.com fuer pc_1715"
	@echo "  make menuconfig               # Startet das Konfigurationsmenue"
	@echo ""
	@echo "[HINWEIS] Fuer reproduzierbare Builds immer 'make config <target>' verwenden!"


# OS bauen (Betriebssystem @OS.COM)
os: .config $(OS_TARGET)

# Build-Regel: zum aufrufen eines systemvariantenspezifischen separaten Makefiles
$(OS_TARGET): $(SRC_DIR)/bios.mac $(PREBUILT_DIR)/bdos.erl $(PREBUILT_DIR)/ccp.erl $(PREBUILT_DIR)/cpabas.erl
	$(MAKE) -C config/$(SYSTEMVAR) BUILD_DIR="$(BUILD_DIR)" SRC_DIR="$(SRC_DIR)" PREBUILT_DIR="$(PREBUILT_DIR)" TOOLS_DIR="$(TOOLS_DIR)" CPM="$(CPM)" CPMEXE="$(CPMEXE)"

# Build-Regel fuer das Betriebssystem Diskettenimage
diskimage: os $(FINAL_IMAGE)
	@echo "[INFO] Target 'diskimage' abgeschlossen."

# Diskettenformat aus .config ermitteln (cpa780 oder cpa800)
FORMAT := $(DEFAULT_FORMAT)
IMAGE_SIZE := $(DEFAULT_IMAGE_SIZE)
DISKDEF := $(DEFAULT_DISKDEF)
ifeq ($(wildcard .config),.config)
	ifneq ($(shell grep -q '^CONFIG_BUILD_DISKTYPE_800K=y' .config && echo yes),)
		FORMAT := cpa800
		IMAGE_SIZE := 800
		DISKDEF := cpa800
		USEBOOTSECTOR := 0
	endif
	ifneq ($(shell grep -q '^CONFIG_BUILD_DISKTYPE_780K=y' .config && echo yes),)
		FORMAT := cpa780
		IMAGE_SIZE := 780
		DISKDEF := cpa780_withoutBoot
		USEBOOTSECTOR := 1
	endif
endif

$(FINAL_IMAGE): $(BOOTSECTOR) $(OS_TARGET)

# Erzeugt das Diskettenimage fuer das CP/A-System
# Diese Regel erstellt ein bootfaehiges Diskettenimage (IMG-Format) fuer Emulatoren oder echte Hardware
# Schritte:
# 1. Erzeuge eine leere Image-Datei mit der gewuenschten Groesse und fuelle sie mit 0xE5 (CP/M-Standardwert)
# 2. Kopiere die Systemdatei (@os.com) mit cpmcp ins Image
# 3. Fuer das 800K-Format: Bootsektor am Anfang einfuegen und Spur 0 fuer Bootfaehigkeit anpassen
# 4. Fuer das 780K-Format: Bootsektor wird am Ende angehaengt (konkateniert)
# 5. Fuege alle Dateien aus dem Verzeichnis 'additions' ins Image ein
# 6. Zeige die Dateien im Image zur Kontrolle an
# 7. Entferne temporaere Dateien
	@if [ "$(FORMAT)" = "cpa780" ]; then \
		echo "[STEP 1] Erzeuge leeres temporaeres Image: $(TMP_IMAGE) (Groesse: 780k, Format: $(FORMAT))"; \
		dd if=/dev/zero bs=1024 count=780 2>/dev/null | tr '\0' '\345' | dd of=$(TMP_IMAGE) bs=1024 count=780 2>/dev/null; \
		echo "[STEP 2] Kopiere CPA-System (@os.com) ins Image (Format: $(FORMAT))"; \
		$(CPMCP) -f $(DISKDEF) $(TMP_IMAGE) $(OS_TARGET) $(SYSTEMNAME); \
	else \
		echo "[STEP 1] Erzeuge leeres temporaeres Image: $(TMP_IMAGE) (Groesse: 800k, Format: $(FORMAT))"; \
		dd if=/dev/zero bs=1024 count=800 2>/dev/null | tr '\0' '\345' | dd of=$(TMP_IMAGE) bs=1024 count=800 2>/dev/null; \
		echo "[STEP 1b] Erzeuge pseudo-Bootblock am Anfang der Dateizuordnungstabelle"; \
		dd if=$(BOOTSECTOR) bs=32 count=1 conv=notrunc of=$(TMP_IMAGE) 2>/dev/null; \
		echo "[STEP 2] Kopiere CPA-System (@os.com) ins Image (Format: $(FORMAT))"; \
		$(CPMCP) -f $(DISKDEF) $(TMP_IMAGE) $(OS_TARGET) $(SYSTEMNAME); \
		echo "[STEP 2b] Fixe Spur 0 damit sie bootfaehig wird"; \
		dd if=$(BOOTSECTOR) bs=32 count=4 conv=notrunc of=$(TMP_IMAGE) 2>/dev/null; \
	fi
	@echo "[STEP 3] Kopiere Dateien aus '$(ADDITIONS_DIR)' ins Image"
# Fuegt alle Dateien aus dem additions-Verzeichnis ins Diskettenimage ein
	# Pruefe, ob ein Unterordner mit dem Namen der Systemvariante existiert
	@if [ -d "$(ADDITIONS_DIR)/$(SYSTEMVAR)" ]; then \
		echo "[STEP 3a] Kopiere Dateien aus '$(ADDITIONS_DIR)/$(SYSTEMVAR)' ins Image"; \
		for f in $(ADDITIONS_DIR)/$(SYSTEMVAR)/*; do \
			if [ -f "$$f" ]; then \
				fname=$$(basename "$$f"); \
				echo "  [ADD] $$fname (system-specific)"; \
				$(CPMCP) -f $(DISKDEF) $(TMP_IMAGE) $$f 0:$$fname; \
			fi; \
		done; \
	fi; \
	echo "[STEP 3b] Kopiere Dateien aus '$(ADDITIONS_DIR)' ins Image"; \
	for f in $(ADDITIONS_DIR)/*; do \
		if [ -f "$$f" ]; then \
			fname=$$(basename "$$f"); \
			echo "  [ADD] $$fname"; \
			$(CPMCP) -f $(DISKDEF) $(TMP_IMAGE) $$f 0:$$fname; \
		fi; \
	done; 
#	@echo "[STEP 4] Zeige Dateien im Image (nach dem Kopieren):"
	@echo "[STEP 4] Zeige Dateien im Image (nach dem Kopieren):"
# Listet alle Dateien im Image zur Kontrolle auf
	$(CPMLS) -Ff $(DISKDEF) $(TMP_IMAGE)
	@if [ "$(FORMAT)" = "cpa780" ]; then \
		if [ -f "$(BOOTSECTOR)" ]; then \
			echo "[STEP 5] Fuege Bootsektor aus $(BOOTSECTOR) hinzu"; \
			(dd if=$(BOOTSECTOR) bs=128 2>/dev/null; dd if=$(TMP_IMAGE) bs=1024 2>/dev/null) > $(FINAL_IMAGE); \
		else \
			echo "[WARNUNG] Bootsektor $(BOOTSECTOR) nicht gefunden!"; \
		fi; \
	else \
		echo "[STEP 5] Bootsektor braucht nicht hinzugefuegt zu werden"; \
		cp $(TMP_IMAGE) $(FINAL_IMAGE); \
	fi
	# Entfernt die temporaere Image-Datei
	rm -f $(TMP_IMAGE)
	@echo "[DONE] Diskettenimage erstellt: $(FINAL_IMAGE)"

# Diskettenimage im HFE-Format erzeugen
diskimagehfe: diskimage $(HFE_IMAGE)
	@echo "[INFO] Target 'diskimagehfe' abgeschlossen."

# Diskettenimage im SCP-Format erzeugen
diskimagescp: diskimage $(SCP_IMAGE)
	@echo "[INFO] Target 'diskimagescp' abgeschlossen."

# Regel fuer HFE-Image
$(HFE_IMAGE): $(FINAL_IMAGE)
	@echo "[STEP] Konvertiere $(FINAL_IMAGE) nach $(HFE_IMAGE) (Format: HFE)"
	$(GW) convert --diskdefs=$(CFG) --format=$(FORMAT) $(FINAL_IMAGE) $(HFE_IMAGE)
	@echo "[DONE] HFE-Image erstellt: $(HFE_IMAGE)"

# Regel fuer SCP-Image
$(SCP_IMAGE): $(FINAL_IMAGE)
	@echo "[STEP] Konvertiere $(FINAL_IMAGE) nach $(SCP_IMAGE) (Format: SCP)"
	$(GW) convert --diskdefs=$(CFG) --format=$(FORMAT) $(FINAL_IMAGE) $(SCP_IMAGE)
	@echo "[DONE] SCP-Image erstellt: $(SCP_IMAGE)"


# Diskettenimage auf physikalisches Laufwerk schreiben
WRITEIMAGE_LOG = $(BUILD_DIR)/writeimage.log
writeimage: $(WRITEIMAGE_LOG)

.PHONY: clean_writeimage_log

clean_writeimage_log:
	@if [ -f "$(WRITEIMAGE_LOG)" ]; then \
		age=$$(($(shell date +%s) - $(shell date +%s -r $(WRITEIMAGE_LOG)))); \
		if [ $$age -gt 30 ]; then \
			echo "[INFO] $(WRITEIMAGE_LOG) ist aelter als 30s, wird geloescht..."; \
			rm -f $(WRITEIMAGE_LOG); \
		fi; \
	fi

$(WRITEIMAGE_LOG): clean_writeimage_log $(FINAL_IMAGE)
	@echo "[STEP] Schreibe Diskettenimage mit gw auf physikalisches Laufwerk"
	@$(GW) write --diskdefs=$(CFG) --format=$(FORMAT) $(FINAL_IMAGE) 2>&1 | tee $@
	@echo "[FERTIG] Diskettenimage mit gw auf Laufwerk geschrieben." 2>&1 | tee $@

# Aufraeumen
clean:
	@rm  $(BUILD_DIR)/* >/dev/null 2>&1 || true
	@echo "[INFO] Aufraeumen abgeschlossen."
