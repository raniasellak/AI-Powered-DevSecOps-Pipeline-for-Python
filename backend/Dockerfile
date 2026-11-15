FROM python:3.12-slim

# Image non-root (bonne pratique sécurité)
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Copie et install des dépendances avant le code (cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Droits sur le dossier pour l'utilisateur non-root
RUN chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
