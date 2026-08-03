import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Matches numbered clause/article headers such as:
#   "20. Protection in respect of conviction for offences.—(1) No person..."
#   "43. Living wage, etc., for workers.—The State shall endeavour..."
# The title body must tolerate embedded newlines (titles routinely wrap onto
# a second line in extracted PDF text, e.g. "15. Prohibition of
# discrimination on grounds of religion, race, caste, \nsex or place of
# birth.—") and embedded periods (abbreviations like "etc."). A non-greedy
# any-character match naturally stops at the first ". " or ".—" it can.
#
# Amendment footnotes ("2. Subs. by the Constitution (Fiftieth Amendment)
# Act, 1984...") are numbered exactly like real headers but usually lack a
# nearby dash, so without the lookahead below the non-greedy search would
# run past them hunting for one and swallow the next real header whole.
_NUMBERED_TITLE_RE = re.compile(
    r"^\s*(\d{1,4}[A-Z]{0,2})\.\s+"
    r"(?!(?:Ins|Sub|Subs|Rep|Added|Omitted|Renumbered|Report|Cl|Cls|Art|Arts)\.?\s+by\b)"
    r"([A-Z].{3,220}?)\.\s*[-—]",
    re.MULTILINE | re.DOTALL,
)
# Matches explicit "Article 20", "Section 5", "Chapter III" style headers.
_KEYWORD_HEADER_RE = re.compile(
    r"(?m)^\s*(Article|Section|Clause|Chapter|Rule)\s+([0-9A-Z]{1,6})\b"
)

MIN_SECTIONS_FOR_STRUCTURE = 8
MAX_SECTION_CHARS = 2000
FALLBACK_CHUNK_SIZE = 800
FALLBACK_CHUNK_OVERLAP = 150


def _merge_pages(docs):
    """Join per-page documents into one string, tracking where each page starts."""
    parts = []
    page_starts = []
    pos = 0
    for d in docs:
        page_starts.append((pos, d.metadata.get("page", 0)))
        parts.append(d.page_content)
        pos += len(d.page_content) + 1
    return "\n".join(parts), page_starts


def _page_for_offset(page_starts, char_pos):
    page = page_starts[0][1]
    for start, pg in page_starts:
        if start > char_pos:
            break
        page = pg
    return page


def _find_section_headers(full_text):
    matches = list(_NUMBERED_TITLE_RE.finditer(full_text))
    if len(matches) >= MIN_SECTIONS_FOR_STRUCTURE:
        # "Article" is the conventional generic term for a bare numbered
        # clause ("14. Equality before law.—"). Users typically refer to
        # such provisions as "Article N" even though the chunk's own text
        # never spells that word out, so without this label neither BM25
        # nor embeddings can connect a query like "Article 14" to it.
        def label_fn(m):
            title = re.sub(r"\s+", " ", m.group(2)).strip()
            return f"Article {m.group(1)}: {title}"
        return matches, label_fn

    matches = list(_KEYWORD_HEADER_RE.finditer(full_text))
    def label_fn(m):
        return f"{m.group(1)} {m.group(2)}"
    return matches, label_fn


def _split_by_sections(full_text, page_starts, matches, label_fn, source):
    sub_splitter = RecursiveCharacterTextSplitter(
        chunk_size=MAX_SECTION_CHARS,
        chunk_overlap=FALLBACK_CHUNK_OVERLAP,
    )

    chunks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        section_text = full_text[start:end].strip()
        if not section_text:
            continue

        page = _page_for_offset(page_starts, start)
        label = label_fn(m)

        if len(section_text) <= MAX_SECTION_CHARS:
            chunks.append(Document(
                page_content=f"{label}\n\n{section_text}",
                metadata={"source": source, "page": page, "section": label},
            ))
        else:
            # Oversized section: split further but keep the header attached to
            # every piece so downstream retrieval never loses the section number.
            for piece in sub_splitter.split_text(section_text):
                chunks.append(Document(
                    page_content=f"{label}\n\n{piece}",
                    metadata={"source": source, "page": page, "section": label},
                ))

    return chunks


def split_documents_by_structure(docs):
    if not docs:
        return []

    full_text, page_starts = _merge_pages(docs)
    matches, label_fn = _find_section_headers(full_text)

    if len(matches) < MIN_SECTIONS_FOR_STRUCTURE:
        # No reliable numbered-section structure detected (e.g. prose documents,
        # manuals, papers) — fall back to plain fixed-size chunking.
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=FALLBACK_CHUNK_SIZE,
            chunk_overlap=FALLBACK_CHUNK_OVERLAP,
        )
        return splitter.split_documents(docs)

    source = docs[0].metadata.get("source", "")
    return _split_by_sections(full_text, page_starts, matches, label_fn, source)
