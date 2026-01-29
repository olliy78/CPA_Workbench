#!/bin/bash

################################################################################
# docker-shell.sh - CPA Workbench Docker Container Management Script
################################################################################
#
# BESCHREIBUNG:
#   Dieses Script ermöglicht das einfache Bauen, Starten und Betreten des
#   CPA Workbench Build-Containers. Es unterstützt das Betreten des Containers
#   sowohl als normaler Benutzer als auch als root.
#
# VERWENDUNG:
#   ./docker-shell.sh [OPTION]
#
# OPTIONEN:
#   build       - Baut das Docker Image mit der aktuellen User-UID/GID
#   shell       - Öffnet eine Shell im Container als normaler Benutzer (Standard)
#   root        - Öffnet eine Shell im Container als root
#   start       - Startet den Container im Hintergrund
#   stop        - Stoppt den laufenden Container
#   restart     - Startet den Container neu
#   status      - Zeigt den Status des Containers
#   logs        - Zeigt die Container-Logs
#   clean       - Stoppt und entfernt den Container
#   help        - Zeigt diese Hilfe an
#
# BEISPIELE:
#   ./docker-shell.sh build       # Image bauen
#   ./docker-shell.sh shell       # Container als User betreten
#   ./docker-shell.sh root        # Container als root betreten
#
# VORAUSSETZUNGEN:
#   - Docker muss installiert und der aktuelle User in der docker-Gruppe sein
#   - Das Dockerfile muss im gleichen Verzeichnis vorhanden sein
#
# AUTOR:
#   Erstellt für CPA Workbench Projekt
#
# VERSION:
#   1.0 - 2026-01-29
#
################################################################################

# Farben für Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Konfiguration
IMAGE_NAME="cpa-workbench-build"
CONTAINER_NAME="cpa-workbench-builder"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Hole die aktuelle User-UID und GID
USER_UID=$(id -u)
USER_GID=$(id -g)
USERNAME=$(whoami)

################################################################################
# Hilfsfunktionen
################################################################################

# Ausgabe von Informationsmeldungen
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Ausgabe von Erfolgsmeldungen
success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Ausgabe von Warnungen
warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Ausgabe von Fehlermeldungen
error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Zeigt die Hilfe an
show_help() {
    sed -n '/^# BESCHREIBUNG:/,/^################################################################################$/p' "$0" | \
    sed 's/^# //g' | sed 's/^#//g'
}

# Prüft ob Docker verfügbar ist
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker ist nicht installiert oder nicht im PATH"
        exit 1
    fi
    
    if ! docker ps &> /dev/null; then
        error "Keine Berechtigung für Docker. Ist der User in der docker-Gruppe?"
        error "Führe aus: sudo usermod -aG docker $USERNAME"
        exit 1
    fi
}

# Prüft ob das Image existiert
check_image() {
    if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
        warning "Docker Image '$IMAGE_NAME' existiert nicht"
        return 1
    fi
    return 0
}

# Prüft ob der Container läuft
check_container_running() {
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        return 0
    fi
    return 1
}

# Prüft ob der Container existiert (läuft oder gestoppt)
check_container_exists() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        return 0
    fi
    return 1
}

################################################################################
# Hauptfunktionen
################################################################################

# Baut das Docker Image
build_image() {
    info "Baue Docker Image '$IMAGE_NAME' mit UID=$USER_UID und GID=$USER_GID..."
    
    if ! docker build \
        --build-arg USER_UID="$USER_UID" \
        --build-arg USER_GID="$USER_GID" \
        --build-arg USERNAME="builder" \
        -t "$IMAGE_NAME" \
        "$PROJECT_DIR"; then
        error "Fehler beim Bauen des Docker Images"
        exit 1
    fi
    
    success "Docker Image '$IMAGE_NAME' erfolgreich gebaut"
}

# Startet den Container
start_container() {
    if check_container_running; then
        info "Container '$CONTAINER_NAME' läuft bereits"
        return 0
    fi
    
    if check_container_exists; then
        info "Starte existierenden Container '$CONTAINER_NAME'..."
        docker start "$CONTAINER_NAME"
    else
        if ! check_image; then
            info "Image existiert nicht, baue es zuerst..."
            build_image
        fi
        
        info "Erstelle und starte neuen Container '$CONTAINER_NAME'..."
        docker run -d \
            --name "$CONTAINER_NAME" \
            -v "$PROJECT_DIR:/workspace" \
            -w /workspace \
            --hostname cpa-builder \
            "$IMAGE_NAME" \
            tail -f /dev/null
    fi
    
    success "Container '$CONTAINER_NAME' läuft"
}

# Öffnet eine Shell im Container als User
open_shell() {
    start_container
    
    info "Öffne Shell im Container als User 'builder'..."
    docker exec -it "$CONTAINER_NAME" /bin/bash
}

# Öffnet eine Shell im Container als root
open_root_shell() {
    start_container
    
    info "Öffne Shell im Container als root..."
    docker exec -it -u root "$CONTAINER_NAME" /bin/bash
}

# Stoppt den Container
stop_container() {
    if ! check_container_running; then
        warning "Container '$CONTAINER_NAME' läuft nicht"
        return 0
    fi
    
    info "Stoppe Container '$CONTAINER_NAME'..."
    docker stop "$CONTAINER_NAME"
    success "Container gestoppt"
}

# Startet den Container neu
restart_container() {
    info "Starte Container '$CONTAINER_NAME' neu..."
    stop_container
    start_container
}

# Zeigt den Container-Status
show_status() {
    info "Status von Container '$CONTAINER_NAME':"
    
    if check_container_running; then
        echo -e "${GREEN}✓ Container läuft${NC}"
        docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
    elif check_container_exists; then
        echo -e "${YELLOW}○ Container existiert, läuft aber nicht${NC}"
        docker ps -a --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
    else
        echo -e "${RED}✗ Container existiert nicht${NC}"
    fi
    
    echo ""
    if check_image; then
        echo -e "${GREEN}✓ Image '$IMAGE_NAME' vorhanden${NC}"
    else
        echo -e "${RED}✗ Image '$IMAGE_NAME' nicht vorhanden${NC}"
    fi
}

# Zeigt die Container-Logs
show_logs() {
    if ! check_container_exists; then
        error "Container '$CONTAINER_NAME' existiert nicht"
        exit 1
    fi
    
    info "Zeige Logs von Container '$CONTAINER_NAME'..."
    docker logs -f "$CONTAINER_NAME"
}

# Räumt auf (stoppt und entfernt Container)
clean_container() {
    if check_container_exists; then
        info "Entferne Container '$CONTAINER_NAME'..."
        docker rm -f "$CONTAINER_NAME" 2>/dev/null
        success "Container entfernt"
    else
        info "Container '$CONTAINER_NAME' existiert nicht"
    fi
}

################################################################################
# Main
################################################################################

# Prüfe Docker-Verfügbarkeit
check_docker

# Parse Kommandozeilen-Argumente
case "${1:-shell}" in
    build)
        build_image
        ;;
    shell|"")
        open_shell
        ;;
    root)
        open_root_shell
        ;;
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    clean)
        clean_container
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "Unbekannte Option: $1"
        echo ""
        echo "Verwende './docker-shell.sh help' für Hilfe"
        exit 1
        ;;
esac
