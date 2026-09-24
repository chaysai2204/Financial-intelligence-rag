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