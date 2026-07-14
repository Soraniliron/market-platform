from fastapi import FastAPI
from config.settings import APP_MODE
from providers.market_provider import get_signal
from database.connection import get_connection

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


@app.get("/db-check")
def db_check():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT 1;")
    result = cursor.fetchone()
    cursor.close()
    connection.close()

    return {
        "database": "ok",
        "result": result[0]
    }
    