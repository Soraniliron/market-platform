from __future__ import annotations

import os

import psycopg2
from psycopg2.extensions import connection


def get_connection() -> connection:
    return psycopg2.connect(
        host=os.getenv(
            "DB_HOST",
            "localhost",
        ),
        port=int(
            os.getenv(
                "DB_PORT",
                "5432",
            )
        ),
        database=os.getenv(
            "DB_NAME",
            "market_db",
        ),
        user=os.getenv(
            "DB_USER",
            "market_user",
        ),
        password=os.getenv(
            "DB_PASSWORD",
            "market_password",
        ),
    )
    