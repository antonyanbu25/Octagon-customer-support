"""
handle_ticket(): the orchestrator that runs the whole pipeline for one ticket.

  classify -> (if technical) draft a grounded reply -> gate decides -> result.

Commercial tickets skip drafting (the agent doesn't auto-handle the business
relationship) and always go to a human team via the gate.
"""

from classifier import classify_ticket
from reply_drafter import draft_reply
from escalation_gate import decide


def handle_ticket(ticket):
    """Full triage for one ticket. Returns everything needed to act + to log."""
    # 1. classify + route + extract signals
    classification = classify_ticket(ticket)

    # 2. only draft a reply on the technical path (commercial -> human)
    draft = None
    if classification.get("intent") == "technical":
        draft = draft_reply(ticket)

    # 3. gate decides: auto_send or escalate
    decision = decide(classification, draft)

    # 4. bundle a single result (also the basis for a log/handoff note later)
    return {
        "ticket_id": classification.get("ticket_id"),
        "team": decision["team"],
        "action": decision["action"],
        "reasons": decision["reasons"],
        "reply": decision["reply"],
        # carry the signals through for logging / observability later
        "intent": classification.get("intent"),
        "plan_class": classification.get("plan_class"),
        "churn_risk": classification.get("churn_risk"),
        "is_bug": classification.get("is_bug"),
        "confidence": classification.get("confidence"),
        "plan_miss": classification.get("plan_miss"),
        "grounded": draft.get("grounded") if draft else None,
    }


if __name__ == "__main__":
    from sample_data import SAMPLE_TICKETS
    for t in SAMPLE_TICKETS[:5]:
        r = handle_ticket(t)
        print(f"\n[{r['ticket_id']}] {r['action'].upper()} -> {r['team']}")
        if r["reasons"]:
            print(f"   escalation reasons: {', '.join(r['reasons'])}")
        if r["reply"]:
            print(f"   reply: {r['reply'][:80]}...")
