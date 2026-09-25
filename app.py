from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv

from database.metrics import get_metrics
from database.postgres_sql import create_database
from database.create_table import create_tables
from vectorstore.create_index import create_index
from routes.ingestion import router as ingestion_router
from routes.chat import router as chat_router

load_dotenv()

app = FastAPI(title="FilingIQ — Financial Filing Intelligence")


@app.on_event("startup")
def startup_event():
    create_database()
    create_tables()

    try:
        create_index(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            api_key=os.getenv("AZURE_SEARCH_API_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        )
    except Exception as exc:
        print(f"Warning: Could not create vector index: {exc}")


app.include_router(ingestion_router, prefix="/api", tags=["Ingestion"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
def dashboard(request: Request):
    metrics = get_metrics()
    companies = sorted({row["company"] for row in metrics if row.get("company")})
    fiscal_years = sorted(
        {row["fiscal_year"] for row in metrics if row.get("fiscal_year") is not None},
        reverse=True,
    )

    client_metrics = [
        {
            "document_id": row.get("document_id"),
            "company": row.get("company"),
            "ticker": row.get("ticker"),
            "fiscal_year": row.get("fiscal_year"),
            "growth_drivers": row.get("growth_drivers") or "",
            "risk_factors": row.get("risk_factors") or "",
        }
        for row in metrics
    ]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "metrics": metrics,
            "client_metrics": client_metrics,
            "companies": companies,
            "fiscal_years": fiscal_years,
            "total_companies": len(companies),
            "total_reports": len(metrics),
            "latest_fiscal_year": fiscal_years[0] if fiscal_years else None,
        },
    )


@app.get("/api/metrics")
def metrics():
    return JSONResponse(content=get_metrics())


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
