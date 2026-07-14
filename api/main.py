from fastapi import FastAPI
from config.settings import APP_MODE
from providers.market_provider import get_signal

app = FastAPI()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": APP_MODE
    }


@app.get("/signal")
def signal():
    return get_signal()
    