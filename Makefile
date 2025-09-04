# Makefile for CP/A BIOS project using z80pack cpm22 emulator
# Edit SOURCES and TARGET as needed


# Makefile for CP/A BIOS project using z80pack cpm22 emulator
# Builds CPABAS, CCP, BDOS, BIOS and links to @OS.bin




# Makefile for CP/A BIOS project using RunCPM, M80.COM, and LINKMT.COM
OS := $(shell uname)
CPMEXE = cpm.exe
TARGET = @OS.com

all: $(TARGET)

ifeq ($(OS),Linux)
CPM = wine $(CPMEXE)
else
CPM = $(CPMEXE)
endif

$(TARGET):
	@echo "---------------------------------------------------"
	@echo "Generieren von CP/A ... @OS.COM"
	@echo "---------------------------------------------------"
	@rm -f @OS.com
	$(CPM) m80 =bios/L
	$(CPM) m80 BIOS.ERL=BIOS
	$(CPM) linkmt @OS=CPABAS,CCP,BDOS,BIOS/p:
	@rm -f *.syp bios.erl bios.rel
	@echo "..................................................."
	@echo "Fertig !!!!!!"

clean:
	rm -f @OS.com *.syp bios.erl bios.rel

.PHONY: all clean
