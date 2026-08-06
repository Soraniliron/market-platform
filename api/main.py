from __future__ import annotations

from apscheduler.schedulers.background import (
    BackgroundScheduler,
)
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config.settings import (
    SCHEDULER_INTERVAL_SECONDS,
)
from database.connection import get_connection
from health.monitor import (
    HealthCheckResult,
    HealthMonitor,
)
from logs.logger import log_event


app = FastAPI(
    title="IDB PRIME",
    version="1.0.0",
)

job_scheduler = BackgroundScheduler()


def scheduler_health_check() -> HealthCheckResult:
    running = job_scheduler.running

    return HealthCheckResult(
        component="scheduler",
        healthy=running,
        status=(
            "running"
            if running
            else "stopped"
        ),
        details={
            "running": running,
            "jobs_count": len(
                job_scheduler.get_jobs()
            ),
            "interval_seconds": (
                SCHEDULER_INTERVAL_SECONDS
            ),
        },
    )


health_monitor = HealthMonitor(
    scheduler_check=scheduler_health_check,
)


@app.on_event("startup")
def start_scheduler() -> None:
    if not job_scheduler.running:
        job_scheduler.start()

    log_event(
        "SCHEDULER_STARTED",
        message="Scheduler started",
        jobs_count=len(
            job_scheduler.get_jobs()
        ),
    )


@app.on_event("shutdown")
def stop_scheduler() -> None:
    if job_scheduler.running:
        job_scheduler.shutdown()

    log_event(
        "SCHEDULER_STOPPED",
        message="Scheduler stopped",
    )


@app.get("/health")
def health() -> JSONResponse:
    log_event(
        "HEALTH_CHECK_STARTED",
        message="System health check started",
    )

    report = health_monitor.check_all()
    payload = report.to_dict()

    log_event(
        "HEALTH_CHECK_COMPLETED",
        message="System health check completed",
        healthy=report.healthy,
        status=report.status,
        checks_count=len(
            report.checks
        ),
    )

    status_code = (
        200
        if report.healthy
        else 503
    )

    return JSONResponse(
        status_code=status_code,
        content=payload,
    )


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
        