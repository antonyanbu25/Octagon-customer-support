# Routing configuration for the Support Triage Agent.
# Group IDs are placeholders — replace with the real Freshdesk group IDs
# you get from fetchGroups once you've created the groups in your FD account.

# Plan name (as stored on the contact) -> plan class used for routing.
PLAN_TIERS = {
    "trial": "trial",
    "growth": "paid",
    "pro": "paid",
    "enterprise": "paid",
}

# (plan_class, intent) -> team. This is the 2x2 from the design spec.
ROUTING = {
    ("trial", "commercial"): "Sales",
    ("trial", "technical"): "Technical Consulting",
    ("paid", "commercial"): "Customer Success",
    ("paid", "technical"): "Customer Support",
}

# Team -> Freshdesk group id. PLACEHOLDERS — swap for real IDs.
GROUP_IDS = {
    "Sales": 1001,
    "Technical Consulting": 1002,
    "Customer Success": 1003,
    "Customer Support": 1004,
    "Engineering": 1005,
}

# When the contact's plan can't be resolved, route here and flag for a human.
DEFAULT_TEAM = "Sales"

MODEL = "claude-sonnet-4-6"
