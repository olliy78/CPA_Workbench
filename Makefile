# ------------------------------------------------------------------------------
# Makefile für das CP/A BIOS-Projekt und die Systemdisketten-Erstellung
# ------------------------------------------------------------------------------
#
# Dieses Makefile steuert den Bau des CP/A-Betriebssystems (@OS.COM) und die
# Erstellung eines CP/M-kompatiblen Systemdisketten-Images. Es unterstützt beliebige
# Systemvarianten, die als Unterordner in src/<systemvariante> und prebuilt/<systemvariante> existieren.
#
# WICHTIG: Wenn du NICHT das Konfigurationsmenü oder die .config verwenden möchtest,
# kannst du die Zeile
#   DEFAULT_SYSTEMVAR := <dein_systemname>
# am Anfang dieses Makefiles anpassen, um die gewünschte Systemvariante festzulegen.
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
# Konfigurationsmenü:
#   make menuconfig   - Startet das mehrstufige Konfigurationsmenü für Systemtyp,
#                       Hardware- und Laufwerksauswahl sowie Build-Optionen.
#                       Die Konfiguration wird in .config gespeichert und die
#                       passenden BIOS-Quellen werden automatisch angepasst.
#   Das Menü bietet:
#     1. Auswahl des Systemtyps (z.B. A5120, PC1715)
#     2. Auswahl der Hardware- und Diskettenlaufwerks-Varianten
#     3. Auswahl des Build-Ausgabeformats
#     4. Hilfetexte zu allen Optionen (mit [?] im Menü)
#     5. Wizard-ähnliche Navigation durch die Konfigurationsschritte
#
# Wichtige Targets:
#   make config <target>      - Baut das gewünschte Target (os, diskImage, diskImage.hfe, diskImage.scp, ...) gemäß .config (empfohlen, reproduzierbar)
#   make os                   - Baut das Betriebssystem (@OS.COM) für das gewählte TARGET (Standard: BC, ggf. Warnung)
#   make diskImage            - Erstellt das Diskettenimage im build/-Verzeichnis (IMG-Format)
#   make diskImage.hfe        - Erstellt ein HFE-Diskettenimage im build/-Verzeichnis
#   make diskImage.scp        - Erstellt ein SCP-Diskettenimage im build/-Verzeichnis
#   make writeImage           - Schreibt das Diskettenimage auf ein physikalisches Laufwerk
#   make clean                - Entfernt temporäre und finale Dateien
#
# Systemvarianten:
#   Der Name der Systemvariante entspricht dem Unterordner in src/<system> und prebuilt/<system>.
#   Beispiel: make pc_1715 os verwendet src/pc_1715 und prebuilt/pc_1715.
#
# Beispiele:
#   make config os                # Baut @os.com gemäß .config (empfohlen)
#   make config diskImage         # Erstellt Diskettenimage gemäß .config
#   make config diskImage.hfe     # Erstellt HFE-Image gemäß .config (wenn aktiviert)
#   make config diskImage.scp     # Erstellt SCP-Image gemäß .config (wenn aktiviert)
#   make config pc_1715 os        # Baut @os.com für pc_1715 (überschreibt .config)
#   make pc_1715 os               # Baut @os.com für pc_1715
#   make menuconfig               # Startet das Konfigurationsmenü
#
# Hinweise:
#   - Die Quelltexte liegen in src/<systemvariante> (z.B. src/pc_1715)
#   - Der Bootsektor liegt in prebuilt/<systemvariante>/bootsec.bin
#   - Das Systemfile @OS.COM wird im build/-Verzeichnis erzeugt
#   - Das Diskettenimage wird als build/cpadisk.img abgelegt
#   - HFE- und SCP-Images werden als build/cpadisk.hfe bzw. build/cpadisk.scp abgelegt (wenn aktiviert)
#   - Die Konfiguration erfolgt über das Menü (menuconfig) und wird in .config gespeichert
#   - Nach Änderung der Konfiguration sollte das System neu gebaut werden
#   - Für reproduzierbare Builds immer 'make config <target>' verwenden!
# ------------------------------------------------------------------------------

# Zentraler Default für Systemvariante (wird überall als Fallback verwendet)
DEFAULT_SYSTEMVAR := pc_1715
# Systemdisk-Image-Konfiguration
TMP_IMAGE = $(BUILD_DIR)/cpadisk.img.tmp
FINAL_IMAGE = $(BUILD_DIR)/cpadisk.img
HFE_IMAGE = $(BUILD_DIR)/cpadisk.hfe
SCP_IMAGE = $(BUILD_DIR)/cpadisk.scp
SYSTEMNAME = 0:@os.com
ADDITIONS_DIR = additions
CPMCP = $(TOOLS_DIR)/cpmcp
CPMLS = $(TOOLS_DIR)/cpmls
GW = gw
CFG = cpaFormates.cfg
# Default Diskettenformat (wird ggf. durch .config überschrieben)
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
		SYSTEMVAR := $(shell awk -F'CONFIG_SYSTEM_' '/^CONFIG_SYSTEM_/ && $$2 ~ /=y/ {sub(/=y/,"",$$2); print tolower($$2)}' .config | head -1)
		ifeq ($(SYSTEMVAR),)
			SYSTEMVAR := $(DEFAULT_SYSTEMVAR)
		endif
	endif
else
	# make <system> <target> → Systemvariante ist erstes Argument, falls kein bekanntes Target
	ifneq ($(filter-out os diskImage diskImage.hfe diskImage.scp writeImage clean help all menuconfig,$(firstword $(MAKECMDGOALS))),)
		SYSTEMVAR := $(firstword $(MAKECMDGOALS))
		override MAKECMDGOALS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
	else
		# Fallback: aus .config
		ifeq ($(wildcard .config),)
			SYSTEMVAR := $(DEFAULT_SYSTEMVAR)
		else
			SYSTEMVAR := $(shell awk -F'CONFIG_SYSTEM_' '/^CONFIG_SYSTEM_/ && $$2 ~ /=y/ {sub(/=y/,"",$$2); print tolower($$2)}' .config | head -1)
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
		if [ -f .config ]; then \
			target=$$(awk -F'CONFIG_BUILD_' '/^CONFIG_BUILD_/ && $$2 ~ /=y/ {sub(/=y/,"",$$2); print tolower($$2)}' .config | head -1); \
			if [ -z "$$target" ]; then \
				echo "[INFO] Keine Build-Ziele in .config gefunden und kein Target angegeben."; exit 1; \
			fi; \
		else \
			echo "[INFO] Bitte gib ein Target an, z.B. 'make config os' oder 'make config diskImage'"; exit 1; \
		fi; \
	else \
		target="$$user_target"; \
	fi; \
	echo "[INFO] Baue explizit mit Konfiguration aus .config: Target='$$target'"; \
	exec $(MAKE) FROM_CONFIG=1 $$target;

# Warnung bei direktem Aufruf ohne config (aber nicht aus config-Target oder Wrapper heraus)
ifeq ($(FROM_CONFIG)$(FROM_WRAPPER),)
ifneq ($(MAKECMDGOALS),)
ifneq ($(firstword $(MAKECMDGOALS)),config)
$(info [INFO] Du hast 'make $(MAKECMDGOALS)' aufgerufen.)
endif
endif
endif

# Betriebssystem erkennen (für Wine unter Linux)
OS := $(shell uname)
# Name des CP/M-Emulators
CPMEXE = cpm.exe
# Arbeits- und Ausgabeverzeichnis für Build-Produkte
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
CPM = wine $(CPMEXE)
else
CPM = $(CPMEXE)
endif

# Keine expliziten Targets für Systemvarianten mehr nötig

# menuconfig: Wrapper für den mehrstufigen Konfigurationsprozess
.PHONY: menuconfig
menuconfig:
	@echo "Starte CPA-Mehrstufen-Konfigurationsmenü..."
	python3 configmenu/cpa_menuconfig.py

# Haupttargets
.PHONY: help all os diskImage writeImage clean

# Standard-Target: Hilfe anzeigen
all: help

