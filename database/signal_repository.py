from database.connection import get_connection


def save_signal(
    ticker: str,
    entry_price: float,
    stop_price: float,
    tp1_price: float,
    tp2_price: float,
    signal: str,
) -> None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO signals (
            ticker,
            entry_price,
            stop_price,
            tp1_price,
            tp2_price,
            signal
        )
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        (
            ticker,
            entry_price,
            stop_price,
            tp1_price,
            tp2_price,
            signal,
        ),
    )

    connection.commit()
    cursor.close()
    connection.close()


def get_signals():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            ticker,
            entry_price,
            stop_price,
            tp1_price,
            tp2_price,
            signal,
            created_at
        FROM signals
        ORDER BY created_at DESC;
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows
    