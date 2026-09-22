from sqlalchemy import text

from database.postgres_sql import get_engine


def create_tables() -> None:
    """
    Create the cleaned financial_metrics table.

    Financial KPI values are stored in USD millions.
    """

    engine = get_engine()

    query = """
    CREATE TABLE IF NOT EXISTS financial_metrics (
        id SERIAL PRIMARY KEY,

        document_id VARCHAR(150),
        company VARCHAR(100) NOT NULL,
        ticker VARCHAR(20) NOT NULL,
        fiscal_year INTEGER NOT NULL,
        filing_type VARCHAR(20) NOT NULL,

        revenue NUMERIC,
        net_income NUMERIC,
        operating_income NUMERIC,
        operating_cash_flow NUMERIC,
        total_assets NUMERIC,
        total_liabilities NUMERIC,

        risk_factors TEXT,
        growth_drivers TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        CONSTRAINT uq_financial_metrics_filing
            UNIQUE (ticker, fiscal_year, filing_type)
    );
    """

    with engine.begin() as connection:
        connection.execute(text(query))

    print("financial_metrics table created successfully.")


if __name__ == "__main__":
    create_tables()