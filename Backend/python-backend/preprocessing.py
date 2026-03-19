import re
from typing import Iterable, List, Optional


_OCR_TRANSLATION = str.maketrans({
    "0": "o",
    "1": "l",
    "5": "s",
    "@": "a",
})

_NOISE_KEYWORDS = [
    "gst",
    "invoice",
    "payment",
    "vendor",
    "purchase order",
]

_KEYWORD_TERMS = [
    "resume",
    "candidate",
    "nda",
    "employment",
    "offer",
]


def clean_text(text: str) -> str:
    if not text:
        return ""
    lowered = text.lower().translate(_OCR_TRANSLATION)
    normalized = lowered.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[^a-z0-9\n\s]", " ", normalized)

    lines: List[str] = []
    for line in normalized.split("\n"):
        compact = re.sub(r"\s+", " ", line).strip()
        lines.append(compact)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned).strip()
    return cleaned


def filter_noise(text: str, keywords: Optional[Iterable[str]] = None) -> str:
    if not text:
        return ""
    needle_list = [k.lower() for k in (keywords or _NOISE_KEYWORDS)]
    lines = text.split("\n")
    kept = [line for line in lines if not any(k in line for k in needle_list)]
    if not kept:
        return text
    return "\n".join(kept).strip()


def extract_keywords(text: str, terms: Optional[Iterable[str]] = None) -> str:
    if not text:
        return ""
    keyword_terms = [t.lower() for t in (terms or _KEYWORD_TERMS)]
    found: List[str] = []
    for term in keyword_terms:
        if term in text and term not in found:
            found.append(term)
    return " ".join(found)


def _detect_department(text: str, keywords: str) -> str:
    corpus = f"{text} {keywords}".strip()
    if not corpus:
        return ""

    rules = [
        ("HR", ["resume", "candidate", "employment", "offer", "cv"]),
        ("Legal", ["nda", "contract", "agreement", "legal", "privacy policy"]),
        ("Finance", ["invoice", "gst", "payment", "bank", "tax", "balance sheet"]),
        ("Procurement", ["purchase order", "vendor", "rfq", "quotation", "tender"]),
        ("Operations", ["operations", "logistics", "maintenance", "incident"]),
        ("IT", ["api", "bug", "security", "system design"]),
        ("Admin", ["memo", "meeting", "travel", "facility"]),
    ]

    for department, markers in rules:
        if any(marker in corpus for marker in markers):
            return department
    return ""


def build_structured_input(text: str, keywords: str, department: str) -> str:
    content = (text or "").strip()
    truncated = content[:450]
    dept_line = f"Department: {department}" if department else "Department: "
    keywords_line = f"Document Type Clues: {keywords}".strip()
    return (
        f"{keywords_line}\n"
        f"{dept_line}\n\n"
        f"Content:\n"
        f"{truncated}"
    ).strip()


def preprocess_for_model(text: str, filename: str = "") -> str:
    combined = f"{filename}\n{text}" if filename else text
    cleaned = clean_text(combined)
    filtered = filter_noise(cleaned)
    keywords = extract_keywords(filtered)
    department = _detect_department(filtered, keywords)
    return build_structured_input(filtered, keywords, department)

