from datetime import date
from typing import Any

from database.connection import get_connection
from earnings.models import EarningsEvent


def create_earnings_table() -> None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS earnings_events (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(20) NOT NULL,
            report_date DATE NOT NULL,
            report_time VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (ticker, report_date)
        );
        """
    )

    connection.commit()
    cursor.close()
    connection.close()


def save_earnings_event(event: EarningsEvent) -> None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO earnings_events (
            ticker,
            report_date,
            report_time
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (ticker, report_date)
        DO UPDATE SET
            report_time = EXCLUDED.report_time;
        """,
        (
            event.ticker,
            event.report_date,
            event.report_time,
        ),
    )

    connection.commit()
    cursor.close()
    connection.close()


def get_earnings_events(
    ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[EarningsEvent]:
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            ticker,
            report_date,
            report_time
        FROM earnings_events
        WHERE ticker = %s
    """

    parameters: list[Any] = [ticker]

    if start_date is not None:
        query += " AND report_date >= %s"
        parameters.append(start_date)

    if end_date is not None:
        query += " AND report_date <= %s"
        parameters.append(end_date)

    query += " ORDER BY report_date ASC;"

    cursor.execute(query, parameters)
    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        EarningsEvent(
            ticker=row[0],
            report_date=row[1],
            report_time=row[2],
        )
        for row in rows
    ]
