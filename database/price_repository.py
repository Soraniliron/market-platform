from datetime import datetime
from typing import Any

from psycopg2.extras import execute_values

from database.connection import get_connection


def delete_daily_prices(ticker: str) -> int:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM daily_prices
        WHERE ticker = %s;
        """,
        (ticker,),
    )

    deleted_rows = cursor.rowcount

    connection.commit()
    cursor.close()
    connection.close()

    return deleted_rows


def save_daily_prices(
    ticker: str,
    rows: list[dict[str, Any]],
) -> int:
    if not rows:
        return 0

    values = []

    for row in rows:
        trade_date = datetime.fromtimestamp(
            row["t"] / 1000
        ).date()

        values.append(
            (
                ticker,
                trade_date,
                row["o"],
                row["h"],
                row["l"],
                row["c"],
                int(row["v"]),
            )
        )

    connection = get_connection()
    cursor = connection.cursor()

    execute_values(
        cursor,
        """
        INSERT INTO daily_prices (
            ticker,
            trade_date,
            open,
            high,
            low,
            close,
            volume
        )
        VALUES %s
        ON CONFLICT (ticker, trade_date)
        DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume
        """,
        values,
    )

    connection.commit()
    cursor.close()
    connection.close()

    return len(values)
