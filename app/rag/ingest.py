import uuid
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import get_settings
from app.rag.embeddings import EMBEDDING_DIM, embed_texts

settings = get_settings()

_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)


def ensure_collection(client: QdrantClient | None = None) -> None:
    client = client or get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


def ingest_documents(docs: list[tuple[str, str]]) -> int:
    """docs: list of (source_name, raw_text). Chunks, embeds, and upserts into Qdrant.

    Returns the number of chunks ingested.
    """
    client = get_qdrant_client()
    ensure_collection(client)

    chunks: list[str] = []
    payloads: list[dict] = []
    for source, text in docs:
        for chunk in _splitter.split_text(text):
            chunks.append(chunk)
            payloads.append({"source": source, "text": chunk})

    if not chunks:
        return 0

    vectors = embed_texts(chunks)
    points = [
        PointStruct(id=str(uuid.uuid4()), vector=vector, payload=payload)
        for vector, payload in zip(vectors, payloads)
    ]
    client.upsert(collection_name=settings.qdrant_collection, points=points)
    return len(points)


def ingest_directory(directory: Path) -> int:
    docs = [(p.name, p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*.md"))]
    return ingest_documents(docs)
