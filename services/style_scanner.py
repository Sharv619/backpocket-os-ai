"""
Style Scanner — sovereign, embedding-driven writing style extraction.

Pipeline:
  1. Fetch sent emails from Gmail
  2. Embed each email locally via ChromaDB (all-MiniLM-L6-v2, no cloud)
  3. Semantic tone profiling: cosine similarity against tone anchor phrases
  4. Vocabulary fingerprinting: n-gram frequency + semantic clustering
  5. Anti-pattern detection: phrases semantically far from user's centroid
  6. AI synthesis: structured style guide generated from all signals
  7. Write to docs/CHERRY_STYLE.txt — 100% data-derived, no hardcoded template
"""

import base64
import collections
import logging
import math
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

STYLE_FILE = "docs/CHERRY_STYLE.txt"
CHROMA_COLLECTION = "style_mirror"
MAX_EMAILS = 100
MAX_BODY_CHARS = 1000

# ── Tone anchors — embed these, measure user emails against them ───────────────
TONE_ANCHORS = {
    "warm_friendly":   "Hi! Hope you're doing well. Really appreciate your time. Looking forward to catching up.",
    "formal_corporate": "Please find attached the document as requested. Kindly revert at your earliest convenience.",
    "direct_efficient": "Done. See attached. Let me know if you need anything else.",
    "casual_conversational": "Hey! Yeah totally works for me. Can we do Tuesday? Cheers.",
    "assertive_confident": "I'll handle this by Friday. No issue. Leave it with me.",
    "apologetic_hedging": "Sorry to bother you. I hope this isn't too much trouble. Please do let me know if this is okay.",
}

# ── Corporate anti-patterns — phrases a sovereign voice avoids ─────────────────
CORPORATE_ANTI_PATTERNS = [
    "as per my last email",
    "kindly find attached",
    "please revert",
    "as discussed herewith",
    "pursuant to",
    "I hope this email finds you well",
    "please do not hesitate to contact",
    "thanking you in anticipation",
    "at your earliest convenience",
    "per our conversation",
]


# ══════════════════════════════════════════════════════════════════════════════
# Gmail fetch
# ══════════════════════════════════════════════════════════════════════════════

def _decode_body(payload: Dict) -> str:
    mime = payload.get("mimeType", "")
    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
    for part in payload.get("parts", []):
        text = _decode_body(part)
        if text:
            return text
    return ""


def fetch_sent_emails(token_file: str = "token.json", limit: int = MAX_EMAILS) -> Tuple[List[Dict], str]:
    """
    Fetch sent emails. Returns (emails_list, sender_email).
    Each email: {subject, body, date}.
    """
    try:
        from services.gmail import get_gmail_service
        service = get_gmail_service(token_file)
        if not service:
            return [], ""

        profile = service.users().getProfile(userId="me").execute()
        sender_email = profile.get("emailAddress", "")

        results = service.users().messages().list(
            userId="me", labelIds=["SENT"], maxResults=limit
        ).execute()
        messages = results.get("messages", [])

        emails = []
        for msg in messages:
            try:
                detail = service.users().messages().get(
                    userId="me", id=msg["id"], format="full"
                ).execute()
                headers = detail.get("payload", {}).get("headers", [])
                subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
                date = next((h["value"] for h in headers if h["name"] == "Date"), "")
                body = _decode_body(detail.get("payload", {})).strip()[:MAX_BODY_CHARS]
                if len(body) > 40:
                    emails.append({"subject": subject, "body": body, "date": date})
            except Exception as e:
                logger.debug(f"Skip msg {msg['id']}: {e}")

        logger.info(f"Fetched {len(emails)} sent emails from {sender_email}")
        return emails, sender_email

    except Exception as e:
        logger.error(f"fetch_sent_emails failed: {e}")
        return [], ""


# ══════════════════════════════════════════════════════════════════════════════
# Embedding layer — ChromaDB local (all-MiniLM-L6-v2, sovereign)
# ══════════════════════════════════════════════════════════════════════════════

