from src.llm.chunker import semantic_chunker


def test_token_counting():
    text = "Hello world from the AI intelligence pipeline."
    tokens = semantic_chunker.count_tokens(text)
    assert tokens > 0


def test_semantic_truncation_preserves_sentences():
    paragraphs = [
        "First sentence. Second sentence.",
        "Third sentence. Fourth sentence.",
        "Fifth sentence. Sixth sentence."
    ]
    full_text = "\n\n".join(paragraphs)

    truncated = semantic_chunker.truncate_to_budget(full_text, max_tokens=10)
    assert len(truncated) < len(full_text)
    assert truncated.endswith(".")


def test_payload_halving():
    text = "Machine learning research paper abstract describing neural architectures. " * 20
    orig_tokens = semantic_chunker.count_tokens(text)
    halved = semantic_chunker.halve_payload(text)
    halved_tokens = semantic_chunker.count_tokens(halved)

    assert halved_tokens <= (orig_tokens // 2) + 5
