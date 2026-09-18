import os

from dotenv import load_dotenv

from vectorstore.azure_ai_search import AzureAISearchVectorStore


load_dotenv(".env")

store = AzureAISearchVectorStore(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    api_key=os.getenv("AZURE_SEARCH_API_KEY"),
    index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
)

results = store.client.search(
    search_text="*",
    filter="document_id eq 'NVDA_2023_10K'",
    top=1000,
)

wanted_indices = {82, 83, 84, 85, 86, 87, 88}

chunks = [
    result
    for result in results
    if result.get("chunk_index") in wanted_indices
]

chunks.sort(key=lambda x: x["chunk_index"])

for chunk in chunks:
    print("\n" + "=" * 100)
    print(f"CHUNK INDEX: {chunk['chunk_index']}")
    print(f"CHUNK ID: {chunk['id']}")
    print("=" * 100)
    print(chunk["content"])