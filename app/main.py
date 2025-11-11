from fastapi import FastAPI

app = FastAPI(title="E-Commerce Graph API")


@app.get("/health")
def health():
    """
    Simple health check used by the checks script.
    """
    return {"ok": True}
