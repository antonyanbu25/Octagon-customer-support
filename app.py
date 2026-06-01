"""
Streamlit demo for the Octagon Support Triage Agent.

A clickable demo: paste a ticket (or pick a sample), watch the agent classify,
retrieve, draft a grounded reply, and decide whether to auto-send or escalate.
Runs on MOCK data (sample contacts) — safe, no real customer data, no live
Freshdesk needed.

RUN LOCALLY:
    pip install streamlit
    streamlit run app.py

DEPLOY (Streamlit Community Cloud):
    push to GitHub -> share.streamlit.io -> point at this repo/app.py
    -> add ANTHROPIC_API_KEY in the app's Secrets settings.
"""

import streamlit as st
from triage_agent import handle_ticket
from sample_data import SAMPLE_TICKETS, CONTACTS
from kb_index import build_index, retrieve
try:
    retrieve("test", n_results=1)   # probe: does the index exist?
except Exception:
    build_index()                    # empty/missing -> build it now
st.set_page_config(page_title="Octagon Triage Agent", page_icon="🎯", layout="centered")

st.title("🎯 Octagon — Support Triage Agent")
st.caption(
    "Classifies a ticket, retrieves a grounded answer, and decides whether to "
    "auto-send or escalate to a human. Built with RAG, evals, and human-in-the-loop "
    "escalation. Demo runs on sample data."
)

# --- pick a sample ticket or write your own ---
sample_labels = ["(write my own)"] + [
    f"#{t['id']} — {t['subject']}" for t in SAMPLE_TICKETS
]
choice = st.selectbox("Start from a sample ticket, or write your own:", sample_labels)

if choice == "(write my own)":
    subject = st.text_input("Subject", "")
    body = st.text_area("Body", "", height=120)
    # let the user pick a known contact (so plan lookup works in the demo)
    email = st.selectbox("Requester (sample contacts)", list(CONTACTS.keys()))
    ticket = {"id": "demo", "requester_email": email, "subject": subject, "body": body}
else:
    idx = sample_labels.index(choice) - 1
    ticket = SAMPLE_TICKETS[idx]
    st.text_input("Subject", ticket["subject"], disabled=True)
    st.text_area("Body", ticket["body"], height=120, disabled=True)

run_qa = st.checkbox("Run QA review on the drafted reply (extra LLM-as-judge check)", value=False)

if st.button("Run the agent", type="primary"):
    if not ticket.get("subject") and not ticket.get("body"):
        st.warning("Add a subject or body first.")
    else:
        with st.spinner("Thinking… (classify → retrieve → draft → decide)"):
            result = handle_ticket(ticket, run_qa=run_qa)

        # --- decision banner ---
        if result["action"] == "auto_send":
            st.success(f"✅ AUTO-SEND  →  routed to **{result['team']}**")
        else:
            st.warning(f"🤝 ESCALATE to a human  →  **{result['team']}**")
            st.write("**Why:** " + ", ".join(result["reasons"]))

        # --- the drafted reply (if any) ---
        if result["reply"]:
            st.subheader("Drafted reply")
            st.write(result["reply"])

        # --- the signals, for transparency ---
        with st.expander("Signals the agent extracted"):
            st.json({
                "plan_class": result["plan_class"],
                "intent": result["intent"],
                "team": result["team"],
                "churn_risk": result["churn_risk"],
                "is_bug": result["is_bug"],
                "confidence": result["confidence"],
                "plan_miss": result["plan_miss"],
                "grounded": result["grounded"],
            })

        # --- QA result, if run ---
        if result.get("qa"):
            with st.expander("QA review (LLM-as-judge)"):
                st.json(result["qa"])
