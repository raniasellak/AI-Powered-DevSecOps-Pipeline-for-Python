from fastapi import FastAPI

from .auth import models  # noqa: F401  (enregistre la table users)
from .database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="InvoicePay API")


@app.get("/health")
def health():
    return {"status": "ok"}