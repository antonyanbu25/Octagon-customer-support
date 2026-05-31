"""
draft_reply(): the 'AG' in RAG — retrieve, then generate a grounded reply.

For a technical ticket it:
  1. retrieves the most relevant KB article(s)               (from kb_index)
  2. checks the retrieval is close enough to be trustworthy  (distance threshold)
  3. asks Claude to answer USING ONLY those articles         (grounding guardrail)
  4. returns the reply + a 'grounded' flag for the escalation gate

GROUNDING IS CHECKED TWICE (belt and suspenders):
  - retrieval side: if even the best article is too far (high distance), there's
    nothing relevant to answer from -> grounded=False, don't draft.
  - generation side: the prompt tells Claude to reply 'INSUFFICIENT_CONTEXT' if
    the articles don't actually cover the question -> grounded=False.
Either failure means "a human should handle this", which the escalation gate
(Week 3) will act on.
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic

from config import MODEL
from kb_index import retrieve

load_dotenv()
client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment


DRAFT_SYSTEM = """You are a customer support agent for OCTAGON, a SaaS help-desk product.

Answer the customer's question using ONLY the knowledge base article(s) provided.
Rules:
- Do NOT invent steps, menu paths, URLs, settings, or facts that are not in the articles.
- If the provided articles do not actually contain the answer, reply with EXACTLY
  the single word: INSUFFICIENT_CONTEXT
- Otherwise, write a concise, friendly reply (a short paragraph or a few steps).
- Do not mention the knowledge base or that you were given articles."""


def draft_reply(ticket, n_articles=2, distance_threshold=1.0):
    """Draft a grounded reply for a technical ticket.

    distance_threshold: max retrieval distance we'll trust. Above it, we treat
    the KB as not covering this ticket. (Starting value from the smoke-test
    distances; should be tuned against the eval set, not guessed forever.)

    Returns a dict:
      reply         : the drafted text, or None if not grounded
      grounded      : True/False
      reason        : "ok" | "no_relevant_article" | "model_could_not_ground"
      best_article  : title of the closest article (for logging/handoff notes)
      best_distance : how close the closest article was
    """
    query = f"{ticket['subject']} {ticket['body']}"
    hits = retrieve(query, n_results=n_articles)
    best = hits[0]

    # ---- grounding check #1: retrieval side ----
    if best["distance"] > distance_threshold:
        return {
            "reply": None,
            "grounded": False,
            "reason": "no_relevant_article",
            "best_article": best["title"],
            "best_distance": round(best["distance"], 3),
        }

    # build the augmented prompt: the retrieved article(s) + the ticket
    context = "\n\n".join(f"Article: {h['title']}\n{h['content']}" for h in hits)
    user_msg = (
        f"Knowledge base articles:\n{context}\n\n"
        f"Customer ticket:\nSubject: {ticket['subject']}\nBody: {ticket['body']}\n\n"
        f"Draft a reply to the customer."
    )

    resp = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=DRAFT_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = resp.content[0].text.strip()

    # ---- grounding check #2: generation side ----
    if text == "INSUFFICIENT_CONTEXT":
        return {
            "reply": None,
            "grounded": False,
            "reason": "model_could_not_ground",
            "best_article": best["title"],
            "best_distance": round(best["distance"], 3),
        }

    return {
        "reply": text,
        "grounded": True,
        "reason": "ok",
        "best_article": best["title"],
        "best_distance": round(best["distance"], 3),
    }


if __name__ == "__main__":
    # quick manual test on a few technical tickets
    samples = [
        {"subject": "Setting up an automation rule",
         "body": "I'm trying to auto-assign tickets based on subject keywords. Where do I configure that?"},
        {"subject": "How do I configure SSO?",
         "body": "We want to set up SAML SSO with our identity provider. Is there a guide?"},
        {"subject": "It's not working",
         "body": "Hi, it stopped working. Can you help?"},   # expect: not grounded
    ]
    for t in samples:
        print(f"\n=== {t['subject']} ===")
        out = draft_reply(t)
        print(f"grounded={out['grounded']}  reason={out['reason']}  "
              f"article={out['best_article']!r}  distance={out['best_distance']}")
        if out["reply"]:
            print(out["reply"])
