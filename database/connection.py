import psycopg2


def get_connection():
    return psycopg2.connect(
        host="db",
        database="market_db",
        user="market_user",
        password="market_password",
    )
    