"""
Eval set for the Support Triage Agent classifier — consolidated source of truth.

Merges the strongest original sample tickets (now with expected labels) with the
additional hard cases, so there's ONE labeled set, no invented-email duplication.

HARNESS USAGE:
    from classifier import classify_ticket
    for case in EVAL_SET:
        result = classify_ticket(case["input"])      # input keys match classifier
        compare result against case["expected"]

INPUT keys match what classify_ticket() reads: id, subject, body, requester_email

EXPECTED fields match the classifier OUTPUT:
    plan_class : "trial" | "paid" | "unknown"
    intent     : "commercial" | "technical"        (lowercase)
    team       : "Sales" | "Technical Consulting" | "Customer Success" |
                 "Customer Support"                 (exact config.ROUTING strings)
    churn_risk : True | False
    is_bug     : True | False
    plan_miss  : True | False
    confidence : "high" | "medium" | "low"          (lowercase)

All requester_emails are registered in sample_data.CONTACTS with the intended
plan, EXCEPT the two deliberate plan-miss cases (jordan@newlead.com,
unknown.person@nowhere.com) which are intentionally absent.

Some intent/churn labels are judgment calls (flagged in "tests"). When the
classifier disagrees, decide case-by-case whether the model is wrong or your
label is — that disagreement is the useful part of an eval.
"""