def _get_chroma_collection():
    """Get or create the style_mirror ChromaDB collection."""
    try:
        import chromadb
        from chromadb.config import Settings
        from pathlib import Path

        db_dir = Path(os.path.expanduser("~/.backpocket/chromadb"))
        db_dir.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(
            path=str(db_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        # Reset collection so each scan is fresh
        try:
            client.delete_collection(CHROMA_COLLECTION)
        except Exception:
            pass
        collection = client.create_collection(CHROMA_COLLECTION)
        return collection
    except Exception as e:
        logger.warning(f"ChromaDB unavailable: {e}")
        return None


def embed_emails(emails: List[Dict]) -> List[List[float]]:
    """
    Embed all email bodies locally. Returns list of embedding vectors.
    Falls back to Ollama nomic-embed-text if chromadb default unavailable.
    """
    texts = [e["body"] for e in emails]
    collection = _get_chroma_collection()

    if collection is not None:
        try:
            ids = [f"email_{i}" for i in range(len(texts))]
            collection.add(documents=texts, ids=ids)
            results = collection.get(ids=ids, include=["embeddings"])
            vecs = results.get("embeddings", [])
            if vecs and len(vecs) == len(texts):
                logger.info(f"Embedded {len(vecs)} emails via ChromaDB local model")
                return vecs, collection
        except Exception as e:
            logger.warning(f"ChromaDB embed failed: {e}")

    # Ollama fallback
    try:
        import requests
        vecs = []
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        for text in texts:
            r = requests.post(
                f"{ollama_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text[:500]},
                timeout=10,
            )
            vecs.append(r.json().get("embedding", []))
        logger.info(f"Embedded {len(vecs)} emails via Ollama")
        return vecs, None
    except Exception as e:
        logger.warning(f"Ollama embed failed: {e}")

    return [], None


def _cosine_sim(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _centroid(vectors: List[List[float]]) -> List[float]:
    if not vectors:
        return []
    dim = len(vectors[0])
    result = [0.0] * dim
    for v in vectors:
        for i, x in enumerate(v):
            result[i] += x
    n = len(vectors)
    return [x / n for x in result]


# ══════════════════════════════════════════════════════════════════════════════
# Isolation Forest — noise filtering before AI call
# ══════════════════════════════════════════════════════════════════════════════

def filter_inliers(
    emails: List[Dict],
    vectors: List[List[float]],
    contamination: float = 0.20,
) -> Tuple[List[Dict], List[List[float]], Dict[str, Any]]:
    """
    Run Isolation Forest on email embeddings to detect and discard outliers.

    Outliers = auto-replies, forwarded threads, calendar invites, OOO messages,
    one-liner acknowledgements — anything not representative of the user's voice.

    contamination=0.20 means we expect ~20% of emails to be noise.
    Returns (clean_emails, clean_vectors, diagnostics).
    """
    if len(emails) < 10:
        return emails, vectors, {"skipped": True, "reason": "too few samples"}

    # No vectors (ChromaDB down) — fall back to TF-IDF via IFFilter
    if not vectors:
        try:
            from services.if_filter import IFFilter
            clean_emails, diag = IFFilter.filter_dicts(
                emails, text_key="body", contamination=contamination
            )
            clean_vecs = []  # no vectors available
            return clean_emails, clean_vecs, {**diag, "method": "tfidf_fallback"}
        except Exception as e:
            return emails, vectors, {"skipped": True, "reason": f"tfidf fallback failed: {e}"}

    try:
        import numpy as np
        from sklearn.ensemble import IsolationForest

        X = np.array(vectors, dtype=np.float32)

        clf = IsolationForest(
            contamination=contamination,
            n_estimators=150,       # more trees = stable with small N
            random_state=42,
            n_jobs=-1,
        )
        labels = clf.fit_predict(X)   # 1 = inlier, -1 = outlier
        scores = clf.decision_function(X)  # higher = more normal

        clean_emails, clean_vecs = [], []
        outlier_emails = []

        for i, (email, vec, label) in enumerate(zip(emails, vectors, labels)):
            if label == 1:
                clean_emails.append(email)
                clean_vecs.append(vec)
            else:
                outlier_emails.append({
                    "subject": email["subject"][:60],
                    "score": round(float(scores[i]), 4),
                })

        logger.info(
            f"Isolation Forest: {len(clean_emails)} inliers / "
            f"{len(outlier_emails)} outliers removed from {len(emails)} emails"
        )

        diagnostics = {
            "total_emails": len(emails),
            "inliers": len(clean_emails),
            "outliers_removed": len(outlier_emails),
            "contamination_rate": round(len(outlier_emails) / len(emails), 2),
            "outlier_sample": outlier_emails[:5],  # first 5 for debugging
        }
        return clean_emails, clean_vecs, diagnostics

    except ImportError:
        logger.warning("scikit-learn not installed — skipping Isolation Forest filter")
        return emails, vectors, {"skipped": True, "reason": "scikit-learn not installed"}
    except Exception as e:
        logger.warning(f"Isolation Forest failed, passing all emails through: {e}")
        return emails, vectors, {"skipped": True, "reason": str(e)}


def select_representative_sample(
    emails: List[Dict],
    vectors: List[List[float]],
    n: int = 30,
) -> List[Dict]:
    """
    From the inlier cluster, select the N most representative emails.
    'Most representative' = closest to the centroid of the cluster.
    Reduces AI prompt size without losing signal quality.
    """
    if len(emails) <= n:
        return emails

    if not vectors:
        # No embeddings — fall back to even distribution across time
        step = max(1, len(emails) // n)
        return emails[::step][:n]

    try:
        import numpy as np

        X = np.array(vectors, dtype=np.float32)
        centroid = X.mean(axis=0)
        dists = np.linalg.norm(X - centroid, axis=1)
        # Closest to centroid = most representative of the cluster
        top_indices = np.argsort(dists)[:n]
        selected = [emails[i] for i in sorted(top_indices)]
        logger.info(f"Selected {len(selected)} most representative emails for AI synthesis")
        return selected
    except Exception as e:
        logger.warning(f"Representative selection failed: {e}")
        return emails[:n]


# ══════════════════════════════════════════════════════════════════════════════
# Tone profiling
# ══════════════════════════════════════════════════════════════════════════════

def _embed_text_single(text: str, collection) -> List[float]:
    """Embed a single text using same model as collection, or Ollama fallback."""
    if collection is not None:
        try:
            tmp_id = f"_tmp_{hash(text)}"
            collection.add(documents=[text], ids=[tmp_id])
            result = collection.get(ids=[tmp_id], include=["embeddings"])
            collection.delete(ids=[tmp_id])
            vecs = result.get("embeddings", [])
            if vecs:
                return vecs[0]
        except Exception:
            pass

    try:
        import requests
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        r = requests.post(
            f"{ollama_url}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text[:500]},
            timeout=10,
        )
        return r.json().get("embedding", [])
    except Exception:
        return []


def profile_tone(email_vectors: List[List[float]], collection) -> Dict[str, float]:
    """
    Compute cosine similarity of the user's email centroid against each tone anchor.
    Returns dict: {tone_name: similarity_score 0-1}.
    """
    if not email_vectors:
        return {}

    centroid = _centroid(email_vectors)
    scores = {}
    for tone_name, anchor_text in TONE_ANCHORS.items():
        anchor_vec = _embed_text_single(anchor_text, collection)
        scores[tone_name] = round(_cosine_sim(centroid, anchor_vec), 3)

    # Sort descending
    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


def detect_avoided_phrases(email_vectors: List[List[float]], collection) -> List[str]:
    """
    Find corporate anti-pattern phrases that are semantically DISTANT from the user's centroid.
    Distance > threshold → they likely avoid this phrasing.
    """
    if not email_vectors:
        return []

    centroid = _centroid(email_vectors)
    avoided = []
    for phrase in CORPORATE_ANTI_PATTERNS:
        vec = _embed_text_single(phrase, collection)
        sim = _cosine_sim(centroid, vec)
        # Low similarity → semantically distant → they don't write this way
        if sim < 0.35:
            avoided.append(phrase)
    return avoided


# ══════════════════════════════════════════════════════════════════════════════
# Vocabulary fingerprinting
# ══════════════════════════════════════════════════════════════════════════════

def extract_vocabulary_fingerprint(emails: List[Dict]) -> Dict[str, Any]:
    """
    Extract n-gram frequency fingerprint from all emails.
    Returns: {phrases: top bigrams/trigrams, greetings: [], signoffs: [], avg_length: int}
    """
    all_text = " ".join(e["body"] for e in emails).lower()
    all_bodies = [e["body"] for e in emails]

    # Greetings — first line of each email
    greetings = collections.Counter()
    signoffs = collections.Counter()
    lengths = []

    for body in all_bodies:
        lines = [l.strip() for l in body.split("\n") if l.strip()]
        if lines:
            first = lines[0]
            # Extract just the greeting token (up to first comma or 30 chars)
            greeting = re.split(r'[,!]', first)[0].strip()
            if 2 < len(greeting) < 40:
                greetings[greeting] += 1
        if lines:
            last = lines[-1]
            if len(last) < 60:
                signoffs[last] += 1
        lengths.append(len(body.split()))

    # Bigrams + trigrams from full corpus
    tokens = re.findall(r"\b[a-zA-Z]{2,}\b", all_text)
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
                 "for", "of", "is", "are", "was", "were", "be", "been", "have",
                 "has", "had", "do", "did", "will", "would", "could", "should",
                 "may", "might", "can", "this", "that", "these", "those", "it",
                 "its", "i", "you", "we", "they", "he", "she", "my", "your",
                 "our", "their", "me", "us", "him", "her", "with", "from", "by",
                 "as", "if", "so", "not", "no", "up", "out", "about", "just",
                 "get", "got", "also", "all", "some", "any", "very", "more"}
    content_tokens = [t for t in tokens if t not in stopwords]

    bigrams = collections.Counter(
        f"{content_tokens[i]} {content_tokens[i+1]}"
        for i in range(len(content_tokens) - 1)
    )
    trigrams = collections.Counter(
        f"{content_tokens[i]} {content_tokens[i+1]} {content_tokens[i+2]}"
        for i in range(len(content_tokens) - 2)
    )

    return {
        "top_greetings": [g for g, _ in greetings.most_common(8)],
        "top_signoffs": [s for s, _ in signoffs.most_common(8)],
        "top_bigrams": [p for p, _ in bigrams.most_common(20)],
        "top_trigrams": [p for p, _ in trigrams.most_common(15)],
        "avg_word_count": round(sum(lengths) / len(lengths)) if lengths else 0,
        "median_word_count": sorted(lengths)[len(lengths) // 2] if lengths else 0,
    }


# ══════════════════════════════════════════════════════════════════════════════
# AI synthesis — generate structured style guide from extracted signals
# ══════════════════════════════════════════════════════════════════════════════

def synthesise_style_guide(
    emails: List[Dict],
    tone_profile: Dict[str, float],
    vocab: Dict[str, Any],
    avoided_phrases: List[str],
    email_count: int,
    sender_email: str,
) -> str:
    """
    Send all extracted signals + raw email samples to AI.
    AI generates the full structured style guide from scratch.
    """
    # Build tone description from scores
    tone_lines = "\n".join(
        f"  - {k.replace('_', ' ')}: {v:.1%}"
        for k, v in list(tone_profile.items())[:6]
    )

    avoided_text = "\n".join(f"  - \"{p}\"" for p in avoided_phrases) or "  (none detected)"

    vocab_text = f"""
  Greeting openers (most common): {', '.join(f'"{g}"' for g in vocab['top_greetings'][:5])}
  Sign-off phrases (most common): {', '.join(f'"{s}"' for s in vocab['top_signoffs'][:5])}
  Characteristic bigrams: {', '.join(vocab['top_bigrams'][:12])}
  Characteristic trigrams: {', '.join(vocab['top_trigrams'][:8])}
  Average email length: {vocab['avg_word_count']} words
  Median email length: {vocab['median_word_count']} words"""

    # Raw samples (20 emails max for AI synthesis)
    samples_text = ""
    for e in emails[:20]:
        samples_text += f"\n---\nSubject: {e['subject']}\n{e['body']}\n"

    prompt = f"""You are analysing {email_count} real emails sent by {sender_email or 'the user'}.
The following signals have been extracted using local embedding models and n-gram analysis.
Your job: synthesise these into a complete, actionable AI Twin Style Guide.

=== EMBEDDING-DERIVED TONE PROFILE (cosine similarity vs tone anchors) ===
{tone_lines}

=== VOCABULARY FINGERPRINT (n-gram extraction) ===
{vocab_text}

=== CORPORATE PHRASES SEMANTICALLY AVOIDED BY THIS PERSON ===
{avoided_text}

=== RAW EMAIL SAMPLES (for qualitative verification) ===
{samples_text}

Now write a complete AI Twin Style Guide with these exact sections:

## CORE PERSONALITY
(3-5 bullet points describing their overall communication identity, derived from tone profile + samples)

## GREETING PATTERNS
(Exact phrases they use to open emails, ranked by frequency. Note any patterns — first name use, time-of-day references, etc.)

## SIGN-OFF PHRASES
(Exact closing phrases ranked by frequency. Note any variation by context)

## VOCABULARY & PHRASES TO USE
(Their characteristic words/phrases. Grouped: common phrases, filler words they like, power words)

## VOCABULARY & PHRASES TO NEVER USE
(Based on semantic distance analysis + anti-pattern detection. These feel wrong in their voice)

## TONE BALANCE
(Quantified tone breakdown from embedding analysis. E.g. "65% warm/friendly, 25% direct/efficient, 10% formal")

## EMAIL LENGTH & STRUCTURE
(How long do they write? Do they use bullet points? Paragraphs? Headers? Short replies?)

## QUIRKS & FINGERPRINT
(Unique patterns: punctuation habits, emoji use, Australian English, capitalisation style, anything distinctive)

## AI INSTRUCTIONS
(2-3 sentences telling an AI twin exactly how to apply this style when drafting emails on their behalf)

Rules:
- Quote real examples from the email samples wherever possible
- All observations must be grounded in the data — no assumptions
- Be specific and concrete, not vague
- Write in second person ("You open with...", "Your sign-off...")
- This will be machine-read by an AI twin — make it unambiguous and directly usable"""

    try:
        from services.gemini import get_openrouter_response
        result = get_openrouter_response(
            prompt,
            model="google/gemma-3-27b-it:free",
            sys_prompt="You are a precision writing-style analyst. Your output is an AI instruction document. Be specific, quote examples, no fluff.",
        )
        if result and len(result) > 300:
            logger.info(f"Style guide synthesised via OpenRouter ({len(result)} chars)")
            return result
    except Exception as e:
        logger.warning(f"OpenRouter synthesis failed: {e}")

    try:
        from services.gemini import get_gemini_client
        client = get_gemini_client()
        if client:
            r = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            if r and r.text:
                logger.info(f"Style guide synthesised via Gemini ({len(r.text)} chars)")
                return r.text.strip()
    except Exception as e:
        logger.error(f"Gemini synthesis failed: {e}")

    return ""


# ══════════════════════════════════════════════════════════════════════════════
# File writer
# ══════════════════════════════════════════════════════════════════════════════

def _write_style_file(guide: str, email_count: int, sender_email: str, tone_profile: Dict) -> None:
    top_tone = list(tone_profile.items())[0] if tone_profile else ("unknown", 0)
    header = f"""# ✍️ AI TWIN STYLE GUIDE
# Source: {email_count} sent emails from {sender_email}
# Dominant tone: {top_tone[0].replace('_', ' ')} ({top_tone[1]:.1%})
# Generated: {datetime.now().strftime('%d %b %Y %H:%M')} — sovereign local embeddings (all-MiniLM-L6-v2)
# Refresh: POST /api/style/scan-sent
# ⚠️  AUTO-GENERATED — do not edit manually, changes will be overwritten on next scan

---

"""
    os.makedirs("docs", exist_ok=True)
    with open(STYLE_FILE, "w", encoding="utf-8") as f:
        f.write(header + guide)
    logger.info(f"Style file written → {STYLE_FILE} ({len(guide)} chars)")


# ══════════════════════════════════════════════════════════════════════════════
# Public entry point
# ══════════════════════════════════════════════════════════════════════════════

def scan_sent_for_style(token_file: str = "token.json") -> Dict[str, Any]:
    """
    Full pipeline: fetch → embed → tone profile → vocab fingerprint → AI synthesis → write file.
    Returns status dict with diagnostics.
    """
    # 1. Fetch
    emails, sender_email = fetch_sent_emails(token_file)
    if not emails:
        return {"status": "error", "message": "No sent emails found or Gmail not connected", "emails_scanned": 0}

    # 2. Embed (local, sovereign)
    logger.info(f"Embedding {len(emails)} emails locally...")
    email_vectors, collection = embed_emails(emails)

    # 3. Isolation Forest — remove noise before anything hits the AI
    if_diagnostics = {}
    clean_emails, clean_vectors = emails, email_vectors
    if email_vectors:
        clean_emails, clean_vectors, if_diagnostics = filter_inliers(emails, email_vectors)
    else:
        logger.warning("No vectors — skipping Isolation Forest, using all emails")

    # 4. Select most representative sample for AI (centroid-nearest, max 30)
    ai_sample = select_representative_sample(clean_emails, clean_vectors, n=30)
    logger.info(
        f"Pipeline: {len(emails)} raw → {len(clean_emails)} inliers "
        f"→ {len(ai_sample)} sent to AI"
    )

    # 5. Tone profile (on full inlier cluster, not just AI sample)
    tone_profile = {}
    avoided_phrases = []
    if clean_vectors:
        logger.info("Profiling tone via embedding cosine similarity...")
        tone_profile = profile_tone(clean_vectors, collection)
        avoided_phrases = detect_avoided_phrases(clean_vectors, collection)
        logger.info(f"Tone: {list(tone_profile.items())[:3]} | Avoided: {len(avoided_phrases)} phrases")
    else:
        logger.warning("Embedding unavailable — skipping tone profile, using text-only analysis")

    # 6. Vocabulary fingerprint — run on full inlier cluster (not just AI sample)
    vocab = extract_vocabulary_fingerprint(clean_emails)

    # 7. AI synthesis — only receives the curated representative sample
    logger.info(f"Synthesising style guide via AI ({len(ai_sample)} emails)...")
    guide = synthesise_style_guide(
        ai_sample, tone_profile, vocab, avoided_phrases, len(clean_emails), sender_email
    )
    if not guide:
        return {"status": "error", "message": "AI synthesis returned empty result", "emails_scanned": len(emails)}

    # 6. Write file
    _write_style_file(guide, len(emails), sender_email, tone_profile)

    return {
        "status": "success",
        "emails_scanned": len(emails),
        "inliers_used": len(clean_emails),
        "ai_sample_size": len(ai_sample),
        "sender_email": sender_email,
        "tone_profile": tone_profile,
        "avoided_phrases": avoided_phrases,
        "isolation_forest": if_diagnostics,
        "vocab_sample": {
            "greetings": vocab["top_greetings"][:3],
            "signoffs": vocab["top_signoffs"][:3],
            "avg_length_words": vocab["avg_word_count"],
        },
        "style_file": STYLE_FILE,
        "preview": guide[:600] + ("..." if len(guide) > 600 else ""),
        "scanned_at": datetime.now().isoformat(),
    }
