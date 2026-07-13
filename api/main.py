from fastapi import FastAPI
from config.settings import APP_MODE
from mock_engine.provider import get_market_data

app = FastAPI()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": APP_MODE
    }


@app.get("/signal")
def signal():
    return get_market_data()
    