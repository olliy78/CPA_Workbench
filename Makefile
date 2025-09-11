# Makefile für CP/A BIOS Projekt mit strukturierter Verzeichnisaufteilung
#
# Dieses Makefile baut das CP/A-System im build/-Verzeichnis.
# Es kopiert alle benötigten Quell- und Vorabdateien ins build/-Verzeichnis,
# da die CP/M-Tools keine Verzeichnisse unterstützen.
# Nach dem Build werden temporäre Dateien entfernt, nur das fertige @OS.com bleibt erhalten.



# Betriebssystem erkennen (für Wine unter Linux)
OS := $(shell uname)
# Name des CP/M-Emulators
CPMEXE = cpm.exe
# Name und Pfad der Zieldatei
TARGET = build/@OS.COM
# Verzeichnis mit CP/A-Quelltexten
SRC_DIR = src
# Verzeichnis mit vorgefertigten ERL/COM-Dateien
PREBUILT_DIR = prebuilt
# Arbeits- und Ausgabeverzeichnis für Build-Produkte
BUILD_DIR = build
# Verzeichnis mit Build-Tools (z.B. m80.com, linkmt.com)
TOOLS_DIR = tools
# Verzeichnis für Beispielprogramme
EXAMPLES_DIR = examples


# CPM-Tool-Aufruf je nach Betriebssystem
ifeq ($(OS),Linux)
CPM = wine $(CPMEXE)
else
CPM = $(CPMEXE)
endif


# Standard-Target: baue das System
all: $(TARGET)

# Build-Regel: Erzeuge @OS.com im build/-Verzeichnis
# Abhaengigkeiten: Quelltexte und vorgefertigte ERL
$(TARGET): $(SRC_DIR)/bios.mac $(PREBUILT_DIR)/bdos.erl $(PREBUILT_DIR)/ccp.erl $(PREBUILT_DIR)/cpabas.erl
	@echo "---------------------------------------------------"
	@echo "Generieren von CP/A ... @OS.COM"
	@echo "---------------------------------------------------"
# 1. Alle benötigten Quell- und Vorabdateien ins Build-Verzeichnis kopieren
	cp $(SRC_DIR)/*.mac $(BUILD_DIR)/
	cp $(PREBUILT_DIR)/*.erl $(BUILD_DIR)/
	cp $(TOOLS_DIR)/* $(BUILD_DIR)/ 2>/dev/null || true
# 2. Assemblieren im Build-Verzeichnis, Ausgabe in bios.log abfangen - wird im nächsten Schritt benötigt
	cd $(BUILD_DIR) && $(CPM) m80 =bios/L | tee bios.log
	cd $(BUILD_DIR) && $(CPM) m80 bios.erl=bios
# 3. Linken im Build-Verzeichnis mit berechnetem /p: Wert
# Extrahiere den Wert nach /p: aus der M80-Ausgabe (bios.log):
# - grep '/p:' filtert nur Zeilen mit /p: (Link-Anweisung)
# - sed 's/[^[:print:]]//g' entfernt alle nicht druckbaren Zeichen (z.B. Backspace)
# - sed -n 's/.*\/p:[[:space:]]*\([0-9A-Fa-f]\{4,\}\).*/\1/p' extrahiert die Hex-Zahl nach /p:
# - head -1 nimmt den ersten Treffer (falls mehrere vorhanden)
	@diff=$$(grep '/p:' $(BUILD_DIR)/bios.log | sed 's/[^[:print:]]//g' | sed -n 's/.*\/p:[[:space:]]*\([0-9A-Fa-f]\{4,\}\).*/\1/p' | head -1); \
	if [ -z "$$diff" ]; then echo "Fehler: Kein /p:-Wert in bios.log gefunden!"; exit 1; fi; \
	echo "Verwende berechneten Linkwert: $$diff"; \
	cd $(BUILD_DIR) && $(CPM) linkmt @OS=cpabas,ccp,bdos,bios/p:$$diff
# 4. Aufräumen: temporäre Dateien löschen, nur @OS.com bleibt
	rm -f $(BUILD_DIR)/*.syp $(BUILD_DIR)/*.rel $(BUILD_DIR)/*.mac $(BUILD_DIR)/*.erl $(BUILD_DIR)/bios.log $(BUILD_DIR)/$(CPMEXE) $(BUILD_DIR)/m80.com $(BUILD_DIR)/linkmt.com
	@echo "..................................................."
	@echo "Fertig !!!!!!"

clean:
	rm -f $(BUILD_DIR)/* $(SRC_DIR)/*.erl $(SRC_DIR)/*.rel $(SRC_DIR)/*.syp

.PHONY: all clean
