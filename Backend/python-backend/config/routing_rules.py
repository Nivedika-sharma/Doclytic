# ROUTING_RULES = {
#     # Map classifier labels -> sidebar department names
#     "invoice": "Finance",
#     "contract": "Legal",

#     "resume,raise letter,complaint letter, appointment letter, "
#     "relieving letter, offer letter, experience certificate, non-disclosure agreement, code of condict, salary slips,employee handbook acknowledgement, company policies": "HR",


#     "report": "Operations",
#     # Common procurement-like labels
#     "purchase_order": "Procurement",
#     "quotation": "Procurement",
#     "rfq": "Procurement",
# }

ROUTING_RULES = {

    "Finance": [
        "invoice",
        "payroll_statement",
        "financial_statement",
        "tax_return",
        "expense_report",
    ],

    "HR": [
        "cv",
        "offer_letter",
        "employee_contract",
        "termination_letter",
        "nda",
    ],

    "Legal": [
        "contract",
        "service_agreement",
        "legal_notice",
        "privacy_policy",
        "nda",
    ],

    "Procurement": [
        "purchase_order",
        "quotation",
        "rfq",
        "tender_document",
        "vendor_contract",
    ],

    "Operations": [
        "report",
        "operations_report",
        "incident_report",
        "maintenance_report",
        "logistics_report",
    ],

    "IT": [
        "system_design_document",
        "api_documentation",
        "bug_report",
        "security_policy",
        "access_request",
    ],

    "Admin": [
        "internal_memo",
        "meeting_minutes",
        "facility_request",
        "travel_request",
        "asset_allocation_form",
    ],
}
