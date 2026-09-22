from decimal import Decimal, InvalidOperation

from sqlalchemy import text

from database.postgres_sql import get_engine


def _normalize_numeric(value):
    """
    Convert extracted financial values to numeric values in USD millions.

    Examples:
        "$391,035"          -> Decimal("391035")
        "391,035"           -> Decimal("391035")
        "$391.035 billion"  -> Decimal("391035")
        None                -> None
    """

    if value is None:
        return None

    text_value = str(value).strip().lower()

    is_billion = "billion" in text_value

    cleaned = (
        text_value
        .replace("$", "")
        .replace(",", "")
        .replace("billions", "")
        .replace("billion", "")
        .replace("millions", "")
        .replace("million", "")
        .strip()
    )

    try:
        number = Decimal(cleaned)
    except InvalidOperation:
        return None

    if is_billion:
        number *= Decimal("1000")

    return number


def _format_list_field(metrics: dict, *keys: str) -> str | None:
    """
    Convert list-based qualitative fields to newline-separated text.
    """

    value = next(
        (
            metrics.get(key)
            for key in keys
            if metrics.get(key) is not None
        ),
        None,
    )

    if value is None:
        return None

    if isinstance(value, str):
        return value

    return "\n".join(str(item) for item in value)


def save_metrics(
    *,
    document_id: str,
    company: str,
    ticker: str,
    fiscal_year: int,
    filing_type: str,
    metrics: dict,
) -> None:
    """
    Insert or update financial metrics for one filing.

    Numeric KPI values are stored in USD millions.
    """

    engine = get_engine()

    query = """
    INSERT INTO financial_metrics (
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
        growth_drivers
    )
    VALUES (
        :document_id,
        :company,
        :ticker,
        :fiscal_year,
        :filing_type,
        :revenue,
        :net_income,
        :operating_income,
        :operating_cash_flow,
        :total_assets,
        :total_liabilities,
        :risk_factors,
        :growth_drivers
    )

    ON CONFLICT (ticker, fiscal_year, filing_type)

    DO UPDATE SET
        document_id = EXCLUDED.document_id,
        company = EXCLUDED.company,

        revenue = EXCLUDED.revenue,
        net_income = EXCLUDED.net_income,
        operating_income = EXCLUDED.operating_income,
        operating_cash_flow = EXCLUDED.operating_cash_flow,
        total_assets = EXCLUDED.total_assets,
        total_liabilities = EXCLUDED.total_liabilities,

        risk_factors = EXCLUDED.risk_factors,
        growth_drivers = EXCLUDED.growth_drivers,

        updated_at = CURRENT_TIMESTAMP;
    """

    params = {
        "document_id": document_id,
        "company": company,
        "ticker": ticker,
        "fiscal_year": fiscal_year,
        "filing_type": filing_type,

        "revenue": _normalize_numeric(
            metrics.get("revenue")
            or metrics.get("Revenue")
        ),

        "net_income": _normalize_numeric(
            metrics.get("net_income")
            or metrics.get("Net Income")
        ),

        "operating_income": _normalize_numeric(
            metrics.get("operating_income")
            or metrics.get("Operating Income")
        ),

        "operating_cash_flow": _normalize_numeric(
            metrics.get("cash_flow")
            or metrics.get(
                "Cash Flow from Operating Activities"
            )
        ),

        "total_assets": _normalize_numeric(
            metrics.get("total_assets")
            or metrics.get("Total Assets")
        ),

        "total_liabilities": _normalize_numeric(
            metrics.get("total_liabilities")
            or metrics.get("Total Liabilities")
        ),

        "risk_factors": _format_list_field(
            metrics,
            "risk_factors",
            "top_risk_factors",
            "Top Risk Factors",
        ),

        "growth_drivers": _format_list_field(
            metrics,
            "growth_drivers",
            "top_growth_drivers",
            "Top Growth Drivers",
        ),
    }

    with engine.begin() as connection:
        connection.execute(
            text(query),
            params,
        )

    print(
        f"Saved metrics for "
        f"{ticker} {fiscal_year} {filing_type}"
    )