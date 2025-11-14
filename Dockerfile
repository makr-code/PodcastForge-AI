# PodcastForge AI Docker Image
FROM python:3.10-slim

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /app

# Python-Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projekt-Code
COPY . .
RUN pip install -e .

# Ollama wird über docker-compose bereitgestellt
ENV OLLAMA_HOST=http://ollama:11434

# Ausgabe-Verzeichnis
RUN mkdir -p /output

VOLUME ["/output"]

# Standard-Kommando
ENTRYPOINT ["podcastforge"]
CMD ["--help"]
