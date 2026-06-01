# Octagon — Support Triage Agent

An agentic AI system that triages customer-support tickets: it classifies the ticket, routes it to the right team, retrieves a grounded answer from a knowledge base, drafts a reply, and decides whether to **auto-send or escalate to a human**.

It is built around one governing principle:

> **When uncertain, escalate rather than auto-send.** A wrong automated reply to a customer is far costlier than an unnecessary handoff to a human.

**[▶ Try the live demo](https://octagon-customer-support-sfx3g8u3frxwlcxu5cy4tp.streamlit.app)** — paste a ticket and watch the agent work. (Free-tier app; first load may take ~30s to wake.)

---

## Why this exists

Most "AI for customer support" demos happily auto-answer everything. Real support doesn't work that way — the hard part isn't generating a reply, it's knowing *when not to*. This project encodes that judgment: a pipeline that is deliberately biased toward escalation, measured end-to-end, and built so the model never sends an answer it can't ground.

---

## How it works

The agent runs a fixed pipeline. Each step is plain Python my code controls (not model-orchestrated), which keeps the flow predictable, evaluable, and safe.

```
Ticket
  │
  ▼
Classify  ──►  plan (trial/paid), intent (technical/commercial),
  │            churn risk, is-bug, confidence
  ▼
Route     ──►  2×2 routing to the right team
  │
  ├─ commercial ───────────────►  escalate to a human team (no auto-reply)
  │
  ▼ technical
Retrieve  ──►  semantic search over the KB (RAG)
  │
  ▼
Draft     ──►  grounded reply (refuses if KB doesn't cover the question)
  │
  ▼
QA review ──►  independent LLM-as-judge scores the reply (optional layer)
  │
  ▼
Decide    ──►  AUTO-SEND  or  ESCALATE (+ reasons)
```

### Routing (2×2)
| | Trial | Paid |
|---|---|---|
| **Commercial** | Sales | Customer Success |
| **Technical** | Technical Consulting | Customer Support |

If the plan can't be found, the ticket defaults to Sales and is flagged `plan_miss` (a reason to escalate).

### Escalation triggers
The agent escalates instead of auto-sending if **any** of these fire: churn risk, the ticket is a bug, low confidence, plan lookup missed, the reply couldn't be grounded, the ticket is commercial, or the QA layer failed the reply. The gate collects *all* reasons, not just the first — so the handoff note explains exactly why.

---

## What makes it more than a wrapper

**Two independent measurement layers.** The system is graded two different ways:
- An **eval harness** that scores *decisions* (route/escalate) against a labeled set.
- An **LLM-as-judge QA agent** that scores *reply quality* (groundedness, relevance, tone, safety), requiring **every** dimension to pass — so one bad dimension (e.g. an ungrounded claim) fails the reply even if the tone is perfect.

In the demo, the same ticket that auto-sends with QA off gets **escalated with QA on** when the judge catches that the reply invented steps not in the knowledge base. The drafter's own grounding check missed it; the independent judge caught it. That second layer is the point.

**Grounded replies, not confident hallucinations.** The reply drafter uses two-layer grounding: a retrieval-distance threshold, plus a prompt that returns `INSUFFICIENT_CONTEXT` if the KB doesn't actually cover the question. If it can't ground an answer, it escalates rather than guess.

**Injectable plan lookup.** The same classifier runs against mock data in tests/evals and a live help desk in production, by injecting the plan-lookup function — so tests stay fast and offline while production uses real data.

**Direct API by design, not MCP.** The agent calls the help-desk REST API directly rather than using MCP. This is deliberate: a fixed, safety-biased pipeline should have its flow owned by code (so the escalation gate always runs and the system stays deterministic and testable). MCP suits open-ended, model-orchestrated copilots — a different problem.

---

## Evaluation

The eval harness scores two layers across **16 labeled cases** covering the full 2×2, bugs, explicit and soft churn, churn false-positive guards, low-confidence/ambiguous tickets, multi-topic tickets, and plan-miss cases:

- **Classification** — each of the 7 classifier fields (plan, intent, team, churn risk, is-bug, plan-miss, confidence).
- **End-to-end escalation** — did the agent make the right auto-send vs escalate call, for the right reasons?
- **Churn confusion matrix** — TP/FP/FN/TN on the highest-stakes signal.

```
python eval_harness.py
```

> Note on the numbers: a high score on a self-authored eval set means the system is internally consistent, not that it's bulletproof. The next step is hardening the eval with adversarial and out-of-distribution cases — which is exactly how I'd treat it in production.

---

## Stack

- **Claude API** (`claude-sonnet-4-6`) — classification, reply drafting, QA judging
- **ChromaDB** — local semantic KB index (RAG)
- **Streamlit** — the live demo app
- **Freshdesk REST API** — live help-desk integration (ticket fetch, routing, private notes; runs in dry-run by default)

---

## Run it locally

```bash
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

python eval_harness.py        # run the evals
streamlit run app.py          # launch the demo
```

The demo runs entirely on sample data — no live help desk needed.

---

## Repo map

| File | What it does |
|---|---|
| `classifier.py` | One Claude call → intent, churn, is-bug, confidence (+ injectable plan lookup) |
| `kb_index.py` | ChromaDB semantic index + `retrieve()` |
| `reply_drafter.py` | Retrieve → two-layer grounded reply (or `INSUFFICIENT_CONTEXT`) |
| `escalation_gate.py` | Collects all escalation triggers → auto-send / escalate decision |
| `qa_agent.py` | LLM-as-judge scoring reply quality on 4 dimensions |
| `triage_agent.py` | Orchestrator: runs the full pipeline for one ticket |
| `eval_set.py` / `eval_harness.py` | Labeled cases + two-layer scoring |
| `freshdesk_client.py` / `run_on_freshdesk.py` | Live help-desk integration (dry-run by default) |
| `app.py` | Streamlit demo |

---

*Built as a hands-on exploration of agentic AI for customer experience — tool use, RAG, evaluation, and human-in-the-loop escalation.*
