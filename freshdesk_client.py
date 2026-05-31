"""
Freshdesk integration for the Support Triage Agent.

Replaces the mock data with the real system:
  READ  : fetch a ticket, look up the contact's plan
  ACT   : route a ticket to a group, add a private note, send a reply

SAFETY: DRY_RUN defaults to True. In dry-run, write actions (route/note/reply)
are LOGGED, not executed — so you can watch the agent's decisions against real
tickets before letting it touch them. Flip DRY_RUN=False only once you trust it.

You provide (in .env, never committed):
    FRESHDESK_DOMAIN   e.g. yourcompany.freshdesk.com
    FRESHDESK_API_KEY  your Freshdesk API key

NOTE: endpoints follow Freshdesk API v2. You know Freshdesk far better than this
code does — verify specifics against your account and adjust as needed.
"""

import os
import requests
from dotenv import load_dotenv

from config import PLAN_TIERS

load_dotenv()

DOMAIN = os.getenv("FRESHDESK_DOMAIN")          # e.g. "yourco.freshdesk.com"
API_KEY = os.getenv("FRESHDESK_API_KEY")
BASE = f"https://{DOMAIN}/api/v2" if DOMAIN else None

# Freshdesk uses the API key as the basic-auth username; password can be anything.
AUTH = (API_KEY, "X") if API_KEY else None

# SAFETY SWITCH — keep True until you've watched it behave on real tickets.
DRY_RUN = True

# Name of the Freshdesk contact custom field that stores the plan.
# (Adjust to whatever your account actually uses.)
PLAN_FIELD = "plan"


def _check_config():
    if not DOMAIN or not API_KEY:
        raise RuntimeError(
            "Freshdesk not configured. Add FRESHDESK_DOMAIN and "
            "FRESHDESK_API_KEY to your .env."
        )


# ---------------- READ ----------------

def fetch_ticket(ticket_id):
    """Fetch one ticket. Returns a dict shaped like the classifier expects:
    id, subject, body, requester_email."""
    _check_config()
    r = requests.get(f"{BASE}/tickets/{ticket_id}", auth=AUTH, timeout=20)
    r.raise_for_status()
    t = r.json()
    # Freshdesk returns description_text (plain) and a requester id; we also need
    # the requester's email, fetched below.
    email = _requester_email(t.get("requester_id"))
    return {
        "id": str(t["id"]),
        "subject": t.get("subject", ""),
        "body": t.get("description_text", "") or t.get("description", ""),
        "requester_email": email,
    }


def _requester_email(requester_id):
    if not requester_id:
        return ""
    r = requests.get(f"{BASE}/contacts/{requester_id}", auth=AUTH, timeout=20)
    if r.status_code != 200:
        return ""
    return (r.json().get("email") or "").lower()


def lookup_plan_freshdesk(email):
    """Look up a contact's plan from Freshdesk (replaces the mock CONTACTS dict).
    Returns (plan_name, plan_class); (None, None) if not found.

    IMPORTANT: Freshdesk's contact SEARCH/LIST endpoint returns a trimmed
    contact that often OMITS custom_fields. So we two-step it:
      1. search by email to get the contact id
      2. fetch the FULL contact by id -> that response includes custom_fields
    (This was the cause of a false plan_miss: search found the contact but
    without the 'plan' field, so the lookup came back empty.)
    """
    _check_config()
    # 1. find the contact id by email
    r = requests.get(f"{BASE}/contacts", params={"email": email}, auth=AUTH, timeout=20)
    if r.status_code != 200 or not r.json():
        return None, None
    contact_id = r.json()[0].get("id")
    if not contact_id:
        return None, None

    # 2. fetch the FULL contact by id (this includes custom_fields)
    r2 = requests.get(f"{BASE}/contacts/{contact_id}", auth=AUTH, timeout=20)
    if r2.status_code != 200:
        return None, None
    contact = r2.json()

    plan_name = (contact.get("custom_fields", {}) or {}).get(PLAN_FIELD)
    if not plan_name:
        return None, None
    plan_name = str(plan_name).lower()
    return plan_name, PLAN_TIERS.get(plan_name, "paid")


# ---------------- ACT (write — respects DRY_RUN) ----------------

def route_ticket(ticket_id, group_id):
    """Assign the ticket to a group (this is the 'routing' action)."""
    if DRY_RUN:
        print(f"   [DRY_RUN] would route ticket {ticket_id} -> group {group_id}")
        return {"dry_run": True}
    _check_config()
    r = requests.put(f"{BASE}/tickets/{ticket_id}", json={"group_id": group_id},
                     auth=AUTH, timeout=20)
    r.raise_for_status()
    return r.json()


def add_private_note(ticket_id, body):
    """Add an internal (private) note — used for the human handoff on escalation."""
    if DRY_RUN:
        print(f"   [DRY_RUN] would add private note to {ticket_id}: {body[:60]}...")
        return {"dry_run": True}
    _check_config()
    r = requests.post(f"{BASE}/tickets/{ticket_id}/notes",
                      json={"body": body, "private": True}, auth=AUTH, timeout=20)
    r.raise_for_status()
    return r.json()


def send_reply(ticket_id, body):
    """Send a public reply to the customer — used on auto_send. The real action."""
    if DRY_RUN:
        print(f"   [DRY_RUN] would REPLY to customer on {ticket_id}: {body[:60]}...")
        return {"dry_run": True}
    _check_config()
    r = requests.post(f"{BASE}/tickets/{ticket_id}/reply",
                      json={"body": body}, auth=AUTH, timeout=20)
    r.raise_for_status()
    return r.json()