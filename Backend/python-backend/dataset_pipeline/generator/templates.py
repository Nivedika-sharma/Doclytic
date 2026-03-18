import random

from metrics_data import cities, legal_entities, person_names, vendor_names

SECTION_DROP_PROB = 0.2

HEADER_SYNONYMS = {
    "summary": ["Summary", "Overview", "Brief"],
    "details": ["Details", "Key Details", "Record Details"],
    "terms": ["Commercial Terms", "Terms", "Payment Terms"],
    "logistics": ["Logistics", "Shipment Details", "Delivery Notes"],
    "confidentiality": ["Confidentiality", "Privacy", "NDA Notes"],
    "metrics": ["Metrics", "KPIs", "Performance Metrics"],
    "actions": ["Action", "Next Steps", "Follow-up"],
    "scope": ["Scope", "Purpose", "Agreement Scope"],
    "compliance": ["Compliance", "Regulatory Notes", "Audit Notes"],
    "employment": ["Employment Details", "Role Details", "Appointment Terms"],
}


def _humanize(label: str) -> str:
    return label.replace("_", " ").title()


def _rand_date() -> str:
    return f"{random.randint(1, 28):02d}-{random.randint(1, 12):02d}-{random.randint(2023, 2026)}"


def _rand_gstin() -> str:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    alnum = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return (
        f"{random.randint(10, 99)}"
        f"{''.join(random.choice(letters) for _ in range(5))}"
        f"{random.randint(1000, 9999)}"
        f"{random.choice(letters)}"
        f"{random.choice(alnum)}"
        f"Z"
        f"{random.choice(alnum)}"
    )


def _apply_section_variability(sections):
    kept = [section for section in sections if random.random() > SECTION_DROP_PROB]
    if not kept:
        kept = [random.choice(sections)]
    random.shuffle(kept)
    return kept


def _render_sections(sections):
    lines = []
    for section in sections:
        header = random.choice(section["headers"])
        lines.append(f"{header}:")
        lines.extend(section["lines"])
        lines.append("")
    return lines


def _limit_lines(lines, length: str) -> str:
    if length == "full":
        return "\n".join(lines).strip()

    compact = [line for line in lines if line.strip()]
    if length == "short":
        target = random.randint(1, 2)
    else:
        target = random.randint(5, 8)

    return "\n".join(compact[:target]).strip()


def _build_document(title: str, department: str, meta_lines, sections, length: str) -> str:
    sections = _apply_section_variability(sections)
    lines = [title, f"Department: {department}"]
    lines.extend(meta_lines)
    lines.append("")
    lines.extend(_render_sections(sections))
    return _limit_lines(lines, length)


def _hr_text(label: str, length: str) -> str:
    candidate = random.choice(person_names)
    sections = [
        {
            "headers": HEADER_SYNONYMS["summary"],
            "lines": ["Candidate profile reviewed for role fit and policy compliance."],
        },
        {
            "headers": HEADER_SYNONYMS["employment"],
            "lines": ["Offer/appointment terms, compensation band and reporting manager are included."],
        },
        {
            "headers": HEADER_SYNONYMS["confidentiality"],
            "lines": ["This HR file contains personal information and NDA related clauses."],
        },
    ]
    return _build_document(
        title=f"HR DOCUMENT: {_humanize(label)}",
        department="HR",
        meta_lines=[f"Candidate Name: {candidate}", f"Document Date: {_rand_date()}"],
        sections=sections,
        length=length,
    )


def _legal_text(label: str, length: str) -> str:
    party_a = random.choice(legal_entities)
    party_b = random.choice([x for x in legal_entities if x != party_a])
    sections = [
        {
            "headers": HEADER_SYNONYMS["scope"],
            "lines": ["This agreement defines legal obligations and enforceable terms."],
        },
        {
            "headers": HEADER_SYNONYMS["confidentiality"],
            "lines": ["No disclosure of confidential information without written consent."],
        },
        {
            "headers": HEADER_SYNONYMS["details"],
            "lines": ["Dispute resolution and jurisdiction clauses are specified."],
        },
    ]
    return _build_document(
        title=f"LEGAL DOCUMENT: {_humanize(label)}",
        department="Legal",
        meta_lines=[f"Agreement Date: {_rand_date()}", f"Parties: {party_a} and {party_b}"],
        sections=sections,
        length=length,
    )


