from functools import lru_cache

from fastembed import TextEmbedding

# Small ONNX model that runs on CPU with no GPU/torch dependency and no API key —
# keeps embeddings free and local, separate from whichever LLM provider is chosen.
_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384


@lru_cache
def get_embedder() -> TextEmbedding:
    return TextEmbedding(model_name=_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    embedder = get_embedder()
    return [vec.tolist() for vec in embedder.embed(texts)]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
