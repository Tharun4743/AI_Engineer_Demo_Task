from src.storage.dedup import Deduplicator


def test_url_normalization():
    dedup = Deduplicator()
    url1 = "https://www.openai.com/research?utm_source=twitter&utm_medium=social"
    url2 = "https://openai.com/research/"
    url3 = "https://openai.com/research?utm_campaign=launch#abstract"

    assert dedup.normalize_url(url1) == "https://openai.com/research"
    assert dedup.normalize_url(url2) == "https://openai.com/research"
    assert dedup.normalize_url(url3) == "https://openai.com/research"


def test_hash_deduplication():
    dedup = Deduplicator()
    url = "https://huggingface.co/papers/2401.12345"

    assert dedup.is_seen(url) is False
    assert dedup.mark_seen(url) is True
    assert dedup.is_seen(url) is True
    assert dedup.mark_seen(url) is False  # Duplicate!
