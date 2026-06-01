"""
The escalation gate: the DECISION layer of the agent.

It combines the signals already produced upstream into ONE decision:
  auto-send the drafted reply, OR stop and escalate to a human.

Governing principle (from the design): "when uncertain, escalate rather than
auto-send." The gate is deliberately biased toward escalation, because a missed
churn / wrong auto-reply is far costlier than an unnecessary human review.

Inputs it reads:
  classification  -> dict from classify_ticket() (intent, churn_risk, is_bug,
                     confidence, plan_miss, team, ...)
  draft           -> dict from draft_reply() (grounded, reply, ...) OR None for
                     commercial tickets where no reply is drafted.

The four+1 escalation conditions:
  1. churn_risk == True        -> a potential leaver; a human should handle it
  2. is_bug == True            -> route to engineering/human triage, don't auto-reply
  3. confidence == "low"       -> the classifier itself is unsure
  4. grounded == False         -> no trustworthy KB-based answer exists
  5. plan_miss == True         -> unknown contact; needs human attention
"""


def decide(classification, draft=None, qa_result=None):
    """Decide whether to auto-send or escalate. Returns a decision dict.

    decision:
      action  : "auto_send" | "escalate"
      reasons : list of the conditions that triggered escalation ([] if auto_send)
      reply   : the drafted reply text if auto_send, else None
      team    : the team to route to (unchanged from classification)
    """
    reasons = []

    # --- collect every escalation trigger (we check ALL, not just the first,
    #     so the handoff note can tell a human everything that's going on) ---
    if classification.get("churn_risk"):
        reasons.append("churn_risk")
    if classification.get("is_bug"):
        reasons.append("is_bug")
    if classification.get("confidence") == "low":
        reasons.append("low_confidence")
    if classification.get("plan_miss"):
        reasons.append("plan_miss")

    # grounding only applies when a reply was actually attempted (technical path).
    # Commercial tickets pass draft=None and are not auto-replied anyway.
    if draft is not None and not draft.get("grounded"):
        reasons.append("ungrounded_reply")

    # commercial tickets are never auto-replied by this agent — they go to a
    # human team (Sales / Customer Success) to handle the relationship.
    if classification.get("intent") == "commercial":
        reasons.append("commercial_needs_human")

    # QA check (optional second opinion): if an independent LLM-as-judge scored
    # the drafted reply and it FAILED, don't auto-send -> hand to a human.
    if qa_result is not None and not qa_result.get("passed", True):
        reasons.append("qa_failed")

    # --- the decision ---
    if reasons:
        return {
            "action": "escalate",
            "reasons": reasons,
            "reply": None,
            "team": classification.get("team"),
        }

    # nothing fired AND it's a grounded technical reply -> safe to auto-send
    return {
        "action": "auto_send",
        "reasons": [],
        "reply": draft.get("reply") if draft else None,
        "team": classification.get("team"),
    }
