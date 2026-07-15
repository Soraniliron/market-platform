from fastapi import FastAPI
from config.settings import APP_MODE
from providers.market_provider import get_signal
from database.connection import get_connection, save_signal

app = FastAPI()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": APP_MODE
    }


@app.get("/signal")
def signal():
    data = get_signal()

    save_signal(
        data["ticker"],
        data["price"],
        data["signal"]
    )

    return data


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
    
    