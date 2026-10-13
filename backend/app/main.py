from fastapi import FastAPI

app = FastAPI(title="InvoicePay API")


@app.get("/health")
def health():
    return {"status": "ok"}