def _finance_text(label: str, length: str) -> str:
    vendor = random.choice(vendor_names)
    qty = random.randint(1, 20)
    unit_price = random.randint(2000, 65000)
    total = qty * unit_price
    sections = [
        {
            "headers": HEADER_SYNONYMS["details"],
            "lines": [
                f"Line Item Quantity: {qty}",
                f"Unit Price: INR {unit_price:,}",
                f"Total Amount: INR {total:,}",
            ],
        },
        {
            "headers": HEADER_SYNONYMS["compliance"],
            "lines": ["Tax and accounting entry validated for finance review."],
        },
    ]
    return _build_document(
        title=f"FINANCE DOCUMENT: {_humanize(label)}",
        department="Finance",
        meta_lines=[f"Vendor: {vendor}", f"Date: {_rand_date()}", f"GSTIN: {_rand_gstin()}"],
        sections=sections,
        length=length,
    )


def _operations_text(label: str, length: str) -> str:
    sections = [
        {
            "headers": HEADER_SYNONYMS["summary"],
            "lines": ["Operations performance and throughput trends recorded for this period."],
        },
        {
            "headers": HEADER_SYNONYMS["metrics"],
            "lines": [
                f"Open incidents: {random.randint(0, 25)}",
                f"Closed tasks: {random.randint(40, 220)}",
                f"Inventory variance: {random.randint(0, 8)}%",
            ],
        },
        {
            "headers": HEADER_SYNONYMS["actions"],
            "lines": ["Escalations and follow-up tasks assigned to relevant teams."],
        },
    ]
    return _build_document(
        title=f"OPERATIONS DOCUMENT: {_humanize(label)}",
        department="Operations",
        meta_lines=[f"Location: {random.choice(cities)}", f"Reporting Date: {_rand_date()}"],
        sections=sections,
        length=length,
    )


def _procurement_text(label: str, length: str) -> str:
    vendor = random.choice(vendor_names)
    sections = [
        {
            "headers": HEADER_SYNONYMS["details"],
            "lines": ["Material request, quotation references and delivery timelines are listed."],
        },
        {
            "headers": HEADER_SYNONYMS["terms"],
            "lines": ["Payment milestones, penalties and acceptance conditions are documented."],
        },
        {
            "headers": HEADER_SYNONYMS["logistics"],
            "lines": ["Shipment and goods receipt tracking IDs attached for closure."],
        },
    ]
    return _build_document(
        title=f"PROCUREMENT DOCUMENT: {_humanize(label)}",
        department="Procurement",
        meta_lines=[f"Vendor: {vendor}", f"Request Date: {_rand_date()}"],
        sections=sections,
        length=length,
    )


def _generic_text(label: str, department: str, length: str) -> str:
    sections = [
        {
            "headers": HEADER_SYNONYMS["details"],
            "lines": ["This file contains department-specific records and process details."],
        }
    ]
    return _build_document(
        title=f"DOCUMENT TYPE: {_humanize(label)}",
        department=department,
        meta_lines=[f"Generated On: {_rand_date()}"],
        sections=sections,
        length=length,
    )


def generate_department_document(label: str, department: str, length: str = "full") -> str:
    if department == "HR":
        return _hr_text(label, length)
    if department == "Legal":
        return _legal_text(label, length)
    if department == "Finance":
        return _finance_text(label, length)
    if department == "Operations":
        return _operations_text(label, length)
    if department == "Procurement":
        return _procurement_text(label, length)
    return _generic_text(label, department, length)
