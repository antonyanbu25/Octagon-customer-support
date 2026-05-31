"""
Eval harness for the Support Triage Agent.

Scores TWO layers:
  A) CLASSIFICATION  - the 7 classifier fields (plan_class, intent, team,
                       churn_risk, is_bug, plan_miss, confidence)
  B) ESCALATION      - the END-TO-END decision: did the agent correctly
                       auto_send vs escalate, and for the right reasons?

Layer B is what actually matters in production: the classifier can be slightly
off on a flag, but as long as the final send/escalate call is right (and biased
toward escalation when uncertain), the system behaves safely.

Plus a TP/FP/FN/TN confusion matrix for churn (the highest-stakes signal).

USAGE:
    python eval_harness.py
"""

from eval_set import EVAL_SET
from classifier import classify_ticket
from triage_agent import handle_ticket


# ---- classifier fields scored individually ----
SCORED_FIELDS = [
    "plan_class", "intent", "team",
    "churn_risk", "is_bug", "plan_miss", "confidence",
]

# tickets we expect retrieval to NOT ground (vague / not in KB). Judgment input;
# adjust as the KB or eval set changes.
EXPECTED_UNGROUNDED_IDS = {"7"}


def expected_escalation(case):
    """Derive the expected action + reasons from a case's labels, using the same
    rules the gate applies. Returns (action, sorted_reasons)."""
    e = case["expected"]
    reasons = []
    if e.get("churn_risk"):          reasons.append("churn_risk")
    if e.get("is_bug"):              reasons.append("is_bug")
    if e.get("confidence") == "low": reasons.append("low_confidence")
    if e.get("plan_miss"):           reasons.append("plan_miss")
    if e.get("intent") == "technical" and case["input"]["id"] in EXPECTED_UNGROUNDED_IDS:
        reasons.append("ungrounded_reply")
    if e.get("intent") == "commercial":
        reasons.append("commercial_needs_human")
    action = "escalate" if reasons else "auto_send"
    return action, sorted(reasons)


def churn_outcome(expected_churn, actual_churn):
    if actual_churn and expected_churn:       return "TP"
    if actual_churn and not expected_churn:   return "FP"
    if not actual_churn and expected_churn:   return "FN"
    return "TN"


def run():
    total = len(EVAL_SET)

    # layer A counters
    field_passed = {f: 0 for f in SCORED_FIELDS}
    churn_counts = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
    field_failures = []

    # layer B counters
    action_correct = 0      # got auto_send vs escalate right
    reasons_exact = 0       # got the EXACT reason set right (stricter)
    escalation_failures = []

    for case in EVAL_SET:
        tid = case["input"]["id"]

        # --- layer A: classification (one API call) ---
        cls = classify_ticket(case["input"])
        for f in SCORED_FIELDS:
            if cls.get(f) == case["expected"].get(f):
                field_passed[f] += 1
            else:
                field_failures.append({
                    "id": tid, "field": f,
                    "expected": case["expected"].get(f), "actual": cls.get(f),
                })
        churn_counts[churn_outcome(case["expected"]["churn_risk"], cls.get("churn_risk"))] += 1

        # --- layer B: end-to-end escalation decision (full pipeline) ---
        result = handle_ticket(case["input"])
        exp_action, exp_reasons = expected_escalation(case)
        got_action = result["action"]
        got_reasons = sorted(result["reasons"])

        if got_action == exp_action:
            action_correct += 1
        else:
            escalation_failures.append({
                "id": tid, "kind": "action",
                "expected": exp_action, "actual": got_action,
                "exp_reasons": exp_reasons, "got_reasons": got_reasons,
            })

        if got_reasons == exp_reasons:
            reasons_exact += 1
        elif got_action == exp_action:
            # action right but reasons differ -> a softer mismatch worth noting
            escalation_failures.append({
                "id": tid, "kind": "reasons",
                "expected": exp_action, "actual": got_action,
                "exp_reasons": exp_reasons, "got_reasons": got_reasons,
            })

    # ===== REPORT =====
    print(f"\n========== A) CLASSIFICATION ({total} cases) ==========")
    for f in SCORED_FIELDS:
        pct = 100 * field_passed[f] / total
        line = f"{f:<12} {field_passed[f]:>2}/{total}  ({pct:>3.0f}%)"
        if f == "churn_risk":
            line += f"   [FN: {churn_counts['FN']}, FP: {churn_counts['FP']}]"
        print(line)

    print("\n--- churn breakdown ---")
    print(f"TP (caught real churn):       {churn_counts['TP']}")
    print(f"FN (MISSED churn - costly):   {churn_counts['FN']}")
    print(f"FP (false alarm - cheap):     {churn_counts['FP']}")
    print(f"TN (correctly left alone):    {churn_counts['TN']}")

    print(f"\n========== B) ESCALATION DECISION ({total} cases) ==========")
    print(f"Action correct (auto_send vs escalate): {action_correct}/{total}  "
          f"({100*action_correct/total:.0f}%)   <- the headline metric")
    print(f"Exact reasons match (stricter):         {reasons_exact}/{total}  "
          f"({100*reasons_exact/total:.0f}%)")

    print(f"\n========== FAILURES ==========")
    if not field_failures and not escalation_failures:
        print("None - clean across classification and escalation.")
    if field_failures:
        print(f"\nClassification ({len(field_failures)}):")
        for f in field_failures:
            print(f"  [{f['id']:<3}] {f['field']:<12} expected={f['expected']!r:<14} got={f['actual']!r}")
    if escalation_failures:
        print(f"\nEscalation ({len(escalation_failures)}):")
        for f in escalation_failures:
            tag = "ACTION WRONG" if f["kind"] == "action" else "reasons differ"
            print(f"  [{f['id']:<3}] {tag}: expected {f['expected']}/{f['exp_reasons']} "
                  f"got {f['actual']}/{f['got_reasons']}")
    print()


if __name__ == "__main__":
    run()
