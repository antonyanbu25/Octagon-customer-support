"""
Builds a semantic search index over the KB articles, and exposes retrieve().

NEW CONCEPT vs the keyword demo:
  Before, you matched tickets to docs by shared WORDS. Here, ChromaDB turns each
  article into an EMBEDDING (a list of numbers capturing its MEANING) and stores
  them in a VECTOR STORE. A query is embedded the same way, and retrieval returns
  the articles whose meaning is closest — even with no shared words. That's
  semantic search.

ChromaDB bundles a local embedding model, so no extra API key is needed. On the
first run it downloads that small model once, then works offline.

USAGE:
    pip install chromadb
    python kb_index.py        # builds the index + runs a quick smoke test
"""
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
import chromadb
from kb_articles import KB_ARTICLES

# PersistentClient stores the index on disk (in ./kb_store) so it survives
# restarts — you build it once, not every run. (This is the 'persistence'
# concept again: state saved to disk instead of rebuilt from scratch.)
client = chromadb.PersistentClient(path="./kb_store")

# A 'collection' is one searchable set of documents. get_or_create avoids
# errors if it already exists from a previous run.
collection = client.get_or_create_collection(name="octagon_kb")


def build_index():
    """Embed and store every KB article. upsert() = insert-or-update, so
    re-running won't create duplicates."""
    collection.upsert(
        ids=[a["id"] for a in KB_ARTICLES],            # stable id per article
        documents=[a["content"] for a in KB_ARTICLES], # the text that gets embedded
        metadatas=[{"title": a["title"]} for a in KB_ARTICLES],  # extra info to carry along
    )
    print(f"Indexed {collection.count()} articles into ./kb_store")


def retrieve(query, n_results=2):
    """Return the n most semantically-similar KB articles to `query`.

    ChromaDB embeds the query, compares it to every stored article embedding,
    and returns the closest matches. Lower 'distance' = more similar.
    """
    results = collection.query(query_texts=[query], n_results=n_results)

    # ChromaDB supports batching many queries at once, so every field comes back
    # as a LIST-OF-LISTS (one inner list per query). We sent ONE query, so we
    # read index [0] of each to get our results.
    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "id": results["ids"][0][i],
            "title": results["metadatas"][0][i]["title"],
            "content": results["documents"][0][i],
            "distance": results["distances"][0][i],   # lower = closer in meaning
        })
    return hits


if __name__ == "__main__":
    build_index()

    # Smoke test: note these queries share FEW exact words with the articles,
    # so getting the right article back proves it's matching on MEANING.
    smoke_queries = [
        "How do I auto-assign tickets by keyword?",   # -> automation_setup
        "Our Slack keeps logging out",                # -> slack_integration
        "I can't remember my password",               # -> login_recovery
        "single sign on with Okta",                   # -> sso_saml
    ]
    for q in smoke_queries:
        print(f"\nQuery: {q!r}")
        for hit in retrieve(q):
            print(f"   -> {hit['title']:<45} (distance {hit['distance']:.3f})")
    print()