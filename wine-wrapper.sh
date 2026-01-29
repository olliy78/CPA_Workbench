#!/bin/bash
# Wine Wrapper Script - startet Xvfb bei Bedarf für headless Wine-Ausführung

# Prüfe ob Xvfb bereits läuft
if ! pgrep -x Xvfb > /dev/null; then
    # Starte Xvfb im Hintergrund
    Xvfb :99 -screen 0 1024x768x16 &
    XVFB_PID=$!
    # Warte kurz bis Xvfb bereit ist
    sleep 0.5
    # Merke, dass wir Xvfb gestartet haben
    STARTED_XVFB=1
fi

# Setze DISPLAY
export DISPLAY=:99
export WINEARCH=win32
export WINEPREFIX=/home/builder/.wine
export WINEDEBUG=-all

# Führe Wine aus
wine "$@"
WINE_EXIT=$?

# Stoppe Xvfb wenn wir es gestartet haben
if [ -n "$STARTED_XVFB" ] && [ -n "$XVFB_PID" ]; then
    kill $XVFB_PID 2>/dev/null
fi

exit $WINE_EXIT
