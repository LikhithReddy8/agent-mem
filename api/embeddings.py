from sentence_transformers import SentenceTransformer

_embedder: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-mpnet-base-v2")
    return _embedder


def embed_text(text: str) -> list[float]:
    return get_embedder().encode(text).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in get_embedder().encode(texts)]
