from fastapi import FastAPI
from config.settings import APP_MODE
from providers.market_provider import get_signal
from database.connection import (
    get_connection,
    save_signal,
    get_signals,
)

app = FastAPI()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": APP_MODE,
    }


@app.get("/signal")
def signal():
    data = get_signal()

    save_signal(
        data["ticker"],
        data["entry_price"],
        data["stop_price"],
        data["tp1_price"],
        data["tp2_price"],
        data["signal"],
    )

    return data


@app.get("/signals")
def signals():
    rows = get_signals()

    return [
        {
            "id": row[0],
            "ticker": row[1],
            "entry_price": row[2],
            "stop_price": row[3],
            "tp1_price": row[4],
            "tp2_price": row[5],
            "signal": row[6],
            "created_at": str(row[7]),
        }
        for row in rows
    ]


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
        "result": result[0],
    }
    



    