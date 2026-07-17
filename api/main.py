from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

from config.settings import APP_MODE
from database.connection import (
    get_connection,
    get_signals,
    save_signal,
)
from logs.logger import logger
from providers.market_provider import get_signal
from scheduler.jobs import scheduled_test_job

app = FastAPI()

job_scheduler = BackgroundScheduler()


@app.on_event("startup")
def start_scheduler():
    job_scheduler.add_job(
        scheduled_test_job,
        "interval",
        seconds=30,
        id="scheduled_test_job",
        replace_existing=True,
    )

    job_scheduler.start()
    logger.info("Scheduler started")


@app.on_event("shutdown")
def stop_scheduler():
    job_scheduler.shutdown()
    logger.info("Scheduler stopped")


@app.get("/health")
def health():
    logger.info("Health endpoint called")

    return {
        "status": "ok",
        "mode": APP_MODE,
    }


@app.get("/signal")
def signal():
    logger.info("Generating new signal")

    data = get_signal()

    save_signal(
        data["ticker"],
        data["entry_price"],
        data["stop_price"],
        data["tp1_price"],
        data["tp2_price"],
        data["signal"],
    )

    logger.info("Signal saved for %s", data["ticker"])

    return data


@app.get("/signals")
def signals():
    logger.info("Reading all signals")

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
    logger.info("Database health check")

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
    