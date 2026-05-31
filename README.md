# Support Triage Agent — OCTAGON

**Objective:** Set up a customer support process for "OCTAGON", a fictitious SaaS
organisation, using the latest AI concepts.

**Concepts used:** RAG · Human in the loop · Guardrails · MCP tool usage ·
Intent-based classification · Integration with Freshdesk

OCTAGON runs support across four teams, split two ways — by **who the customer is**
(trial or paid) and by **what they need** (commercial or technical). Doing that
triage by hand is slow and inconsistent, and it's the first thing to break at volume.
This agent does the triage automatically and only pulls in a human when judgement or
a financial commitment is actually at stake. The agent is the reasoning core: it
decides which tools to call and whether a human is needed, ticket by ticket — no
brittle keyword rules to maintain.

---

## Workflow

- Ticket arrives (Freshdesk webhook).
- Look up the contact's plan from the Freshdesk contact/company record → trial or paid.
- Reason about intent → commercial or technical.
- Map plan × intent to the right ticket type + group, and update the Freshdesk ticket.
- Branch on intent:
  - **Commercial** (Sales / Customer Success): route and assign only — no auto-reply. A human picks it up. Stop.
  - **Technical** (Customer Support / Technical Consulting): retrieve from the KB (RAG) and draft a grounded reply.
- Run the drafted reply through the escalation gate (below). If any condition is true, add a private note and leave it for a human.
- If no escalation condition is met, send the reply.

Governing principle: **when uncertain, escalate rather than auto-send.**

### Routing model

Routing is a 2×2 of plan against intent, with Engineering as a downstream queue.

| | Trial plan | Paid plan (Growth / Pro / Enterprise) |
|---|---|---|
| **Commercial** — pricing, offers, demos, trial extension, renewals, business reviews | Sales | Customer Success |
| **Technical** — configuration, workflow automation, integrations, app not working, bugs | Technical Consulting | Customer Support |

**Engineering** isn't a triage destination — it receives bugs handed up from Customer
Support or Technical Consulting when a code fix is needed.

---

## Integration: Freshdesk

Reads and actions on the ticket go through the Freshdesk MCP server —
`fetchTicket` and `fetchContact`/`fetchCompany` to read, `updateTicket` to set the
type and route to a group, `createTicketNote` for the human handoff, and
`replyTicket` on the clean send path.

## RAG

A small set of KB articles is converted into a vector database, enabling the LLM to
search and fetch the right information when responding to customer queries. This is a
retrieval layer built *alongside* the MCP — Freshdesk's solution-article tools fetch
by folder or ID, not by free-text query, so semantic search is handled here.

## Human in the loop

The agent checks all four conditions before sending. Any one of them stops the
auto-reply and hands the ticket to a human via a private note.

- **Churn / cancellation risk** — the customer threatens to cancel or downgrade, asks about leaving, names a competitor, or is strongly dissatisfied.
- **Ungrounded reply** — the draft can't be supported by a retrieved KB article.
- **Low confidence / ambiguity** — the agent is unsure, or the request is unclear.
- **Bug report** — additionally assigned to the Engineering group.

A false negative on churn (a cancellation signal that slips through to an auto-reply)
is far costlier than a false positive, so the gate is deliberately biased toward
escalating when unsure.

---

## What's built now

The **classifier** — the front half of the workflow — is implemented and testable
locally without a Freshdesk connection.

| File | Role |
|---|---|
| `classifier.py` | Plan lookup → intent classification (Claude API) → routing. Entry point: `classify_ticket()`. |
| `config.py` | Plan tiers, the 2×2 routing matrix, Freshdesk group-ID placeholders. |
| `sample_data.py` | Mock plan lookup + 10 sample tickets covering every matrix cell and each edge case. |
| `test_classifier.py` | Runs all 10 tickets and prints a results table. |

The classifier already extracts `churn_risk`, `is_bug`, and `confidence` in the same
call that determines intent — so the escalation gate gets those signals without a
second model call.

### Run it

```bash
pip install -r requirements.txt
cp .env.example .env        # add your ANTHROPIC_API_KEY
python test_classifier.py
```

---

## Roadmap

- [x] **Classifier** — plan lookup, intent classification, team routing
- [ ] **Freshdesk integration** — read tickets and write type/group via the Freshdesk MCP
- [ ] **RAG** — index OCTAGON's KB articles into a vector store and retrieve top matches per ticket
- [ ] **Reply drafting** — draft technical replies grounded in retrieved KB context
- [ ] **Escalation gate** — wire the four conditions to `createTicketNote` + the Engineering handoff
- [ ] **Send path** — `replyTicket` on the clean, no-escalation path
- [ ] **Guardrails** — plan-miss fallback, loop prevention (ignore the agent's own updates), and an eval set over the sample tickets
