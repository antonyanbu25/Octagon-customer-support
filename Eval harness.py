"""
Eval harness for the Support Triage Agent classifier.

WHAT IT DOES (the process we walked through):
  1. Load EVAL_SET (the answer key) and classify_ticket (the thing being tested)
  2. Run every test case through the classifier
  3. Compare each field of the classifier's answer against the expected answer
  4. Tally per-field accuracy
  5. Record every failure (which ticket, which field, expected vs actual)
  6. Print a scorecard + a failure list

  Plus a special TP / FP / FN / TN breakdown for churn_risk, because for churn
  a false negative (missed churn) is far costlier than a false positive.

USAGE:
    pip install -r requirements.txt
    cp .env.example .env     # add your ANTHROPIC_API_KEY
    python eval_harness.py
"""

from eval_set import EVAL_SET
from classifier import classify_ticket


# The fields we score. Each one is compared independently so we can see WHICH
# kind of decision the classifier is good or bad at (not just overall pass/fail).
SCORED_FIELDS = [
    "plan_class",
    "intent",
    "team",
    "churn_risk",
    "is_bug",
    "plan_miss",
    "confidence",
]


def evaluate(case, result):
    """
    Compare one classifier result against one expected answer.
    Returns a dict: {field_name: True/False} for each scored field.
    """
    expected = case["expected"]
    field_results = {}
    for field in SCORED_FIELDS:
        # Did the classifier's value for this field match what we expected?
        field_results[field] = (result.get(field) == expected.get(field))
    return field_results


def churn_outcome(expected_churn, actual_churn):
    """
    Classify the churn prediction into one of the four outcomes.
      - expected_churn = the truth (our label)
      - actual_churn   = what the classifier predicted
    Returns "TP", "FP", "FN", or "TN".
    """
    if actual_churn and expected_churn:
        return "TP"   # predicted churn, and it was churn        (correct catch)
    if actual_churn and not expected_churn:
        return "FP"   # predicted churn, but it wasn't            (false alarm)
    if not actual_churn and expected_churn:
        return "FN"   # predicted no-churn, but it WAS churn      (a miss - costly!)
    return "TN"       # predicted no-churn, and it wasn't churn   (correct pass)


def run():
    # --- counters ---
    # per-field: how many passed out of how many total
    passed = {field: 0 for field in SCORED_FIELDS}
    total = len(EVAL_SET)

    # churn confusion-matrix counts
    churn_counts = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}

    # collected failures, to print at the end
    failures = []

    # --- the loop: one pass per test case ---
    for case in EVAL_SET:
        ticket_id = case["input"]["id"]

        # run the classifier on this ticket
        result = classify_ticket(case["input"])

        # compare every scored field
        field_results = evaluate(case, result)
        for field, ok in field_results.items():
            if ok:
                passed[field] += 1
            else:
                # record the failure with expected vs actual, for study later
                failures.append({
                    "id": ticket_id,
                    "field": field,
                    "expected": case["expected"].get(field),
                    "actual": result.get(field),
                })

        # special churn outcome tracking (TP/FP/FN/TN)
        outcome = churn_outcome(
            expected_churn=case["expected"]["churn_risk"],
            actual_churn=result.get("churn_risk"),
        )
        churn_counts[outcome] += 1

    # --- print the scorecard ---
    print(f"\n=== EVAL RESULTS ({total} cases) ===")
    for field in SCORED_FIELDS:
        pct = 100 * passed[field] / total
        line = f"{field:<12} {passed[field]:>2}/{total}  ({pct:>3.0f}%)"
        # annotate churn with its FN/FP, since those are what matter for churn
        if field == "churn_risk":
            line += f"   [FN: {churn_counts['FN']}, FP: {churn_counts['FP']}]"
        print(line)

    # --- churn confusion matrix (the high-stakes signal) ---
    print("\n=== CHURN BREAKDOWN ===")
    print(f"True Positives  (caught real churn):     {churn_counts['TP']}")
    print(f"False Negatives (MISSED churn - costly): {churn_counts['FN']}")
    print(f"False Positives (false alarm - cheap):   {churn_counts['FP']}")
    print(f"True Negatives  (correctly left alone):  {churn_counts['TN']}")

    # --- the failure list (the part you actually learn from) ---
    print(f"\n=== FAILURES ({len(failures)}) ===")
    if not failures:
        print("None - every field matched on every case.")
    else:
        for f in failures:
            print(f"[{f['id']:<3}] {f['field']:<12} expected={f['expected']!r:<18} got={f['actual']!r}")
    print()


if __name__ == "__main__":
    run()