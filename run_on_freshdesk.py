"""
End-to-end: pull a real Freshdesk ticket, run the agent brain, execute the
decision (respecting DRY_RUN in freshdesk_client).

  fetch ticket -> handle_ticket() (classify/RAG/gate) -> act:
     auto_send -> send_reply
     escalate  -> route_ticket + add_private_note (with the reasons)

USAGE:
    # add FRESHDESK_DOMAIN + FRESHDESK_API_KEY to .env first
    python run_on_freshdesk.py <ticket_id>
"""

import sys
from config import GROUP_IDS
from triage_agent import handle_ticket
import freshdesk_client as fd


def process(ticket_id):
    # 1. READ the real ticket
    ticket = fd.fetch_ticket(ticket_id)
    print(f"\nTicket {ticket_id}: {ticket['subject']!r}  from {ticket['requester_email']}")

    # 2. THINK — run the validated brain
    result = handle_ticket(ticket, plan_lookup=fd.lookup_plan_freshdesk)
    print(f"   decision: {result['action'].upper()} -> {result['team']}")
    if result["reasons"]:
        print(f"   reasons: {', '.join(result['reasons'])}")

    # 3. ACT (dry-run by default — see freshdesk_client.DRY_RUN)
    group_id = GROUP_IDS.get(result["team"])
    if result["action"] == "auto_send" and result["reply"]:
        fd.send_reply(ticket_id, result["reply"])
    else:
        # escalate: route to the team + leave a private handoff note for the human
        note = (f"[Triage agent] Escalating. Reasons: "
                f"{', '.join(result['reasons']) or 'n/a'}. "
                f"Suggested team: {result['team']}.")
        fd.route_ticket(ticket_id, group_id)
        fd.add_private_note(ticket_id, note)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_on_freshdesk.py <ticket_id>")
        sys.exit(1)
    process(sys.argv[1])
