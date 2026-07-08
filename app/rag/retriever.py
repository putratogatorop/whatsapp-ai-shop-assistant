from app.config import get_settings
from app.rag.embeddings import embed_query
from app.rag.ingest import get_qdrant_client

settings = get_settings()


def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """Embed `query`, search Qdrant, and return formatted context snippets for the LLM."""
    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        return "Knowledge base is empty — run scripts/ingest_knowledge_base.py first."

    vector = embed_query(query)
    hits = client.query_points(
        collection_name=settings.qdrant_collection, query=vector, limit=top_k
    ).points

    if not hits:
        return "No relevant information found in the knowledge base."

    snippets = [f"[{hit.payload['source']}] {hit.payload['text']}" for hit in hits]
    return "\n\n".join(snippets)
