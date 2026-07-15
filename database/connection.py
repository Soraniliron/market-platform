import psycopg2


def get_connection():
    return psycopg2.connect(
        host="db",
        database="market_db",
        user="market_user",
        password="market_password",
    )


def save_signal(ticker, price, signal):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO signals (ticker, price, signal)
        VALUES (%s, %s, %s)
        """,
        (ticker, price, signal),
    )

    connection.commit()
    cursor.close()
    connection.close()


def get_signals():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, ticker, price, signal
        FROM signals
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows
    
