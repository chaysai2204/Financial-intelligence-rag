from types import SimpleNamespace

from rag.query_aware_retriever import (
    build_retrieval_targets,
    detect_companies,
    detect_years,
    query_aware_retrieve,
)


def test_detect_company_aliases():
    assert detect_companies(
        "Compare AAPL and Microsoft"
    ) == ["Apple", "Microsoft"]


def test_detect_years():
    assert detect_years(
        "Compare Apple 2023 with 2024"
    ) == [2023, 2024]


def test_multiple_companies_single_year():
    targets = build_retrieval_targets(
        "Compare Apple and NVIDIA in 2024"
    )

    assert len(targets) == 2

    assert targets[0].company == "Apple"
    assert targets[0].year == 2024

    assert targets[1].company == "NVIDIA"
    assert targets[1].year == 2024


def test_single_company_multiple_years():
    targets = build_retrieval_targets(
        "Compare Apple 2023 and 2024"
    )

    assert len(targets) == 2

    assert targets[0].company == "Apple"
    assert targets[0].year == 2023

    assert targets[1].company == "Apple"
    assert targets[1].year == 2024


class FakeRetriever:
    def invoke(
        self,
        query,
        company=None,
        year=None,
        top_k=5,
    ):
        if company == "Apple":
            return [
                SimpleNamespace(
                    metadata={
                        "document_id": "AAPL_2024_10K",
                        "chunk_index": 1,
                    },
                    page_content="Apple evidence 1",
                ),
                SimpleNamespace(
                    metadata={
                        "document_id": "AAPL_2024_10K",
                        "chunk_index": 2,
                    },
                    page_content="Apple evidence 2",
                ),
            ]

        if company == "NVIDIA":
            return [
                SimpleNamespace(
                    metadata={
                        "document_id": "NVDA_2024_10K",
                        "chunk_index": 1,
                    },
                    page_content="NVIDIA evidence 1",
                ),
                SimpleNamespace(
                    metadata={
                        "document_id": "NVDA_2024_10K",
                        "chunk_index": 2,
                    },
                    page_content="NVIDIA evidence 2",
                ),
            ]

        return []


def test_balanced_multi_company_merge():
    docs = query_aware_retrieve(
        retriever=FakeRetriever(),
        question="Compare Apple and NVIDIA in 2024",
        final_top_k=4,
        per_target_k=5,
    )

    document_ids = [
        doc.metadata["document_id"]
        for doc in docs
    ]

    assert document_ids == [
        "AAPL_2024_10K",
        "NVDA_2024_10K",
        "AAPL_2024_10K",
        "NVDA_2024_10K",
    ]

    def test_all_company_aliases():
        assert detect_companies("AAPL") == ["Apple"]
        assert detect_companies("MSFT") == ["Microsoft"]
        assert detect_companies("NVDA") == ["NVIDIA"]
        assert detect_companies("AMZN") == ["Amazon"]
        assert detect_companies("GOOGL") == ["Alphabet"]
        assert detect_companies("Google") == ["Alphabet"]


    def test_multiple_companies_without_year():
        targets = build_retrieval_targets(
            "Compare Apple and Microsoft"
        )

        assert len(targets) == 2
        assert targets[0].company == "Apple"
        assert targets[1].company == "Microsoft"

        assert targets[0].year is None
        assert targets[1].year is None


    def test_no_detected_metadata_returns_empty_targets():
        targets = build_retrieval_targets(
            "What risks were discussed?"
        )

        assert targets == []


    class GlobalFallbackRetriever:
        def __init__(self):
            self.last_kwargs = None

        def invoke(self, **kwargs):
            self.last_kwargs = kwargs
            return []


    def test_global_fallback_when_no_target_detected():
        retriever = GlobalFallbackRetriever()

        query_aware_retrieve(
            retriever=retriever,
            question="What risks were discussed?",
            final_top_k=5,
        )

        assert retriever.last_kwargs == {
            "query": "What risks were discussed?",
            "top_k": 5,
        }