from dotenv import load_dotenv

import os

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

load_dotenv()


def create_index(
    endpoint: str,
    api_key: str,
    index_name: str,
    embedding_dimensions: int = 1536,
) -> None:
    """
    Create or update the Azure AI Search index.

    The index stores:
    - document provenance metadata
    - chunk text
    - chunk embeddings
    """

    client = SearchIndexClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(api_key),
    )

    fields = [

        # -----------------------------------------------------
        # Chunk identity
        # -----------------------------------------------------

        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
        ),

        # -----------------------------------------------------
        # Document provenance
        # -----------------------------------------------------

        SimpleField(
            name="document_id",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        SimpleField(
            name="company",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        SimpleField(
            name="ticker",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        SimpleField(
            name="year",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        SimpleField(
            name="filing_type",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        SimpleField(
            name="source_file",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        SimpleField(
            name="file_hash",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        SimpleField(
            name="chunk_index",
            type=SearchFieldDataType.Int32,
            filterable=True,
            sortable=True,
        ),

        # -----------------------------------------------------
        # Chunk content
        # -----------------------------------------------------

        SearchField(
            name="content",
            type=SearchFieldDataType.String,
            searchable=True,
        ),

        # -----------------------------------------------------
        # Embedding vector
        # -----------------------------------------------------

        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(
                SearchFieldDataType.Single
            ),
            vector_search_dimensions=embedding_dimensions,
            vector_search_profile_name="vector-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-config"
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="hnsw-config",
            )
        ],
    )

    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
    )

    client.create_or_update_index(index)

    print(
        f"Index '{index_name}' created or updated successfully."
    )


if __name__ == "__main__":

    create_index(
        endpoint=os.getenv(
            "AZURE_SEARCH_ENDPOINT"
        ),
        api_key=os.getenv(
            "AZURE_SEARCH_API_KEY"
        ),
        index_name=os.getenv(
            "AZURE_SEARCH_INDEX_NAME"
        ),
    )