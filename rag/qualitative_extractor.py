from pydantic import BaseModel, Field

from llm.azure_openai import get_structured_completion


class QualitativeInsights(BaseModel):
    growth_drivers: list[str] = Field(
        default_factory=list
    )

    risk_factors: list[str] = Field(
        default_factory=list
    )


def _build_context(documents) -> str:
    blocks = []

    for doc in documents:
        metadata = doc.metadata

        blocks.append(
            f"Document: {metadata.get('document_id')}\n"
            f"Company: {metadata.get('company')}\n"
            f"Fiscal Year: {metadata.get('year')}\n"
            f"Evidence:\n"
            f"{doc.page_content}"
        )

    return "\n\n---\n\n".join(blocks)


def extract_qualitative_insights(
    retriever,
    company: str,
    year: int,
) -> dict:
    """
    Extract evidence-grounded growth drivers and risk factors
    from an already-indexed annual filing.

    This function performs retrieval only.
    It does not upload or modify Azure Search documents.
    """

    # ---------------------------------------------------------
    # 1. Retrieve evidence about growth / business drivers
    # ---------------------------------------------------------

    growth_documents = retriever.invoke(
        query=(
            "management discussion results of operations "
            "revenue increased growth driven by services net sales "
            "services growth installed base subscriptions "
            "cost savings gross margin improvement "
            "product demand geographic growth business expansion"
        ),
        company=company,
        year=year,
        top_k=5,
    )


    # ---------------------------------------------------------
    # 2. Retrieve evidence from risk disclosures
    # ---------------------------------------------------------

    risk_documents = retriever.invoke(
        query=(
            "risk factors business risks competition supply chain "
            "third party manufacturing regulation economic conditions "
            "cybersecurity privacy product demand operational risks"
        ),
        company=company,
        year=year,
        top_k=5,
    )


    growth_context = _build_context(
        growth_documents
    )

    risk_context = _build_context(
        risk_documents
    )


    # ---------------------------------------------------------
    # 3. Evidence-grounded extraction
    # ---------------------------------------------------------

    prompt = f"""
You are an expert financial analyst reviewing a company's annual filing.

Company: {company}
Fiscal Year: {year}

Your task is to extract concise, evidence-grounded qualitative insights.

GROWTH EVIDENCE:
{growth_context}

RISK EVIDENCE:
{risk_context}

Return:

1. growth_drivers
   - Return 3 to 5 factors that the filing explicitly links to improved
     revenue, margin, demand, business growth, or financial performance.
   - Prefer language such as "increased due to", "driven by",
     "benefited from", or other explicit causal support.
   - Do NOT treat seasonality, generic product launches, or factors that
     merely "could impact" results as growth drivers.
   - Explain each driver in one concise sentence.

2. risk_factors
   - 3 to 5 important risks explicitly supported by the provided evidence
   - Explain each risk in one concise sentence
   - Focus on material business, operational, competitive, supply-chain,
     regulatory, technological, or economic risks

Rules:
- Use ONLY the provided evidence.
- Do not infer unsupported causes or risks.
- Do not use outside knowledge.
- Do not invent facts.
- Keep company and fiscal-year attribution correct.
- Do not include duplicate points.
- If evidence for a category is insufficient, return an empty list for it.
"""

    result = get_structured_completion(
        prompt=prompt,
        response_model=QualitativeInsights,
    )


    return {
        "growth_drivers": result.growth_drivers,
        "risk_factors": result.risk_factors,
    }