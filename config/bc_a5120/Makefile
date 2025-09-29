
# ------------------------------------------------------------------------------
# Systemvariantenspezifisches Makefile für CP/A BIOS (@OS.COM) - bc_a5120
# ------------------------------------------------------------------------------
#
# Dieses Makefile enthält die Build-Regeln für die Systemvariante "bc_a5120".
# Es wurde aus dem Haupt-Makefile ausgelagert, um variantenspezifische Build-Logik zu ermöglichen.
#
# WICHTIG: Dieses Makefile soll NICHT direkt aufgerufen werden!
# Der Aufruf erfolgt ausschließlich über das Haupt-Makefile im Projekt-Hauptverzeichnis.
#
# Die notwendigen Verzeichnisse und Tools (BUILD_DIR, SRC_DIR, PREBUILT_DIR, TOOLS_DIR, CPM, CPMEXE)
# werden als Umgebungsvariablen vom Haupt-Makefile übergeben.
#
# Beispiel-Aufruf aus Haupt-Makefile:
#   $(MAKE) -C config/bc_a5120 BUILD_DIR=... SRC_DIR=... PREBUILT_DIR=... TOOLS_DIR=... CPM=... CPMEXE=...
#
# Hinweise:
#   - Die Pfade sind relativ zum Hauptverzeichnis (BASEDIR = ../../)
#   - Die Build-Schritte und Dateinamen können pro Variante angepasst werden
#   - Kommentare und Schritt-Ausgaben sind analog zum Haupt-Makefile gehalten
# ------------------------------------------------------------------------------

BASEDIR = ../..
OS_TARGET = $(BASEDIR)/$(BUILD_DIR)/@os.com
all: os

os: $(OS_TARGET)

$(OS_TARGET): $(BASEDIR)/$(SRC_DIR)/bios.mac $(BASEDIR)/$(PREBUILT_DIR)/bdos.erl $(BASEDIR)/$(PREBUILT_DIR)/ccp.erl $(BASEDIR)/$(PREBUILT_DIR)/cpabas.erl
	@echo "[STEP 1] Kopiere alle .mac-Dateien aus src und $(SRC_DIR) nach $(BUILD_DIR)"
	@cp $(BASEDIR)/src/*.mac $(BASEDIR)/$(BUILD_DIR)/ 2>/dev/null || true
	@cp $(BASEDIR)/$(SRC_DIR)/*.mac $(BASEDIR)/$(BUILD_DIR)/ 2>/dev/null || true
	@echo "[STEP 2] Kopiere ERL-Dateien aus $(PREBUILT_DIR) nach $(BUILD_DIR)"
	@cp $(BASEDIR)/$(PREBUILT_DIR)/*.erl $(BASEDIR)/$(BUILD_DIR)/
	@echo "[STEP 3] Kopiere Tools (m80.com, linkmt.com, cpm.exe) nach $(BUILD_DIR)"
	@cp $(BASEDIR)/$(TOOLS_DIR)/m80.com $(BASEDIR)/$(TOOLS_DIR)/linkmt.com $(BASEDIR)/$(TOOLS_DIR)/cpm.exe $(BASEDIR)/$(BUILD_DIR)/ 2>/dev/null || true
	@echo "[STEP 4] Assemblieren mit m80 (Log: bios.log)"
	@cd $(BASEDIR)/$(BUILD_DIR) && $(CPM) m80 =bios/L | tee bios.log
	@echo "[STEP 5] Assemblieren bios.erl=bios"
	@cd $(BASEDIR)/$(BUILD_DIR) && $(CPM) m80 bios.erl=bios
	@echo "[STEP 6] Linken mit berechnetem /p:-Wert"
	@diff=$$(LC_ALL=C grep -a '/p:' $(BASEDIR)/$(BUILD_DIR)/bios.log | sed 's/[^0-9A-Fa-f ]//g' | sed -n 's/.*[ ]\([0-9A-Fa-f]\{4,\}\).*/\1/p' | head -1); \
	if [ -z "$$diff" ]; then echo "Fehler: Kein /p:-Wert in bios.log gefunden!"; exit 1; fi; \
	echo "Verwende berechneten Linkwert: $$diff"; \
	cd $(BASEDIR)/$(BUILD_DIR) && $(CPM) linkmt @OS=cpabas,ccp,bdos,bios/p:$$diff
	@echo "[STEP 7] Aufraeumen temporaerer Dateien"
	@rm -f $(BASEDIR)/$(BUILD_DIR)/*.syp $(BASEDIR)/$(BUILD_DIR)/*.rel $(BASEDIR)/$(BUILD_DIR)/*.mac $(BASEDIR)/$(BUILD_DIR)/*.erl $(BASEDIR)/$(BUILD_DIR)/bios.log $(BASEDIR)/$(BUILD_DIR)/$(CPMEXE) $(BASEDIR)/$(BUILD_DIR)/m80.com $(BASEDIR)/$(BUILD_DIR)/linkmt.com
	@echo "[FERTIG] @OS.COM wurde erfolgreich erzeugt."
