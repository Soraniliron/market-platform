import psycopg2


def get_connection():
    return psycopg2.connect(
        host="db",
        database="market_db",
        user="market_user",
        password="market_password",
    )


def save_signal(
    ticker,
    entry_price,
    stop_price,
    tp1_price,
    tp2_price,
    signal,
):
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
        VALUES (%s, %s, %s, %s, %s, %s)
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

    cursor.execute("""
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
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows
    

