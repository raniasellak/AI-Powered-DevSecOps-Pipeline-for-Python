from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

# check_same_thread n'existe que pour SQLite
connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Classe de base de tous les modeles (tables)."""


def get_db():
    """Ouvre une session par requete et la ferme toujours a la fin."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()