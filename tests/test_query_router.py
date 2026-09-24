from rag.query_router import route_query


def test_exact_kpi_routes_to_structured():
    decision = route_query(
        question="What was Apple revenue in 2024?",
        company="Apple",
        year=2024,
    )

    assert decision.route == "structured"
    assert decision.metric == "revenue"


def test_qualitative_kpi_routes_to_rag():
    decision = route_query(
        question="Why did Apple revenue change in 2024?",
        company="Apple",
        year=2024,
    )

    assert decision.route == "rag"


def test_question_without_supported_metric_routes_to_rag():
    decision = route_query(
        question="What risks did Apple discuss?",
        company="Apple",
        year=2024,
    )

    assert decision.route == "rag"

def test_missing_company_routes_to_rag():
    decision = route_query(
        question="What was revenue in 2024?",
        company=None,
        year=2024,
    )

    assert decision.route == "rag"


def test_missing_year_routes_to_rag():
    decision = route_query(
        question="What was Apple revenue?",
        company="Apple",
        year=None,
    )

    assert decision.route == "rag"


def test_operating_cash_flow_alias_routes_to_structured():
    decision = route_query(
        question="What was Apple's cash flow from operating activities?",
        company="Apple",
        year=2024,
    )

    assert decision.route == "structured"
    assert decision.metric == "operating_cash_flow"


def test_explanatory_question_stays_rag():
    decision = route_query(
        question="Explain why Apple's operating income changed.",
        company="Apple",
        year=2024,
    )

    assert decision.route == "rag"