# ------------------------------------------------------------------------------
# Makefile für Systemdisketten-Image-Erstellung (CP/A-Projekt)
#
# Dieses Makefile automatisiert die Erstellung eines CP/M-kompatiblen
# Systemdisketten-Images für das CP/A-System. Es nutzt externe Tools (cpmcp,
# cpmls, gw) und kopiert Systemdateien sowie Zusatzdateien in ein Diskettenimage.
#
# Hauptfunktionen:
#  - Erzeugt ein leeres Diskettenimage mit vorgegebenem Format
#  - Kopiert das Betriebssystem (@os.com) und alle Dateien aus dem additions/-Verzeichnis
#    in das Image
#  - Fügt einen Bootblock hinzu und erzeugt das finale Diskettenimage
#  - Optional: Schreibt das Image mit gw auf ein physikalisches Laufwerk
#
# Voraussetzungen:
#  - Tools cpmcp, cpmls, gw müssen im tools/-Verzeichnis liegen
#  - cpaFormates.cfg muss im Verzeichnis liegen
#  - Das Systemfile ../build/@os.com muss bereits gebaut sein
#  - Zusatzdateien im additions/-Verzeichnis
#
# Targets:
#  make diskImage   - Erzeugt das Diskettenimage (build/cpadisk.img)
#  make writeImage  - Schreibt das Image mit gw auf ein physikalisches Laufwerk
#  make clean       - Entfernt temporäre und finale Images
#
# Konfiguration:
#  TARGET=BC (Standard) oder TARGET=PC (z.B. make PC diskImage)
# ------------------------------------------------------------------------------
# Configuration: Set TARGET to BC (default) or PC
TARGET ?= BC


# Path to external tools
TOOLSPATH = tools
CPMCP = $(TOOLSPATH)/cpmcp
CPMLS = $(TOOLSPATH)/cpmls
GW = gw
CFG = cpaFormates.cfg
FORMAT = cpa.780

# Image and file names
TMP_IMAGE = build/cpa780fs.img
FINAL_IMAGE = build/cpadisk.img
BOOTBLOCK = src/bootblock.img
SYSTEMFILE = ../build/@os.com
SYSTEMNAME = 0:@os.com
DISKDEF = cpa780_withoutBoot
ADDITIONS_DIR = additions

.PHONY: all help diskImage writeImage clean BC PC

all: help

help:
	@echo "Verwendung: make [TARGET] [diskImage|writeImage|clean]"
	@echo ""
	@echo "Konfigurationsziele:"
	@echo "  BC (Standard)   - Erzeuge für BC-System (make BC ...)"
	@echo "  PC              - Erzeuge für PC-System (make PC ...)"
	@echo ""
	@echo "Hauptziele:"
	@echo "  diskImage       - Erzeugt das Diskettenimage für das gewählte TARGET (Standard: BC)"
	@echo "  writeImage      - Schreibt das Diskettenimage (mit gw) auf ein physikalisches Laufwerk"
	@echo "  clean           - Entfernt erzeugte Diskettenimages"
	@echo ""
	@echo "Beispiele:"
	@echo "  make diskImage           # Erzeugt BC-Image (Standard)"
	@echo "  make PC diskImage        # Erzeugt PC-Image"
	@echo "  make writeImage          # Schreibt BC-Image (Standard)"
	@echo "  make PC writeImage       # Schreibt PC-Image"
	@echo "  make clean               # Entfernt alle Images"

# Configuration switch targets
BC:
	@$(MAKE) TARGET=BC $(MAKECMDGOALS)

PC:
	@$(MAKE) TARGET=PC $(MAKECMDGOALS)

# Create the disk image file
$(FINAL_IMAGE): $(BOOTBLOCK) $(SYSTEMFILE)
	@echo "[STEP 1] Creating empty temporary image: $(TMP_IMAGE)"
	dd if=/dev/zero bs=1024 count=780 2>/dev/null | tr '\0' '\345' | dd of=$(TMP_IMAGE) bs=1024 count=780 2>/dev/null
	@echo "[STEP 2] Copying CPA system (@os.com) to image"
	$(CPMCP) -f $(DISKDEF) $(TMP_IMAGE) $(SYSTEMFILE) $(SYSTEMNAME)
	@echo "[STEP 3] Copying files from '$(ADDITIONS_DIR)' to image"
	@for f in $(ADDITIONS_DIR)/*; do \
	  if [ -f "$$f" ]; then \
	    fname=$$(basename "$$f"); \
	    echo "  [ADD] $$fname"; \
	    $(CPMCP) -f $(DISKDEF) $(TMP_IMAGE) $$f 0:$$fname; \
	  fi; \
	done
	@echo "[STEP 4] Listing files in image (after copy):"
	$(CPMLS) -Ff $(DISKDEF) $(TMP_IMAGE)
	@echo "[STEP 5] Adding bootblock and creating final image: $(FINAL_IMAGE)"
	(dd if=$(BOOTBLOCK) bs=128 2>/dev/null; dd if=$(TMP_IMAGE) bs=1024 2>/dev/null) > $(FINAL_IMAGE)
	rm -f $(TMP_IMAGE)
	@echo "[DONE] Disk image created: $(FINAL_IMAGE)"

diskImage: $(FINAL_IMAGE)
	@echo "[INFO] Target 'diskImage' abgeschlossen. Diskettenimage ist bereit für TARGET=$(TARGET)."

# Write the disk image (depends on the image file)
writeImage: $(FINAL_IMAGE)
	@echo "[STEP] Schreibe Diskettenimage mit gw auf physikalisches Laufwerk (TARGET=$(TARGET))"
	$(GW) write --diskdefs=$(CFG) --format=$(FORMAT) $(FINAL_IMAGE)
	@echo "[FERTIG] Diskettenimage mit gw auf Laufwerk geschrieben."

clean:
	@echo "[STEP] Entferne temporäre und finale Images..."
	rm -f $(TMP_IMAGE) $(FINAL_IMAGE)
	@echo "[FERTIG] Aufgeräumt."


