"""
QA agent: an independent LLM-as-judge that SCORES a drafted reply for quality.

Distinct from eval_harness.py:
  - eval_harness  -> did the agent make the right DECISION (route/escalate)?  (vs labels)
  - qa_agent      -> is the drafted REPLY actually good?  (quality, vs the source article)

Scores 4 dimensions (1-5) and returns pass/fail. A low score is meant to be
used as an extra escalation signal: if QA fails, don't auto-send -> hand to a human.

USAGE:
    from qa_agent import score_reply
    qa = score_reply(ticket, reply_text, source_article)
"""

import os, json, re
from dotenv import load_dotenv
from anthropic import Anthropic
from config import MODEL

load_dotenv()
client = Anthropic()

QA_SYSTEM = """You are a strict QA reviewer for customer-support replies.

You are given: the customer's ticket, the support reply that was drafted, and the
knowledge-base article the reply was supposed to be based on.

Score the reply 1-5 on each dimension (5 = excellent, 1 = unacceptable):
- groundedness: is EVERY claim supported by the provided article? Penalize any
  invented steps, settings, URLs, or facts not in the article.
- relevance: does it actually answer the customer's specific question?
- tone: is it clear, professional, and appropriate for support?
- safety: is it free of anything harmful, promises it shouldn't make, or data it
  shouldn't reveal?

Respond with ONLY a JSON object, nothing else:
{"groundedness": 1-5, "relevance": 1-5, "tone": 1-5, "safety": 1-5, "reasoning": "one short sentence"}"""


def _parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def score_reply(ticket, reply_text, source_article="", pass_threshold=4):
    """Independently score a drafted reply. Returns a dict with the four scores,
    an overall pass/fail, and the lowest dimension (the reason if it fails).

    pass_threshold: minimum score required on EVERY dimension to pass. We require
    all dimensions to clear the bar (not an average) — one bad dimension
    (e.g. ungrounded) should fail the reply even if the others are fine.
    """
    user_msg = (
        f"Customer ticket:\nSubject: {ticket.get('subject','')}\n"
        f"Body: {ticket.get('body','')}\n\n"
        f"Knowledge-base article the reply should be based on:\n{source_article or '(none provided)'}\n\n"
        f"Drafted reply to review:\n{reply_text}"
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=QA_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    scores = _parse_json(resp.content[0].text.strip())

    dims = ["groundedness", "relevance", "tone", "safety"]
    lowest_dim = min(dims, key=lambda d: scores.get(d, 0))
    lowest_score = scores.get(lowest_dim, 0)
    passed = all(scores.get(d, 0) >= pass_threshold for d in dims)

    return {
        "scores": {d: scores.get(d) for d in dims},
        "reasoning": scores.get("reasoning", ""),
        "passed": passed,
        "weakest": lowest_dim,
        "weakest_score": lowest_score,
    }


if __name__ == "__main__":
    # quick manual test: a GOOD grounded reply vs a HALLUCINATED one
    ticket = {"subject": "How do I set up SSO?",
              "body": "We want SAML SSO with our identity provider."}
    article = ("Configuring SAML SSO: go to Admin > Security > SSO, select SAML, "
               "enter your IdP sign-in URL and certificate, copy the ACS URL back "
               "to your IdP, map the email attribute, and test with one account.")

    good = ("To set up SAML SSO, go to Admin > Security > SSO and choose SAML. "
            "Enter your identity provider's sign-in URL and certificate, copy our "
            "ACS URL back into your IdP, map the email attribute, and test with a "
            "single account before rolling out.")
    bad = ("Just call our SSO hotline at 1-800-555-0199 and we'll enable SSO on "
           "your account within 24 hours. It's included free on all plans.")

    print("=== GOOD reply ===")
    print(score_reply(ticket, good, article))
    print("\n=== HALLUCINATED reply ===")
    print(score_reply(ticket, bad, article))
