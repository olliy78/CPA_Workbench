# Dockerfile für CPA Workbench Build-Container
# Basierend auf Debian 13 (Trixie) mit 32-bit Wine Support

FROM debian:trixie

# Setze DEBIAN_FRONTEND um interaktive Prompts zu vermeiden
ENV DEBIAN_FRONTEND=noninteractive

# Aktualisiere das System und installiere grundlegende Tools
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    build-essential \
    make \
    gcc \
    g++ \
    git \
    wget \
    curl \
    vim \
    nano \
    python3 \
    python3-pip \
    python3-venv \
    sudo \
    locales \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Generiere Locales
RUN sed -i 's/^# *\(de_DE.UTF-8\)/\1/' /etc/locale.gen && \
    sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen && \
    locale-gen

# Aktiviere 32-bit Architektur für Wine
RUN dpkg --add-architecture i386

# Aktualisiere Package-Liste und installiere Wine und Abhängigkeiten
RUN apt-get update && apt-get install -y \
    wine \
    wine32 \
    wine64 \
    libwine \
    libwine:i386 \
    fonts-wine \
    xvfb \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Erstelle Build-User (UID wird beim Container-Start gesetzt)
# Default UID 1000 falls nicht anders spezifiziert
ARG USER_UID=1000
ARG USER_GID=1000
ARG USERNAME=builder

RUN groupadd -g ${USER_GID} ${USERNAME} && \
    useradd -m -u ${USER_UID} -g ${USER_GID} -s /bin/bash ${USERNAME} && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Setze Arbeitsverzeichnis
WORKDIR /workspace

# Setze Wine Umgebungsvariablen VOR der Initialisierung
ENV WINEARCH=win32
ENV WINEPREFIX=/home/builder/.wine
ENV DISPLAY=:99
ENV WINEDEBUG=-all

# Wechsle zum Build-User
USER ${USERNAME}

# Initialisiere Wine als 32-bit (erstellt .wine Verzeichnis)
RUN WINEARCH=win32 WINEPREFIX=/home/builder/.wine wineboot --init && \
    while pgrep wineserver >/dev/null; do sleep 1; done

# Zurück ins Arbeitsverzeichnis
WORKDIR /workspace

# Kopiere Wine-Wrapper Script
COPY --chown=builder:builder wine-wrapper.sh /usr/local/bin/wine-wrapper
RUN chmod +x /usr/local/bin/wine-wrapper

# Standard-Command: bash
CMD ["/bin/bash"]
