from database.connection import get_connection


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(10),
            price FLOAT,
            signal VARCHAR(10)
        );
    """)

    connection.commit()
    cursor.close()
    connection.close()


if __name__ == "__main__":
    create_tables()
    