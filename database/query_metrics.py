from sqlalchemy import text

from database.postgres_sql import get_engine


SUPPORTED_METRICS = {
    "revenue",
    "net_income",
    "operating_income",
    "operating_cash_flow",
    "total_assets",
    "total_liabilities",
}


def get_metric(
    *,
    company: str,
    fiscal_year: int,
    metric: str,
) -> dict | None:
    """
    Retrieve one structured financial KPI from PostgreSQL.

    Financial values are stored in USD millions.
    """

    if metric not in SUPPORTED_METRICS:
        raise ValueError(
            f"Unsupported metric: {metric}"
        )

    engine = get_engine()

    # Column names cannot be parameterized in SQL,
    # so metric is validated against SUPPORTED_METRICS first.
    query = text(
        f"""
        SELECT
            document_id,
            company,
            ticker,
            fiscal_year,
            filing_type,
            {metric} AS value
        FROM financial_metrics
        WHERE LOWER(company) = LOWER(:company)
          AND fiscal_year = :fiscal_year
        ORDER BY updated_at DESC
        LIMIT 1;
        """
    )

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {
                "company": company,
                "fiscal_year": fiscal_year,
            },
        ).fetchone()

    if row is None:
        return None

    return dict(row._mapping)