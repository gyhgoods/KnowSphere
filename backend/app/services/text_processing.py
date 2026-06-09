import re
import unicodedata
from dataclasses import dataclass

CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
HORIZONTAL_SPACE = re.compile(r"[^\S\n\t]+")
EXCESS_BLANK_LINES = re.compile(r"\n{3,}")
TOKEN_PATTERN = re.compile(r"[\u3400-\u9fff]|[A-Za-z0-9_]+|[^\s]")


@dataclass(frozen=True, slots=True)
class TextChunk:
    index: int
    content: str
    token_count: int
    start_offset: int
    end_offset: int


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = CONTROL_CHARACTERS.sub("", text)
    lines = [HORIZONTAL_SPACE.sub(" ", line).strip() for line in text.splitlines()]
    return EXCESS_BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()


def estimate_token_count(value: str) -> int:
    return len(TOKEN_PATTERN.findall(value))


def tokenize_text(value: str) -> list[str]:
    return TOKEN_PATTERN.findall(normalize_text(value).lower())


def _split_boundary(text: str, start: int, desired_end: int) -> int:
    if desired_end >= len(text):
        return len(text)
    lower_bound = start + max(1, (desired_end - start) // 2)
    for separator in ("\n\n", "\n", "。", "！", "？", ". ", "! ", "? ", " "):
        boundary = text.rfind(separator, lower_bound, desired_end)
        if boundary >= lower_bound:
            return boundary + len(separator)
    return desired_end


def split_text(
    value: str,
    *,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[TextChunk]:
    if chunk_size < 100:
        raise ValueError("chunk_size must be at least 100")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be between 0 and chunk_size")

    text = normalize_text(value)
    if not text:
        return []

    chunks: list[TextChunk] = []
    start = 0
    while start < len(text):
        end = _split_boundary(text, start, min(len(text), start + chunk_size))
        content = text[start:end].strip()
        if content:
            chunks.append(
                TextChunk(
                    index=len(chunks),
                    content=content,
                    token_count=estimate_token_count(content),
                    start_offset=start,
                    end_offset=end,
                )
            )
        if end >= len(text):
            break
        next_start = max(start + 1, end - chunk_overlap)
        while next_start < end and text[next_start].isspace():
            next_start += 1
        start = next_start
    return chunks
