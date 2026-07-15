from database.connection import get_connection


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DROP TABLE IF EXISTS signals;

        CREATE TABLE signals (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL,
            entry_price FLOAT NOT NULL,
            stop_price FLOAT NOT NULL,
            tp1_price FLOAT NOT NULL,
            tp2_price FLOAT NOT NULL,
            signal VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    connection.commit()
    cursor.close()
    connection.close()


if __name__ == "__main__":
    create_tables()
    
