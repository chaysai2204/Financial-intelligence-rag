import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database.query_metrics import get_metric
from llm.azure_openai import (
    get_embedding_client,
    get_openai_client,
)
from rag.query_router import route_query
from vectorstore.azure_ai_search import (
    AzureAISearchVectorStore,
    DenseRetriever,
)


router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    company: str | None = None
    year: int | None = None


METRIC_DISPLAY_NAMES = {
    "revenue": "Revenue",
    "net_income": "Net income",
    "operating_income": "Operating income",
    "operating_cash_flow": "Cash flow from operating activities",
    "total_assets": "Total assets",
    "total_liabilities": "Total liabilities",
}


def format_structured_answer(
    *,
    company: str,
    year: int,
    metric: str,
    value,
) -> str:
    """
    Format structured PostgreSQL KPI values.

    Database values are stored in USD millions.
    """

    display_name = METRIC_DISPLAY_NAMES[metric]

    formatted_value = f"{value:,.0f}"

    return (
        f"{display_name} for {company} in fiscal year {year} "
        f"was ${formatted_value} million."
    )


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        # -----------------------------------------------------
        # 1. Route the question
        # -----------------------------------------------------

        decision = route_query(
            question=request.question,
            company=request.company,
            year=request.year,
        )

        print(
            f"[router] route={decision.route} "
            f"metric={decision.metric} "
            f"reason={decision.reason}"
        )

        # -----------------------------------------------------
        # 2. Structured PostgreSQL path
        # -----------------------------------------------------

        if decision.route == "structured":
            result = get_metric(
                company=request.company,
                fiscal_year=request.year,
                metric=decision.metric,
            )

            # Structured database may not contain this filing yet.
            # Fall back to RAG instead of returning an incorrect answer.
            if result is not None and result["value"] is not None:
                answer = format_structured_answer(
                    company=result["company"],
                    year=result["fiscal_year"],
                    metric=decision.metric,
                    value=result["value"],
                )

                source = {
                    "citation_id": 1,
                    "document_id": result["document_id"],
                    "company": result["company"],
                    "ticker": result["ticker"],
                    "year": result["fiscal_year"],
                    "filing_type": result["filing_type"],
                    "source_file": None,
                    "chunk_index": None,
                    "rank": None,
                    "evidence": (
                        f"{METRIC_DISPLAY_NAMES[decision.metric]}: "
                        f"{result['value']} million"
                    ),
                }

                return {
                    "answer": answer,
                    "sources": [source],
                    "route": "structured",
                }

            print(
                "[router] Structured record unavailable. "
                "Falling back to RAG."
            )

        # -----------------------------------------------------
        # 3. Existing Dense RAG path
        # -----------------------------------------------------

        vector_store = AzureAISearchVectorStore(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            api_key=os.getenv("AZURE_SEARCH_API_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        )

        embeddings = get_embedding_client()

        retriever = DenseRetriever(
            vector_store.client,
            embeddings,
        )

        if request.company and request.year:
            docs = retriever.invoke(
                query=request.question,
                company=request.company,
                year=request.year,
                top_k=5,
            )
        else:
            docs = retriever.invoke(
                query=request.question,
                top_k=5,
            )

        context_blocks = []
        sources = []

        for citation_id, doc in enumerate(
            docs,
            start=1,
        ):
            metadata = doc.metadata

            context_blocks.append(
                f"[Source {citation_id}]\n"
                f"{doc.page_content}"
            )

            sources.append(
                {
                    "citation_id": citation_id,
                    "document_id": metadata.get(
                        "document_id"
                    ),
                    "company": metadata.get("company"),
                    "ticker": metadata.get("ticker"),
                    "year": metadata.get("year"),
                    "filing_type": metadata.get(
                        "filing_type"
                    ),
                    "source_file": metadata.get(
                        "source_file"
                    ),
                    "chunk_index": metadata.get(
                        "chunk_index"
                    ),
                    "rank": metadata.get("rank"),
                    "evidence": doc.page_content,
                }
            )

        context = "\n\n".join(context_blocks)

        prompt = f"""
You are an expert financial analyst.

Answer the user's question using only the provided sources.

Citation rules:
- Cite the supporting source using [Source N].
- Every factual claim must be supported by at least one source.
- Use only source numbers that appear in the provided context.
- Do not invent citations.
- If the provided sources do not contain enough evidence to answer the question, say that you do not have enough information.
- When abstaining, do not cite unrelated sources as if they support the missing answer.
- Never substitute data from a different fiscal year for the year requested.

Context:
{context}

User Question:
{request.question}

Answer:
"""

        client = get_openai_client()

        response = client.chat.completions.create(
            model=os.getenv(
                "AZURE_OPENAI_CHAT_DEPLOYMENT"
            ),
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        answer = response.choices[0].message.content

        return {
            "answer": answer,
            "sources": sources,
            "route": "rag",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )