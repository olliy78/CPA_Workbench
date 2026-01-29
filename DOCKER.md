# Docker Build Environment für CPA Workbench

Dieses Verzeichnis enthält die Docker-Konfiguration für eine portable Build-Umgebung des CPA Workbench Projekts.

## Dateien

- **Dockerfile** - Definiert den Build-Container basierend auf Debian 13 mit Wine 32-bit
- **docker-shell.sh** - Management-Script für den Container
- **docker-compose.yml** - Docker Compose Konfiguration (optional)

## Schnellstart

### 1. Image bauen

```bash
./docker-shell.sh build
```

Dies baut das Docker-Image mit Ihrer aktuellen User-UID/GID, damit Dateiberechtigungen korrekt funktionieren.

### 2. Container als User betreten

```bash
./docker-shell.sh shell
# oder einfach:
./docker-shell.sh
```

### 3. Container als root betreten

```bash
./docker-shell.sh root
```

## Verfügbare Kommandos

| Kommando | Beschreibung |
|----------|--------------|
| `build` | Baut das Docker Image mit der aktuellen User-UID/GID |
| `shell` | Öffnet eine Shell im Container als normaler Benutzer (Standard) |
| `root` | Öffnet eine Shell im Container als root |
| `start` | Startet den Container im Hintergrund |
| `stop` | Stoppt den laufenden Container |
| `restart` | Startet den Container neu |
| `status` | Zeigt den Status des Containers |
| `logs` | Zeigt die Container-Logs |
| `clean` | Stoppt und entfernt den Container |
| `help` | Zeigt die Hilfe an |

## Verwendung mit docker-compose

Alternativ zum Shell-Script können Sie auch docker-compose verwenden:

```bash
# Image bauen
USER_UID=$(id -u) USER_GID=$(id -g) docker-compose build

# Container starten
USER_UID=$(id -u) USER_GID=$(id -g) docker-compose up -d

# Shell als User öffnen
docker-compose exec cpa-builder bash

# Shell als root öffnen
docker-compose exec -u root cpa-builder bash

# Container stoppen
docker-compose down
```

## Was ist im Container enthalten?

- **Debian 13 (Trixie)** - Basis-System
- **Wine 32-bit (10.0)** - Windows-Emulation für 32-bit Anwendungen
- **Xvfb** - Virtual Framebuffer für headless Wine-Ausführung
- **Build-Tools** - gcc, g++, make, etc.
- **Python 3** - Für Build-Scripts
- **Standard-Tools** - git, vim, nano, wget, curl

## Projekt-Verzeichnis

Das aktuelle Projekt-Verzeichnis wird automatisch als `/workspace` in den Container eingebunden. Alle Änderungen, die Sie im Container machen, werden direkt auf dem Host-System reflektiert.

## User-Mapping

Der Container-User `builder` wird automatisch mit der gleichen UID/GID wie Ihr Host-User erstellt. Dies stellt sicher, dass:

- Dateien, die im Container erstellt werden, Ihnen auf dem Host gehören
- Keine Berechtigungsprobleme bei der Arbeit mit Dateien entstehen
- Builds mit den richtigen Berechtigungen durchgeführt werden

## Tipps

### Projekt im Container bauen

```bash
# Container betreten
./docker-shell.sh shell

# Im Container - Xvfb wird automatisch bei Wine-Aufrufen gestartet
cd /workspace

# Konfiguration (falls noch nicht vorhanden)
make menuconfig

# Betriebssystem bauen
Xvfb :99 -screen 0 1024x768x16 & sleep 1
DISPLAY=:99 make config os

# Oder alternativ mit wine-wrapper (startet Xvfb automatisch):
wine-wrapper build/m80.com /?

# Disk-Image erstellen
DISPLAY=:99 make config diskimage
```

**Hinweis:** Wine benötigt ein X11-Display. Der Container nutzt Xvfb (Virtual Framebuffer) für headless Builds. Die Umgebungsvariable `DISPLAY=:99` muss gesetzt sein.

### Container im Hintergrund laufen lassen

```bash
# Container starten
./docker-shell.sh start

# Jederzeit wieder verbinden
./docker-shell.sh shell
```

### Pakete im Container installieren

```bash
# Als root einloggen
./docker-shell.sh root

# Im Container
apt-get update
apt-get install -y <paket-name>
```

**Hinweis:** Änderungen am Container gehen beim Löschen verloren. Wenn Sie dauerhafte Änderungen benötigen, passen Sie das Dockerfile an und bauen das Image neu.

## Fehlerbehebung

### "Permission denied" beim Ausführen von docker-shell.sh

```bash
chmod +x docker-shell.sh
```

### "Cannot connect to Docker daemon"

Stellen Sie sicher, dass:
1. Docker installiert ist
2. Der Docker-Daemon läuft: `sudo systemctl start docker`
3. Ihr User in der docker-Gruppe ist: `sudo usermod -aG docker $USER`
4. Sie sich neu einloggen nach der Gruppenänderung

### Container startet nicht

```bash
# Status prüfen
./docker-shell.sh status

# Logs anzeigen
./docker-shell.sh logs

# Container neu erstellen
./docker-shell.sh clean
./docker-shell.sh build
```

## Weitere Informationen

Für detaillierte Informationen zum Script führen Sie aus:

```bash
./docker-shell.sh help
```
