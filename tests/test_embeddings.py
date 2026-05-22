from api.embeddings import get_embedder, embed_text, embed_batch


def test_embed_text_returns_768_dims():
    result = embed_text("JWT token refresh race condition in auth middleware")
    assert len(result) == 768


def test_embed_text_is_float_list():
    result = embed_text("payment webhook handler")
    assert isinstance(result, list)
    assert isinstance(result[0], float)


def test_embed_batch_returns_multiple():
    texts = ["auth service", "payment service", "notification service"]
    results = embed_batch(texts)
    assert len(results) == 3
    assert all(len(r) == 768 for r in results)


def test_get_embedder_is_singleton():
    e1 = get_embedder()
    e2 = get_embedder()
    assert e1 is e2
