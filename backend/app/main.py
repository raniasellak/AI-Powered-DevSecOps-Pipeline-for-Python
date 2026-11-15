from fastapi import FastAPI

from .auth import models as auth_models  # noqa: F401
from .auth.router import router as auth_router
from .database import Base, engine
from .invoices import models as invoice_models  # noqa: F401
from .invoices.router import router as invoices_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="InvoicePay API")
app.include_router(auth_router)
app.include_router(invoices_router)


@app.get("/health")
def health():
    return {"status": "ok"}