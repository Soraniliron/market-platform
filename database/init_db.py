from database.connection import get_connection


def create_tables() -> None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS signals (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL,
            entry_price DOUBLE PRECISION NOT NULL,
            stop_price DOUBLE PRECISION NOT NULL,
            tp1_price DOUBLE PRECISION NOT NULL,
            tp2_price DOUBLE PRECISION NOT NULL,
            signal VARCHAR(20) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
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

        CREATE TABLE IF NOT EXISTS scan_runs (
            id UUID PRIMARY KEY,
            started_at TIMESTAMPTZ NOT NULL,
            completed_at TIMESTAMPTZ,
            timeframe_minutes INTEGER NOT NULL,
            trading_date DATE NOT NULL,
            status VARCHAR(20) NOT NULL,
            scanned_count INTEGER NOT NULL DEFAULT 0,
            error_message TEXT,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb
        );

        CREATE TABLE IF NOT EXISTS scan_results (
            id BIGSERIAL PRIMARY KEY,
            scan_run_id UUID NOT NULL
                REFERENCES scan_runs(id)
                ON DELETE CASCADE,
            ticker VARCHAR(10) NOT NULL,
            rank INTEGER,
            scan_status VARCHAR(20) NOT NULL,
            score DOUBLE PRECISION NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            change_percent DOUBLE PRECISION NOT NULL,
            volume DOUBLE PRECISION NOT NULL,
            vwap DOUBLE PRECISION,
            above_vwap BOOLEAN,
            reason TEXT NOT NULL,
            engine_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS decisions (
            id UUID PRIMARY KEY,
            scan_run_id UUID
                REFERENCES scan_runs(id)
                ON DELETE SET NULL,
            ticker VARCHAR(10),
            decision_status VARCHAR(20) NOT NULL,
            score DOUBLE PRECISION NOT NULL,
            selected_rank INTEGER,
            candidates_count INTEGER NOT NULL DEFAULT 0,
            reason TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb
        );

        CREATE TABLE IF NOT EXISTS trade_plans (
            id UUID PRIMARY KEY,
            decision_id UUID
                REFERENCES decisions(id)
                ON DELETE CASCADE,
            ticker VARCHAR(10) NOT NULL,
            entry_status VARCHAR(20) NOT NULL,
            entry_price DOUBLE PRECISION,
            stop_price DOUBLE PRECISION,
            tp1_price DOUBLE PRECISION,
            tp2_price DOUBLE PRECISION,
            risk_per_share DOUBLE PRECISION,
            risk_reward_tp1 DOUBLE PRECISION,
            risk_reward_tp2 DOUBLE PRECISION,
            invalidation_price DOUBLE PRECISION,
            reason TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb
        );

        CREATE TABLE IF NOT EXISTS risk_results (
            id UUID PRIMARY KEY,
            trade_plan_id UUID
                REFERENCES trade_plans(id)
                ON DELETE CASCADE,
            ticker VARCHAR(10) NOT NULL,
            risk_status VARCHAR(20) NOT NULL,
            quantity INTEGER NOT NULL,
            position_value DOUBLE PRECISION NOT NULL,
            total_position_value DOUBLE PRECISION NOT NULL,
            risk_per_share DOUBLE PRECISION NOT NULL,
            total_risk DOUBLE PRECISION NOT NULL,
            maximum_risk_value DOUBLE PRECISION NOT NULL,
            maximum_position_value DOUBLE PRECISION NOT NULL,
            maximum_allowed_value DOUBLE PRECISION NOT NULL,
            reason TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS notification_logs (
            id UUID PRIMARY KEY,
            ticker VARCHAR(10),
            notification_type VARCHAR(30) NOT NULL,
            delivery_status VARCHAR(20) NOT NULL,
            subject TEXT NOT NULL,
            recipients JSONB NOT NULL,
            attempts_count INTEGER NOT NULL,
            sent_at TIMESTAMPTZ,
            error_message TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_records (
            audit_id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL,
            ticker VARCHAR(10) NOT NULL,
            event VARCHAR(30) NOT NULL,
            decision VARCHAR(20) NOT NULL,
            score DOUBLE PRECISION NOT NULL,
            entry_price DOUBLE PRECISION,
            stop_price DOUBLE PRECISION,
            tp1_price DOUBLE PRECISION,
            tp2_price DOUBLE PRECISION,
            reason TEXT NOT NULL,
            input_data JSONB NOT NULL DEFAULT '{}'::jsonb,
            output_data JSONB NOT NULL DEFAULT '{}'::jsonb
        );

        CREATE TABLE IF NOT EXISTS performance_records (
            id BIGSERIAL PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            decision VARCHAR(20) NOT NULL,
            result VARCHAR(20) NOT NULL,
            entry_price DOUBLE PRECISION,
            exit_price DOUBLE PRECISION,
            stop_price DOUBLE PRECISION,
            tp1_price DOUBLE PRECISION,
            tp2_price DOUBLE PRECISION,
            return_percent DOUBLE PRECISION,
            decision_score DOUBLE PRECISION NOT NULL,
            engine_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
            selected_rank INTEGER,
            notes TEXT NOT NULL DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_scan_results_run
            ON scan_results(scan_run_id);

        CREATE INDEX IF NOT EXISTS idx_scan_results_ticker
            ON scan_results(ticker);

        CREATE INDEX IF NOT EXISTS idx_decisions_created_at
            ON decisions(created_at);

        CREATE INDEX IF NOT EXISTS idx_audit_records_created_at
            ON audit_records(created_at);

        CREATE INDEX IF NOT EXISTS idx_performance_records_created_at
            ON performance_records(created_at);
        """
    )

    connection.commit()
    cursor.close()
    connection.close()


if __name__ == "__main__":
    create_tables()
    