# Hilfe-Target
	help:
	@echo "Verfügbare Targets für das CP/A-Projekt:"
	@echo "  make config <target>      - Baut das gewünschte Target (os, diskImage, diskImage.hfe, diskImage.scp, ...) gemäß .config (empfohlen, reproduzierbar)"
	@echo "  make <system> <target>    - Baut für die angegebene Systemvariante (z.B. make pc_1715 os)"
	@echo "  make os                   - Baut das Betriebssystem (@os.com) für die Standard-Variante ($(DEFAULT_SYSTEMVAR))"
	@echo "  make diskImage            - Erstellt das Diskettenimage im build/-Verzeichnis (IMG-Format)"
	@echo "  make diskImage.hfe        - Erstellt ein HFE-Diskettenimage im build/-Verzeichnis"
	@echo "  make diskImage.scp        - Erstellt ein SCP-Diskettenimage im build/-Verzeichnis"
	@echo "  make writeImage           - Schreibt das Diskettenimage auf ein physikalisches Laufwerk"
	@echo "  make clean                - Entfernt temporäre und finale Dateien"
	@echo "  make menuconfig           - Startet das mehrstufige Konfigurationsmenü (Systemtyp, Hardware, Build-Optionen)"
	@echo "  make help                 - Zeigt diese Hilfe an"
	@echo ""
	@echo "Hinweis: Wenn du nicht das Menü oder die .config verwenden möchtest, setze die Zeile DEFAULT_SYSTEMVAR := <dein_systemname> am Anfang dieses Makefiles."
	@echo "Die verwendeten Ordner leiten sich direkt vom Namen der Systemvariante ab:"
	@echo "  - Quelltexte:      src/<systemvariante> (z.B. src/pc_1715)"
	@echo "  - Prebuilt-Files:  prebuilt/<systemvariante> (z.B. prebuilt/pc_1715)"
	@echo "  - Bootsektor:      prebuilt/<systemvariante>/bootsec.bin"
	@echo ""
	@echo "Konfigurationsmenü (menuconfig):"
	@echo "  - Interaktives Menü zur Auswahl von Systemtyp, Hardware und Build-Optionen"
	@echo "  - Hilfetexte zu allen Optionen mit [?] im Menü aufrufbar"
	@echo "  - Wizard-ähnliche Navigation durch die Konfigurationsschritte"
	@echo "  - Änderungen werden in .config gespeichert und automatisch übernommen"
	@echo ""
	@echo "Beispiele:"
	@echo "  make config os                # Baut @os.com gemäß .config (empfohlen)"
	@echo "  make config diskImage         # Erstellt Diskettenimage gemäß .config"
	@echo "  make config diskImage.hfe     # Erstellt HFE-Image gemäß .config (wenn aktiviert)"
	@echo "  make config diskImage.scp     # Erstellt SCP-Image gemäß .config (wenn aktiviert)"
	@echo "  make config pc_1715 os        # Baut @os.com für pc_1715 (überschreibt .config)"
	@echo "  make pc_1715 os               # Baut @os.com für pc_1715"
	@echo "  make menuconfig               # Startet das Konfigurationsmenü"
	@echo ""
	@echo "[HINWEIS] Für reproduzierbare Builds immer 'make config <target>' verwenden!"


# OS bauen (Betriebssystem @OS.COM)
os: .config $(OS_TARGET)

