from sqlalchemy import text

from database.postgres_sql import get_engine


def update_qualitative_insights(
    *,
    ticker: str,
    fiscal_year: int,
    filing_type: str,
    growth_drivers: list[str],
    risk_factors: list[str],
) -> None:
    """
    Update only qualitative fields for an existing filing.

    Existing numeric KPI values are preserved.
    """

    engine = get_engine()

    query = text(
        """
        UPDATE financial_metrics
        SET
            growth_drivers = :growth_drivers,
            risk_factors = :risk_factors,
            updated_at = CURRENT_TIMESTAMP
        WHERE ticker = :ticker
          AND fiscal_year = :fiscal_year
          AND filing_type = :filing_type;
        """
    )

    params = {
        "ticker": ticker,
        "fiscal_year": fiscal_year,
        "filing_type": filing_type,
        "growth_drivers": (
            "\n".join(growth_drivers)
            if growth_drivers
            else None
        ),
        "risk_factors": (
            "\n".join(risk_factors)
            if risk_factors
            else None
        ),
    }

    with engine.begin() as connection:
        result = connection.execute(
            query,
            params,
        )

    if result.rowcount == 0:
        raise ValueError(
            f"No financial_metrics row found for "
            f"{ticker} {fiscal_year} {filing_type}"
        )

    print(
        f"Updated qualitative insights for "
        f"{ticker} {fiscal_year} {filing_type}"
    )