"""
Run the 10 sample tickets through the classifier and print the results.

Usage:
    pip install -r requirements.txt
    cp .env.example .env   # then put your ANTHROPIC_API_KEY in it
    python test_classifier.py
"""

from classifier import classify_ticket
from sample_data import SAMPLE_TICKETS


def flags(r):
    out = []
    if r["plan_miss"]:
        out.append("PLAN-MISS")
    if r["churn_risk"]:
        out.append("CHURN")
    if r["is_bug"]:
        out.append("BUG")
    if r["confidence"] == "low":
        out.append("LOW-CONF")
    return ",".join(out) if out else "-"


def main():
    print(f"\n{'ID':<3} {'PLAN':<11} {'INTENT':<11} {'TEAM':<22} {'CONF':<7} FLAGS")
    print("-" * 80)
    for ticket in SAMPLE_TICKETS:
        r = classify_ticket(ticket)
        print(
            f"{r['ticket_id']:<3} {r['plan']:<11} {r['intent']:<11} "
            f"{r['team']:<22} {str(r['confidence']):<7} {flags(r)}"
        )
        print(f"    -> {r['reasoning']}")
    print()


if __name__ == "__main__":
    main()