# Build-Regel: Erzeuge @OS.COM im build/-Verzeichnis
# Abhaengigkeiten: Quelltexte und vorgefertigte ERL
$(OS_TARGET): $(SRC_DIR)/bios.mac $(PREBUILT_DIR)/bdos.erl $(PREBUILT_DIR)/ccp.erl $(PREBUILT_DIR)/cpabas.erl
	@echo "[STEP 1] Kopiere alle .mac-Dateien aus src und $(SRC_DIR) nach $(BUILD_DIR)"
	cp src/*.mac $(BUILD_DIR)/ 2>/dev/null || true
	cp $(SRC_DIR)/*.mac $(BUILD_DIR)/ 2>/dev/null || true
	@echo "[STEP 2] Kopiere ERL-Dateien aus $(PREBUILT_DIR) nach $(BUILD_DIR)"
	cp $(PREBUILT_DIR)/*.erl $(BUILD_DIR)/
	@echo "[STEP 3] Kopiere Tools (m80.com, linkmt.com, cpm.exe) nach $(BUILD_DIR)"
	cp $(TOOLS_DIR)/m80.com $(TOOLS_DIR)/linkmt.com $(TOOLS_DIR)/cpm.exe $(BUILD_DIR)/ 2>/dev/null || true
	@echo "[STEP 4] Assemblieren mit m80 (Log: bios.log)"
	cd $(BUILD_DIR) && $(CPM) m80 =bios/L | tee bios.log
	@echo "[STEP 5] Assemblieren bios.erl=bios"
	cd $(BUILD_DIR) && $(CPM) m80 bios.erl=bios
	@echo "[STEP 6] Linken mit berechnetem /p:-Wert"
	@diff=$$(LC_ALL=C grep -a '/p:' $(BUILD_DIR)/bios.log | sed 's/[^0-9A-Fa-f ]//g' | sed -n 's/.*[ ]\([0-9A-Fa-f]\{4,\}\).*/\1/p' | head -1); \
	if [ -z "$$diff" ]; then echo "Fehler: Kein /p:-Wert in bios.log gefunden!"; exit 1; fi; \
	echo "Verwende berechneten Linkwert: $$diff"; \
	cd $(BUILD_DIR) && $(CPM) linkmt @OS=cpabas,ccp,bdos,bios/p:$$diff
	@echo "[STEP 7] Aufräumen temporärer Dateien"
	rm -f $(BUILD_DIR)/*.syp $(BUILD_DIR)/*.rel $(BUILD_DIR)/*.mac $(BUILD_DIR)/*.erl $(BUILD_DIR)/bios.log $(BUILD_DIR)/$(CPMEXE) $(BUILD_DIR)/m80.com $(BUILD_DIR)/linkmt.com
	@echo "[FERTIG] @OS.COM wurde erfolgreich erzeugt."

# Diskettenimage erzeugen
diskImage: .config $(FINAL_IMAGE)
	@echo "[INFO] Target 'diskImage' abgeschlossen."

# Diskettenformat aus .config ermitteln (cpa780 oder cpa800)
FORMAT := $(DEFAULT_FORMAT)
IMAGE_SIZE := $(DEFAULT_IMAGE_SIZE)
DISKDEF := $(DEFAULT_DISKDEF)
ifeq ($(wildcard .config),.config)
	ifneq ($(shell grep -q '^CONFIG_DISKTYPE_800K=y' .config && echo yes),)
		FORMAT := cpa800
		IMAGE_SIZE := 800
		DISKDEF := cpa800
		USEBOOTSECTOR := 0
	endif
	ifneq ($(shell grep -q '^CONFIG_DISKTYPE_780K=y' .config && echo yes),)
		FORMAT := cpa780
		IMAGE_SIZE := 780
		DISKDEF := cpa780_withoutBoot
		USEBOOTSECTOR := 1
	endif
endif

# Image bauen: Abhängigkeit von OS und Bootsektor
$(FINAL_IMAGE): $(BOOTSECTOR) $(OS_TARGET)
	@if [ "$(FORMAT)" = "cpa780" ]; then \
		echo "[STEP 1] Erzeuge leeres temporäres Image: $(TMP_IMAGE) (Größe: 780k, Format: $(FORMAT))"; \
		dd if=/dev/zero bs=1024 count=780 2>/dev/null | tr '\0' '\345' | dd of=$(TMP_IMAGE) bs=1024 count=780 2>/dev/null; \
		echo "[STEP 2] Kopiere CPA-System (@os.com) ins Image (Format: $(FORMAT))"; \
		$(CPMCP) -f $(DISKDEF) $(TMP_IMAGE) $(OS_TARGET) $(SYSTEMNAME); \
	else \
		echo "[STEP 1] Erzeuge leeres temporäres Image: $(TMP_IMAGE) (Größe: 800k, Format: $(FORMAT))"; \
		dd if=/dev/zero bs=1024 count=800 2>/dev/null | tr '\0' '\345' | dd of=$(TMP_IMAGE) bs=1024 count=800 2>/dev/null; \
		echo "[STEP 1b] Erzeuge pseudo-Bootblock am Anfang der Dateizuordnungstabelle"; \
		dd if=$(BOOTSECTOR) bs=32 count=1 conv=notrunc of=$(TMP_IMAGE); \
		echo "[STEP 2] Kopiere CPA-System (@os.com) ins Image (Format: $(FORMAT))"; \
		$(CPMCP) -f $(DISKDEF) $(TMP_IMAGE) $(OS_TARGET) $(SYSTEMNAME); \
		echo "[STEP 2b] Fixe Spur 0 damit sie bootfähig wird"; \
		dd if=$(BOOTSECTOR) bs=32 count=4 conv=notrunc of=$(TMP_IMAGE); \
	fi
	@echo "[STEP 3] Kopiere Dateien aus '$(ADDITIONS_DIR)' ins Image"
	@for f in $(ADDITIONS_DIR)/*; do \
		if [ -f "$$f" ]; then \
			fname=$$(basename "$$f"); \
			echo "  [ADD] $$fname"; \
			$(CPMCP) -f $(DISKDEF) $(TMP_IMAGE) $$f 0:$$fname; \
		fi; \
	done; 
	@echo "[STEP 4] Zeige Dateien im Image (nach dem Kopieren):"
	$(CPMLS) -Ff $(DISKDEF) $(TMP_IMAGE)
	@if [ "$(FORMAT)" = "cpa780" ]; then \
		if [ -f "$(BOOTSECTOR)" ]; then \
			echo "[STEP 5] Füge Bootsektor aus $(BOOTSECTOR) hinzu"; \
			(dd if=$(BOOTSECTOR) bs=128 2>/dev/null; dd if=$(TMP_IMAGE) bs=1024 2>/dev/null) > $(FINAL_IMAGE); \
		else \
			echo "[WARNUNG] Bootsektor $(BOOTSECTOR) nicht gefunden!"; \
		fi; \
	else \
		echo "[STEP 5] Bootsektor braucht nicht hinzugefügt zu werden"; \
		cp $(TMP_IMAGE) $(FINAL_IMAGE); \
	fi
	rm -f $(TMP_IMAGE)
	@echo "[DONE] Diskettenimage erstellt: $(FINAL_IMAGE)"
# Diskettenimage im HFE-Format erzeugen
diskImage.hfe: .config $(HFE_IMAGE)
	@echo "[INFO] Target 'diskImage.hfe' abgeschlossen."

# Diskettenimage im SCP-Format erzeugen
diskImage.scp: .config $(SCP_IMAGE)
	@echo "[INFO] Target 'diskImage.scp' abgeschlossen."

# Regel für HFE-Image
$(HFE_IMAGE): $(FINAL_IMAGE)
	@echo "[STEP] Konvertiere $(FINAL_IMAGE) nach $(HFE_IMAGE) (Format: HFE)"
	$(GW) convert --diskdefs=$(CFG) --format=$(FORMAT) $(FINAL_IMAGE) $(HFE_IMAGE)
	@echo "[DONE] HFE-Image erstellt: $(HFE_IMAGE)"

# Regel für SCP-Image
$(SCP_IMAGE): $(FINAL_IMAGE)
	@echo "[STEP] Konvertiere $(FINAL_IMAGE) nach $(SCP_IMAGE) (Format: SCP)"
	$(GW) convert --diskdefs=$(CFG) --format=$(FORMAT) $(FINAL_IMAGE) $(SCP_IMAGE)
	@echo "[DONE] SCP-Image erstellt: $(SCP_IMAGE)"

# Diskettenimage auf physikalisches Laufwerk schreiben
writeImage: .config $(FINAL_IMAGE)
	@echo "[STEP] Schreibe Diskettenimage mit gw auf physikalisches Laufwerk (TARGET=$(TARGET))"
	$(GW) write --diskdefs=$(CFG) --format=$(FORMAT) $(FINAL_IMAGE)
	@echo "[FERTIG] Diskettenimage mit gw auf Laufwerk geschrieben."

# Aufräumen
clean:
	@echo "[STEP] Entferne temporäre und finale Dateien..."
	rm -f $(TMP_IMAGE) $(FINAL_IMAGE) $(BUILD_DIR)/* $(SRC_DIR)/*.erl $(SRC_DIR)/*.rel $(SRC_DIR)/*.syp
	@echo "[FERTIG] Aufgeräumt."
