from datetime import date
from typing import Any

from database.connection import get_connection


def get_price_history(
    ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            trade_date,
            open,
            high,
            low,
            close,
            volume
        FROM daily_prices
        WHERE ticker = %s
    """

    parameters: list[Any] = [ticker]

    if start_date is not None:
        query += " AND trade_date >= %s"
        parameters.append(start_date)

    if end_date is not None:
        query += " AND trade_date <= %s"
        parameters.append(end_date)

    query += " ORDER BY trade_date ASC;"

    cursor.execute(query, parameters)
    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "trade_date": row[0],
            "open": row[1],
            "high": row[2],
            "low": row[3],
            "close": row[4],
            "volume": row[5],
        }
        for row in rows
    ]


def get_price_summary(ticker: str) -> dict[str, Any]:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*),
            MIN(trade_date),
            MAX(trade_date),
            MIN(low),
            MAX(high),
            AVG(close),
            AVG(volume)
        FROM daily_prices
        WHERE ticker = %s;
        """,
        (ticker,),
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None or row[0] == 0:
        raise ValueError(f"No price data found for ticker: {ticker}")

    return {
        "ticker": ticker,
        "rows_count": row[0],
        "first_date": row[1],
        "last_date": row[2],
        "lowest_price": float(row[3]),
        "highest_price": float(row[4]),
        "average_close": float(row[5]),
        "average_volume": float(row[6]),
    }
