"""
Classifier for the Support Triage Agent (Week 10 component).

Pipeline for one ticket:
  1. lookup_plan()      -> the contact's plan, from the (mock) CRM
  2. classify_intent()  -> commercial vs technical, via the Claude API,
                           plus churn_risk / is_bug / confidence for later use
  3. route()            -> combine plan class + intent into a team + group id

classify_ticket() runs all three and returns one result dict.
"""

import os
import json
import re

from dotenv import load_dotenv
from anthropic import Anthropic

from config import PLAN_TIERS, ROUTING, GROUP_IDS, DEFAULT_TEAM, MODEL
from sample_data import CONTACTS

load_dotenv()
client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment


INTENT_SYSTEM = """You classify SaaS support tickets by INTENT, for routing.

Choose exactly one intent:
- "commercial": about money, the account, or the business relationship — pricing,
  offers, negotiation, demos, trial extensions, renewals, invoices, billing
  questions, business reviews, or cancellation.
- "technical": about making the product work — configuration, setup, automating
  workflows, integrations, errors, bugs, or "the app isn't working".

Also assess:
- confidence: "high", "medium", or "low". Use "low" when the ticket is vague or
  could plausibly be either intent.
- churn_risk: true if the customer threatens to cancel or downgrade, asks about
  leaving, names a competitor, or expresses strong dissatisfaction.
- is_bug: true if the customer reports something in the product erroring or broken.

Respond with ONLY a JSON object and nothing else:
{"intent": "commercial|technical", "confidence": "high|medium|low", "churn_risk": true|false, "is_bug": true|false, "reasoning": "one short sentence"}"""


def lookup_plan(email):
    """Return (plan_name, plan_class). Both None if the contact isn't found."""
    plan_name = CONTACTS.get(email.lower())
    if plan_name is None:
        return None, None
    return plan_name, PLAN_TIERS.get(plan_name, "paid")


def _parse_json(text):
    """Parse the model's JSON, tolerating any stray surrounding text."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def classify_intent(ticket):
    """Ask Claude for the intent (and the extra signals) for one ticket."""
    user_msg = f"Subject: {ticket['subject']}\n\nBody: {ticket['body']}"
    resp = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=INTENT_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    return _parse_json(resp.content[0].text.strip())


def route(plan_class, intent):
    """Map (plan_class, intent) to a team + group id. Falls back if plan is unknown."""
    team = ROUTING.get((plan_class, intent))
    if team is None:
        return DEFAULT_TEAM, GROUP_IDS[DEFAULT_TEAM], True  # plan-miss -> needs human
    return team, GROUP_IDS[team], False


def classify_ticket(ticket, plan_lookup=lookup_plan):
    """Full classification for one ticket. Returns a result dict."""
    plan_name, plan_class = plan_lookup(ticket["requester_email"])
    signals = classify_intent(ticket)
    intent = signals["intent"]

    # If plan is unknown, route to default and force a human flag.
    if plan_class is None:
        team, group_id, plan_miss = DEFAULT_TEAM, GROUP_IDS[DEFAULT_TEAM], True
    else:
        team, group_id, plan_miss = route(plan_class, intent)

    return {
        "ticket_id": ticket["id"],
        "email": ticket["requester_email"],
        "plan": plan_name or "UNKNOWN",
        "plan_class": plan_class or "unknown",
        "intent": intent,
        "team": team,
        "group_id": group_id,
        "confidence": signals.get("confidence"),
        "churn_risk": signals.get("churn_risk"),
        "is_bug": signals.get("is_bug"),
        "plan_miss": plan_miss,
        "reasoning": signals.get("reasoning"),
    }
