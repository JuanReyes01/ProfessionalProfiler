import re
import nltk
from nltk import sent_tokenize

nltk.download("punkt")
nltk.download("punkt_tab")


def parse_degrees_from_content(results):
    CITATION_RE = re.compile(r"(?:\[\s*\d+\s*\]\s*)+")
    degree_pattern = re.compile(
        r"""
        (?:
            \bB\.A\.?\b
        | \bB\.S\.?\b
        | \bM\.A\.?\b
        | \bM\.S\.?\b
        | \bPh\.?D\.?\b
        | \bJ\.?D\.?\b
        )
        |
        (?:
            \bBachelor\ of\ (?:Arts|Science|Fine\ Arts|Philosophy|Laws)\b
        | \bMaster\ of\ (?:Arts|Science|Research|Philosophy|Education|Laws)\b
        | \bDoctor\ of\ (?:Philosophy|Science|Medicine|Engineering)\b
        | \bJuris\ Doctor\b
        )
    """,
        re.IGNORECASE | re.VERBOSE,
    )

    degree_sentences = []
    for hit in results:
        raw = hit["content"]
        clean = CITATION_RE.sub("", raw)
        clean = re.sub(r"\s+([,\.])", r"\1", clean)
        clean = re.sub(r"\s{2,}", " ", clean).strip()
        sentences = sent_tokenize(clean)
        degree_sentences.extend([s for s in sentences if degree_pattern.search(s)])
    return degree_sentences
