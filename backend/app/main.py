from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import models  # noqa: F401  (enregistre la table users)
from .auth.router import router as auth_router
from .config import settings
from .database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="InvoicePay API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router)


@app.get("/health")
def health():
    return {"status": "ok"}