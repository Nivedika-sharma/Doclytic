import re
from collections import Counter
from typing import Dict, Iterable, List, Optional, Tuple


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

_DOMAIN_KEYWORDS = {
    "hr": ["resume", "candidate", "nda", "employment", "offer", "cv", "employee"],
    "finance": ["invoice", "gst", "payment", "bank", "tax", "balance sheet", "payroll"],
    "legal": ["agreement", "contract", "clause", "legal", "nda", "privacy policy", "notice"],
    "procurement": ["purchase order", "vendor", "rfq", "quotation", "tender", "supply"],
    "operations": ["operations", "logistics", "maintenance", "incident", "report"],
    "it": ["api", "bug", "security", "system design", "access", "architecture"],
    "admin": ["memo", "meeting", "travel", "facility", "office"],
}

_STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "document", "department",
    "type", "classify", "task", "report", "form", "note", "details", "summary",
    "date", "name", "candidate", "company", "policy", "agreement", "terms",
}


def clean_text(text: str) -> str:
    if not text:
        return ""
    lowered = text.lower().translate(_OCR_TRANSLATION)
    lowered = lowered.replace("rn", "m").replace("vv", "w")
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


def _score_domains(text: str) -> Dict[str, int]:
    if not text:
        return {}
    scores: Dict[str, int] = {}
    for domain, markers in _DOMAIN_KEYWORDS.items():
        score = 0
        for marker in markers:
            if marker in text:
                score += 1
        if score:
            scores[domain] = score
    return scores


def detect_department(text: str, keywords: str = "") -> str:
    corpus = f"{text} {keywords}".strip()
    if not corpus:
        return ""
    scores = _score_domains(corpus)
    if not scores:
        return ""
    top = max(scores.items(), key=lambda item: item[1])[0]
    return {
        "hr": "HR",
        "finance": "Finance",
        "legal": "Legal",
        "procurement": "Procurement",
        "operations": "Operations",
        "it": "IT",
        "admin": "Admin",
    }.get(top, "")


def _prune_cross_domain_terms(text: str) -> str:
    scores = _score_domains(text)
    if len(scores) <= 1:
        return text
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_domain, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0
    if top_score < 2 or top_score <= second_score:
        return text
    pruned = text
    for domain, markers in _DOMAIN_KEYWORDS.items():
        if domain == top_domain:
            continue
        for marker in markers:
            pruned = pruned.replace(marker, " ")
    return re.sub(r"\s+", " ", pruned).strip()


def build_keyword_dict(
    texts: Iterable[str],
    labels: Iterable[str],
    top_k: int = 12,
    min_count: int = 3,
) -> Dict[str, List[str]]:
    buckets: Dict[str, Counter] = {}
    for text, label in zip(texts, labels):
        clean = clean_text(text)
        tokens = re.findall(r"[a-z]{3,}", clean)
        if not tokens:
            continue
        bucket = buckets.setdefault(label, Counter())
        for tok in tokens:
            if tok in _STOPWORDS:
                continue
            bucket[tok] += 1

    keyword_dict: Dict[str, List[str]] = {}
    for label, counter in buckets.items():
        common = [w for w, c in counter.most_common(top_k) if c >= min_count]
        keyword_dict[label] = common
    return keyword_dict


def extract_keywords_from_dict(
    text: str,
    keyword_dict: Optional[Dict[str, List[str]]] = None,
    max_keywords: int = 10,
) -> Tuple[str, List[str]]:
    if not text or not keyword_dict:
        return "", []
    matches: List[str] = []
    for label, words in keyword_dict.items():
        for w in words:
            if w in text and w not in matches:
                matches.append(w)
                if len(matches) >= max_keywords:
                    break
        if len(matches) >= max_keywords:
            break
    return " ".join(matches), matches


def build_structured_input(text: str, keywords: str, department: str) -> str:
    content = (text or "").strip()
    truncated = content[:450]
    dept_line = f"Department Hint: {department}" if department else "Department Hint: "
    keywords_line = f"Keywords: {keywords}".strip()
    return (
        f"{keywords_line}\n"
        f"{dept_line}\n\n"
        f"Content:\n"
        f"{truncated}"
    ).strip()


def preprocess_for_model(
    text: str,
    filename: str = "",
    keyword_dict: Optional[Dict[str, List[str]]] = None,
) -> str:
    combined = f"{filename}\n{text}" if filename else text
    cleaned = clean_text(combined)
    filtered = filter_noise(cleaned)
    filtered = _prune_cross_domain_terms(filtered)
    base_keywords = extract_keywords(filtered)
    dict_keywords, _ = extract_keywords_from_dict(filtered, keyword_dict)
    keywords = " ".join([k for k in [dict_keywords, base_keywords] if k]).strip()
    department = detect_department(filtered, keywords)
    return build_structured_input(filtered, keywords, department)
