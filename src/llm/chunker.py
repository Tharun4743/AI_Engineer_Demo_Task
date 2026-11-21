import re
from typing import List

try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False


class SemanticChunker:
    """Token budget manager and semantic boundary truncator."""

    def __init__(self, model_encoding: str = "cl100k_base"):
        self.encoding = None
        if HAS_TIKTOKEN:
            try:
                self.encoding = tiktoken.get_encoding(model_encoding)
            except Exception:
                self.encoding = None

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        if self.encoding:
            return len(self.encoding.encode(text))
        # Word-based token estimation (average 1 word = 1.3 tokens)
        return int(len(text.split()) * 1.3)

    def truncate_to_budget(self, text: str, max_tokens: int = 4000) -> str:
        """Semantically truncates text to fit within token budget, respecting paragraph/sentence boundaries."""
        if not text or self.count_tokens(text) <= max_tokens:
            return text

        # Split into paragraphs
        paragraphs = text.split("\n\n")
        selected_paragraphs: List[str] = []
        current_tokens = 0

        for p in paragraphs:
            p_tokens = self.count_tokens(p)
            if current_tokens + p_tokens <= max_tokens:
                selected_paragraphs.append(p)
                current_tokens += p_tokens
            else:
                # Split large paragraph by sentences
                sentences = re.split(r"(?<=[.!?])\s+", p)
                selected_sentences: List[str] = []
                for s in sentences:
                    cand = " ".join(selected_sentences + [s]).strip()
                    if self.count_tokens(cand) + current_tokens <= max_tokens:
                        selected_sentences.append(s)
                    else:
                        break
                if selected_sentences:
                    selected_paragraphs.append(" ".join(selected_sentences))
                break

        res = "\n\n".join(selected_paragraphs).strip()
        # Fallback if single sentence exceeded
        if not res and text:
            words = text.split()
            # Approximate words to budget
            target_words = max(1, int(max_tokens / 1.3))
            res = " ".join(words[:target_words]) + "..."
        return res

    def halve_payload(self, text: str) -> str:
        """Halves the text payload strictly by token budget."""
        tokens = self.count_tokens(text)
        target_tokens = max(1, tokens // 2)
        return self.truncate_to_budget(text, max_tokens=target_tokens)


semantic_chunker = SemanticChunker()