EVAL_SET = [

    # ===== BASELINE — the 2x2 cells, clear-cut =====

    {   # trial + commercial -> Sales (mild multi-topic: extension + pricing, both commercial)
        "input": {
            "id": "1",
            "requester_email": "ravi@acmestartup.io",
            "subject": "Can we extend our trial?",
            "body": "We're still evaluating and need two more weeks. Also, what "
                    "does annual pricing look like for the Pro plan?",
        },
        "expected": {
            "plan_class": "trial", "intent": "commercial", "team": "Sales",
            "churn_risk": False, "is_bug": False, "plan_miss": False, "confidence": "high",
        },
        "tests": "Trial extension + pricing -> commercial, Sales. Both topics commercial.",
    },

    {   # trial + technical -> Technical Consulting
        "input": {
            "id": "2",
            "requester_email": "deepak@hooli.com",
            "subject": "Setting up an automation rule",
            "body": "During my trial I'm trying to auto-assign tickets based on "
                    "subject keywords. Where do I configure that?",
        },
        "expected": {
            "plan_class": "trial", "intent": "technical", "team": "Technical Consulting",
            "churn_risk": False, "is_bug": False, "plan_miss": False, "confidence": "high",
        },
        "tests": "Configuration how-to on a trial -> technical, Technical Consulting.",
    },

    {   # paid + commercial -> Customer Success
        "input": {
            "id": "3",
            "requester_email": "priya@globex.com",
            "subject": "Quarterly business review",
            "body": "Can we get our QBR on the calendar for next month? Want to "
                    "walk through adoption and our renewal.",
        },
        "expected": {
            "plan_class": "paid", "intent": "commercial", "team": "Customer Success",
            "churn_risk": False, "is_bug": False, "plan_miss": False, "confidence": "high",
        },
        "tests": "QBR + renewal -> commercial, Customer Success. 'Renewal' is NOT churn "
                 "-> guards against a churn false positive.",
    },

    {   # paid + technical -> Customer Support (regression = bug)
        "input": {
            "id": "4",
            "requester_email": "sam@initech.co",
            "subject": "Workflow automation stopped firing",
            "body": "Our ticket-routing automation worked last week but hasn't "
                    "triggered on any new tickets since Monday.",
        },
        "expected": {
            "plan_class": "paid", "intent": "technical", "team": "Customer Support",
            "churn_risk": False, "is_bug": True, "plan_miss": False, "confidence": "high",
        },
        "tests": "Regression -> technical, Customer Support, is_bug=True (debatable vs "
                 "config; labeled bug since it previously worked).",
    },

    # ===== BUG =====

    {   # explicit error -> is_bug True
        "input": {
            "id": "5",
            "requester_email": "lena@umbrella.dev",
            "subject": "Export throws a 500 error",
            "body": "Every time I try to export the contacts report I get a 500 "
                    "error page. Tried three browsers. Looks broken.",
        },
        "expected": {
            "plan_class": "paid", "intent": "technical", "team": "Customer Support",
            "churn_risk": False, "is_bug": True, "plan_miss": False, "confidence": "high",
        },
        "tests": "Clear defect (500 error) -> technical, is_bug=True.",
    },

    # ===== CHURN — explicit (TP) and soft (false-negative trap) =====

    {   # explicit churn
        "input": {
            "id": "6",
            "requester_email": "mara@piedpiper.com",
            "subject": "Reconsidering our subscription",
            "body": "Honestly the price keeps going up and a competitor is quoting "
                    "us half. We're seriously thinking of switching.",
        },
        "expected": {
            "plan_class": "paid", "intent": "commercial", "team": "Customer Success",
            "churn_risk": True, "is_bug": False, "plan_miss": False, "confidence": "high",
        },
        "tests": "Explicit churn (competitor + switching intent). The obvious churn TP.",
    },

    {   # SOFT churn -> most valuable case
        "input": {
            "id": "H1",
            "requester_email": "paid.soft@acmeco.com",
            "subject": "Quick question on our renewal",
            "body": "Our renewal is coming up next month. We're reviewing tooling "
                    "spend this quarter and honestly aren't sure we're getting "
                    "enough value. Can someone walk us through what we're paying for?",
        },
        "expected": {
            "plan_class": "paid", "intent": "commercial", "team": "Customer Success",
            "churn_risk": True, "is_bug": False, "plan_miss": False, "confidence": "high",
        },
        "tests": "SOFT churn -- value doubt + spend review near renewal. THE hard case: "
                 "catches implicit churn (avoids a costly false negative).",
    },

    # ===== CHURN FALSE-POSITIVE GUARDS =====

    {   # frustration but NOT churn
        "input": {
            "id": "H2",
            "requester_email": "trial.tech@acmeco.com",
            "subject": "Parent-child ticketing not working",
            "body": "I'm struggling to create a child ticket. I followed the "
                    "solution article but it isn't working.",
        },
        "expected": {
            "plan_class": "trial", "intent": "technical", "team": "Technical Consulting",
            "churn_risk": False, "is_bug": False, "plan_miss": False, "confidence": "high",
        },
        "tests": "Technical frustration on a trial -> technical. NOT churn -> guards "
                 "against treating annoyance as churn.",
    },

    {   # competitor named but HAPPY -> churn False
        "input": {
            "id": "H3",
            "requester_email": "paid.happy@acmeco.com",
            "subject": "Migrating our macros from Zendesk",
            "body": "We moved over from Zendesk a few months ago and we're really "
                    "happy. Quick question -- how do I bulk-import our old canned "
                    "responses into the product?",
        },
        "expected": {
            "plan_class": "paid", "intent": "technical", "team": "Customer Support",
            "churn_risk": False, "is_bug": False, "plan_miss": False, "confidence": "high",
        },
        "tests": "Competitor named but customer is happy + how-to. Tests classifier does "
                 "NOT over-flag churn on a competitor keyword.",
    },

    # ===== AMBIGUITY / LOW CONFIDENCE =====

    {   # genuinely vague -> low confidence
        "input": {
            "id": "7",
            "requester_email": "tom@wonka.io",
            "subject": "It's not working",
            "body": "Hi, it stopped working. Can you help?",
        },
        "expected": {
            "plan_class": "paid", "intent": "technical", "team": "Customer Support",
            "churn_risk": False, "is_bug": False, "plan_miss": False, "confidence": "low",
        },
        "tests": "Deliberately vague -> should flag LOW confidence rather than guess. "
                 "intent/is_bug debatable, which is the point.",
    },

    {   # SSO on Growth -> debatable technical vs commercial
        "input": {
            "id": "9",
            "requester_email": "anita@stark.com",
            "subject": "How do I configure SSO?",
            "body": "We're on Growth and want to set up SAML SSO with our identity "
                    "provider. Is there a guide?",
        },
        "expected": {
            "plan_class": "paid", "intent": "technical", "team": "Customer Support",
            "churn_risk": False, "is_bug": False, "plan_miss": False, "confidence": "high",
        },
        "tests": "DEBATABLE: config how-to (technical) BUT if SSO needs an Enterprise "
                 "upgrade it's really commercial/upsell. Tests where plan-feature domain "
                 "knowledge would change routing.",
    },

    # ===== BILLING + UPSELL (commercial sub-types) =====

    {   # invoice/billing
        "input": {
            "id": "10",
            "requester_email": "priya@globex.com",
            "subject": "Custom invoice request",
            "body": "Our finance team needs the invoice to include our PO number "
                    "and a separate line for taxes. Can that be changed?",
        },
        "expected": {
            "plan_class": "paid", "intent": "commercial", "team": "Customer Success",
            "churn_risk": False, "is_bug": False, "plan_miss": False, "confidence": "high",
        },
        "tests": "Billing/invoice request -> commercial, Customer Success.",
    },

    {   # upsell interest
        "input": {
            "id": "H4",
            "requester_email": "paid.upsell@acmeco.com",
            "subject": "Need multi-product capability",
            "body": "Looks like I need to move to a higher plan to use the "
                    "multi-product capability. What are the next steps?",
        },
        "expected": {
            "plan_class": "paid", "intent": "commercial", "team": "Customer Success",
            "churn_risk": False, "is_bug": False, "plan_miss": False, "confidence": "high",
        },
        "tests": "Upgrade/upsell interest -> commercial, Customer Success.",
    },

    # ===== MULTI-TOPIC =====

    {   # technical blocker + pricing ask
        "input": {
            "id": "H5",
            "requester_email": "paid.multi@acmeco.com",
            "subject": "Integration help + pricing for more seats",
            "body": "Two things: our Slack integration keeps disconnecting, and "
                    "separately, what would it cost to add 10 more agent seats?",
        },
        "expected": {
            "plan_class": "paid", "intent": "technical", "team": "Customer Support",
            "churn_risk": False, "is_bug": True, "plan_miss": False, "confidence": "low",
        },
        "tests": "Two intents (technical + commercial). Tests primary-intent selection. "
                 "Assumes blocker-first; align the prompt to whatever rule you choose.",
    },

    # ===== PLAN-MISS — commercial + technical variants =====

    {   # plan-miss + commercial
        "input": {
            "id": "8",
            "requester_email": "jordan@newlead.com",
            "subject": "Interested in a demo",
            "body": "Saw your product on a comparison site. Could someone show us "
                    "how it handles multi-brand support?",
        },
        "expected": {
            "plan_class": "unknown", "intent": "commercial", "team": "Sales",
            "churn_risk": False, "is_bug": False, "plan_miss": True, "confidence": "high",
        },
        "tests": "Unknown contact (prospect) -> plan_miss=True, default team. Intent "
                 "still detectable (commercial/demo).",
    },

    {   # plan-miss + technical
        "input": {
            "id": "H6",
            "requester_email": "unknown.person@nowhere.com",
            "subject": "Forgot my login email and password",
            "body": "I forgot the email and password for my account and can't log "
                    "in. Need help getting back in.",
        },
        "expected": {
            "plan_class": "unknown", "intent": "technical", "team": "Sales",
            "churn_risk": False, "is_bug": False, "plan_miss": True, "confidence": "high",
        },
        "tests": "Unknown contact + technical -> plan_miss=True. Documents that default "
                 "team is Sales even for technical; the plan_miss flag (not the team) "
                 "signals 'needs a human'.",
    },
]