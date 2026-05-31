# Mock data for local testing — no Freshdesk connection needed yet.
#
# CONTACTS stands in for the plan lookup. In production this is replaced by a
# Freshdesk custom field read via fetchContact / fetchCompany.
#
# Plan names must be keys in config.PLAN_TIERS:
#   "trial" -> trial ; "growth"/"pro"/"enterprise" -> paid
# (The eval checks plan_class, so any paid-tier name gives plan_class="paid".)

CONTACTS = {
    # --- original demo contacts (used by EVAL_SET cases 1-7, 9, 10) ---
    "ravi@acmestartup.io": "trial",      # case 1
    "deepak@hooli.com": "trial",         # case 2
    "priya@globex.com": "enterprise",    # cases 3 and 10
    "sam@initech.co": "pro",             # case 4
    "lena@umbrella.dev": "growth",       # case 5
    "mara@piedpiper.com": "enterprise",  # case 6
    "tom@wonka.io": "pro",               # case 7
    "anita@stark.com": "growth",         # case 9
    # "jordan@newlead.com" intentionally ABSENT -> plan-miss (case 8)

    # --- contacts for the added hard cases ---
    "paid.soft@acmeco.com": "enterprise",  # H1 soft churn
    "trial.tech@acmeco.com": "trial",      # H2 frustration-not-churn
    "paid.happy@acmeco.com": "growth",     # H3 competitor-but-happy
    "paid.upsell@acmeco.com": "pro",       # H4 upsell
    "paid.multi@acmeco.com": "enterprise", # H5 multi-topic
    # "unknown.person@nowhere.com" intentionally ABSENT -> plan-miss (H6)
}

# NOTE: The labeled evaluation set now lives in eval_set.py (EVAL_SET), which is
# the single source of truth. The SAMPLE_TICKETS list below is kept only for the
# original quick-demo runner (test_classifier.py) and is unlabeled. New work
# should go in EVAL_SET.
SAMPLE_TICKETS = [
    {
        "id": 1,
        "requester_email": "ravi@acmestartup.io",
        "subject": "Can we extend our trial?",
        "body": "We're still evaluating and need two more weeks. Also, what does annual pricing look like for the Pro plan?",
    },
    {
        "id": 2,
        "requester_email": "deepak@hooli.com",
        "subject": "Setting up an automation rule",
        "body": "During my trial I'm trying to auto-assign tickets based on subject keywords. Where do I configure that?",
    },
    {
        "id": 3,
        "requester_email": "priya@globex.com",
        "subject": "Quarterly business review",
        "body": "Can we get our QBR on the calendar for next month? Want to walk through adoption and our renewal.",
    },
    {
        "id": 4,
        "requester_email": "sam@initech.co",
        "subject": "Workflow automation stopped firing",
        "body": "Our ticket-routing automation worked last week but hasn't triggered on any new tickets since Monday.",
    },
    {
        "id": 5,
        "requester_email": "lena@umbrella.dev",
        "subject": "Export throws a 500 error",
        "body": "Every time I try to export the contacts report I get a 500 error page. Tried three browsers. Looks broken.",
    },
    {
        "id": 6,
        "requester_email": "mara@piedpiper.com",
        "subject": "Reconsidering our subscription",
        "body": "Honestly the price keeps going up and a competitor is quoting us half. We're seriously thinking of switching.",
    },
    {
        "id": 7,
        "requester_email": "tom@wonka.io",
        "subject": "It's not working",
        "body": "Hi, it stopped working. Can you help?",
    },
    {
        "id": 8,
        "requester_email": "jordan@newlead.com",
        "subject": "Interested in a demo",
        "body": "Saw your product on a comparison site. Could someone show us how it handles multi-brand support?",
    },
    {
        "id": 9,
        "requester_email": "anita@stark.com",
        "subject": "How do I configure SSO?",
        "body": "We're on Growth and want to set up SAML SSO with our identity provider. Is there a guide?",
    },
    {
        "id": 10,
        "requester_email": "priya@globex.com",
        "subject": "Custom invoice request",
        "body": "Our finance team needs the invoice to include our PO number and a separate line for taxes. Can that be changed?",
    },
]