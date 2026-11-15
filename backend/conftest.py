import sys
import os

# Ajoute le dossier backend au path pour que 'app' soit importable
sys.path.insert(0, os.path.dirname(__file__))

# Variables d'environnement minimales pour les tests
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
