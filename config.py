# Routing configuration for the Support Triage Agent.
# GROUP_IDS are the REAL Freshdesk group IDs from the connected account.

# Plan name (as stored on the contact's "plan" custom field) -> plan class.
# The Freshdesk "plan" dropdown only has two choices: trial / paid,
# so the field already gives the plan class directly. The extra paid-tier
# names are harmless fallbacks in case the field is expanded later.
PLAN_TIERS = {
    "trial": "trial",
    "paid": "paid",
    "growth": "paid",
    "pro": "paid",
    "enterprise": "paid",
}

# (plan_class, intent) -> team. The 2x2 from the design spec.
ROUTING = {
    ("trial", "commercial"): "Sales",
    ("trial", "technical"): "Technical Consulting",
    ("paid", "commercial"): "Customer Success",
    ("paid", "technical"): "Customer Support",
}

# Team -> REAL Freshdesk group id (from the connected account).
GROUP_IDS = {
    "Sales": 68000009797,
    "Technical Consulting": 68000009801,
    "Customer Success": 68000009796,
    "Customer Support": 68000009800,
    "Engineering": 68000009802,
}

# When the contact's plan can't be resolved, route here and flag for a human.
DEFAULT_TEAM = "Sales"

MODEL = "claude-sonnet-4-6"