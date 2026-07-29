from database.connection import get_connection


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL,
            entry_price DOUBLE PRECISION NOT NULL,
            stop_price DOUBLE PRECISION NOT NULL,
            tp1_price DOUBLE PRECISION NOT NULL,
            tp2_price DOUBLE PRECISION NOT NULL,
            signal VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS daily_prices (
            ticker VARCHAR(10) NOT NULL,
            trade_date DATE NOT NULL,
            open DOUBLE PRECISION NOT NULL,
            high DOUBLE PRECISION NOT NULL,
            low DOUBLE PRECISION NOT NULL,
            close DOUBLE PRECISION NOT NULL,
            volume BIGINT NOT NULL,
            PRIMARY KEY (ticker, trade_date)
        );
    """)

    connection.commit()
    cursor.close()
    connection.close()


if __name__ == "__main__":
    create_tables()
    
    
