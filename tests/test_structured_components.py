import pytest

from database.query_metrics import get_metric
from routes.chat import format_structured_answer


def test_structured_revenue_answer_format():
    answer = format_structured_answer(
        company="Apple",
        year=2024,
        metric="revenue",
        value=391035,
    )

    assert answer == (
        "Revenue for Apple in fiscal year 2024 "
        "was $391,035 million."
    )


def test_structured_net_income_answer_format():
    answer = format_structured_answer(
        company="Microsoft",
        year=2024,
        metric="net_income",
        value=88136,
    )

    assert answer == (
        "Net income for Microsoft in fiscal year 2024 "
        "was $88,136 million."
    )


def test_unsupported_metric_is_rejected():
    with pytest.raises(ValueError):
        get_metric(
            company="Apple",
            fiscal_year=2024,
            metric="gross_margin",
        )