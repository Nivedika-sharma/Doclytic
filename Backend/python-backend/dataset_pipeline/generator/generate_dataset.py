import csv
import random
import sys
from collections import Counter
from pathlib import Path

from noise import add_ocr_noise
from templates import generate_department_document

PY_BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(PY_BACKEND_DIR) not in sys.path:
    sys.path.append(str(PY_BACKEND_DIR))

from config.routing_rules import ROUTING_RULES  # noqa: E402

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "output" / "dataset.csv"
TARGET_PER_LABEL = 250
TARGET_DEPARTMENTS = ["HR", "Finance", "Legal", "Operations", "Procurement"]
HARD_NEGATIVE_PROB = 0.3

LENGTH_WEIGHTS = [
    ("short", 0.2),
    ("medium", 0.45),
    ("full", 0.35),
]

CROSS_DEPARTMENT_TERMS = {
    "Procurement": [
        "invoice",
        "payment advice",
        "payment confirmation",
        "tax invoice",
    ],
    "HR": [
        "vendor invoice",
        "payment receipt",
        "purchase order",
        "gst filing",
    ],
    "Finance": [
        "offer letter",
        "employee onboarding",
        "non-disclosure agreement",
        "resume",
    ],
    "Legal": [
        "delivery challan",
        "goods receipt note",
        "payment voucher",
        "purchase order",
    ],
    "Operations": [
        "salary payment",
        "invoice pending",
        "contract clause",
        "vendor payment",
    ],
}

TASK_WRAPPER = (
    "DOCUMENT CLASSIFICATION TASK: Classify the document by department and document type.\n\n"
)


def read_label_counts(path: Path) -> Counter:
    counts = Counter()
    if not path.exists() or path.stat().st_size == 0:
        return counts

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = (row.get("label") or "").strip().lower()
            if label:
                counts[label] += 1
    return counts


def append_rows(path: Path, rows):
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def _choose_length() -> str:
    roll = random.random()
    cumulative = 0.0
    for length, weight in LENGTH_WEIGHTS:
        cumulative += weight
        if roll <= cumulative:
            return length
    return LENGTH_WEIGHTS[-1][0]


def _inject_hard_negative(text: str, department: str) -> str:
    if random.random() > HARD_NEGATIVE_PROB:
        return text

    terms = CROSS_DEPARTMENT_TERMS.get(department)
    if not terms:
        return text

    snippet = ", ".join(random.sample(terms, k=min(2, len(terms))))
    line = f"Note: Related terms include {snippet}."
    lines = text.splitlines()
    insert_at = random.randint(1, max(1, len(lines)))
    lines.insert(insert_at, line)
    return "\n".join(lines)


def _wrap_task(text: str) -> str:
    return f"{TASK_WRAPPER}{text}"


def generate_rows(doc_type: str, department: str, full_label: str, missing_count: int):
    rows = []
    for _ in range(missing_count):
        length = _choose_length()
        text = generate_department_document(label=doc_type, department=department, length=length)
        text = _inject_hard_negative(text, department)
        text = _wrap_task(text)
        text = add_ocr_noise(text, noise_probability=0.6)
        rows.append({"text": text, "label": full_label})
    return rows


def main():
    counts = read_label_counts(OUTPUT_PATH)
    total_appended = 0

    for department in TARGET_DEPARTMENTS:
        labels = ROUTING_RULES.get(department, [])
        for raw_label in labels:
            doc_type = raw_label.strip().lower()
            label = f"{department.lower()}__{doc_type}"
            current = counts.get(label, 0)
            missing = max(0, TARGET_PER_LABEL - current)
            new_rows = generate_rows(doc_type, department, label, missing)
            if new_rows:
                append_rows(OUTPUT_PATH, new_rows)
                counts[label] += len(new_rows)
                total_appended += len(new_rows)
            print(
                f"{department}/{label}: existing={current}, "
                f"appended={len(new_rows)}, total={counts[label]}"
            )

    print(f"Done. Appended {total_appended} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
