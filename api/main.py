from fastapi import FastAPI
from apscheduler.schedulers.background import (
    BackgroundScheduler,
)

from config.settings import (
    APP_MODE,
    SCHEDULER_INTERVAL_SECONDS,
)
from database.connection import get_connection
from database.signal_repository import (
    get_signals,
    save_signal,
)
from logs.logger import log_event
from providers.market_provider import get_signal
from scheduler.jobs import scheduled_test_job


app = FastAPI()

job_scheduler = BackgroundScheduler()


@app.on_event("startup")
def start_scheduler() -> None:
    job_scheduler.add_job(
        scheduled_test_job,
        "interval",
        seconds=SCHEDULER_INTERVAL_SECONDS,
        id="scheduled_test_job",
        replace_existing=True,
    )

    job_scheduler.start()

    log_event(
        "SCHEDULER_STARTED",
        message="Scheduler started",
        interval_seconds=(
            SCHEDULER_INTERVAL_SECONDS
        ),
    )


@app.on_event("shutdown")
def stop_scheduler() -> None:
    job_scheduler.shutdown()

    log_event(
        "SCHEDULER_STOPPED",
        message="Scheduler stopped",
    )


@app.get("/health")
def health() -> dict:
    log_event(
        "HEALTH_ENDPOINT_CALLED",
        message="Health endpoint called",
        app_mode=APP_MODE,
    )

    return {
        "status": "ok",
        "mode": APP_MODE,
    }


@app.get("/signal")
def signal() -> dict:
    log_event(
        "LEGACY_SIGNAL_REQUESTED",
        message="Generating legacy signal",
    )

    data = get_signal()

    save_signal(
        data["ticker"],
        data["entry_price"],
        data["stop_price"],
        data["tp1_price"],
        data["tp2_price"],
        data["signal"],
    )

    log_event(
        "LEGACY_SIGNAL_SAVED",
        message="Legacy signal saved",
        ticker=data["ticker"],
        signal=data["signal"],
    )

    return data


@app.get("/signals")
def signals() -> list[dict]:
    log_event(
        "SIGNALS_READ_REQUESTED",
        message="Reading saved signals",
    )

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
def db_check() -> dict:
    log_event(
        "DATABASE_HEALTH_CHECK_STARTED",
        message="Database health check started",
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()

        log_event(
            "DATABASE_HEALTH_CHECK_PASSED",
            message="Database health check passed",
            result=result[0],
        )

        return {
            "database": "ok",
            "result": result[0],
        }

    finally:
        cursor.close()
        connection.close()
        