from sqlalchemy import text

from database.postgres_sql import get_engine


def get_metrics():
    """
    Return stored financial metrics ordered by company and fiscal year.
    """

    engine = get_engine()

    query = """
    SELECT
        id,
        document_id,
        company,
        ticker,
        fiscal_year,
        filing_type,
        revenue,
        net_income,
        operating_income,
        operating_cash_flow,
        total_assets,
        total_liabilities,
        risk_factors,
        growth_drivers,
        created_at,
        updated_at
    FROM financial_metrics
    ORDER BY company, fiscal_year DESC;
    """

    with engine.connect() as connection:
        result = connection.execute(text(query))

        rows = [
            dict(row._mapping)
            for row in result
        ]

    return rows