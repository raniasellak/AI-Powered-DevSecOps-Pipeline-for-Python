# Image de base officielle, legere (moins de paquets = moins de failles)
FROM python:3.12-slim

# Pas de fichiers .pyc, logs affiches tout de suite
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Utilisateur sans privileges : l'application ne tourne jamais en root
RUN useradd --create-home --uid 10001 appuser

# Dependances d'abord (mise en cache), sans garder le cache pip
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Code de l'application, appartenant a appuser
COPY --chown=appuser:appuser backend/ ./backend/

USER appuser

EXPOSE 8000

# Pas de --reload en conteneur (mode developpement uniquement)
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
