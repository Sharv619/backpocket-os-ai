"""
IFFilter — Isolation Forest pre-filter for AI calls.

Drop this in front of any batch → AI call to remove outlier/noise items
before they waste tokens. Works on text (TF-IDF fallback) or pre-computed
embedding vectors. Zero AI calls — pure local sklearn + numpy.

Usage:
    from services.if_filter import IFFilter

    clean_chunks = IFFilter.filter_texts(chunks, query=query)
    clean_patterns = IFFilter.filter_dicts(patterns, text_key="pattern_data")
    clean_emails = IFFilter.filter_dicts(emails, text_key="body")
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Items below this count skip IF entirely — not enough data to fit the model.
MIN_ITEMS = 6
# Default fraction assumed to be noise.
DEFAULT_CONTAMINATION = 0.20


# ══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ══════════════════════════════════════════════════════════════════════════════

def _tfidf_matrix(texts: List[str]):
    """Build a TF-IDF feature matrix from texts. Returns numpy array or None."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
        vec = TfidfVectorizer(max_features=256, stop_words="english", min_df=1)
        X = vec.fit_transform(texts).toarray().astype(np.float32)
        return X
    except Exception as e:
        logger.debug(f"TF-IDF build failed: {e}")
        return None


def _run_isolation_forest(
    X,
    contamination: float,
    n_estimators: int = 150,
) -> Tuple[List[int], List[float]]:
    """
    Fit IsolationForest on X. Returns (labels, scores).
    labels: 1 = inlier, -1 = outlier.
    scores: higher = more normal.
    """
    from sklearn.ensemble import IsolationForest

    clf = IsolationForest(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=42,
        n_jobs=-1,
    )
    labels = clf.fit_predict(X).tolist()
    scores = clf.decision_function(X).tolist()
    return labels, scores


def _centroid_rank(X) -> List[int]:
    """Return indices sorted by distance to centroid (closest first)."""
    import numpy as np
    centroid = X.mean(axis=0)
    dists = ((X - centroid) ** 2).sum(axis=1) ** 0.5
    return sorted(range(len(dists)), key=lambda i: dists[i])


# ══════════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════════

class IFFilter:
    """
    Static utility — no instantiation needed.
    All methods return (filtered_items, diagnostics_dict).
    """

    @staticmethod
    def filter_texts(
        texts: List[str],
        query: Optional[str] = None,
        contamination: float = DEFAULT_CONTAMINATION,
        vectors: Optional[List[List[float]]] = None,
        top_n: Optional[int] = None,
    ) -> Tuple[List[str], Dict[str, Any]]:
        """
        Filter a list of text strings. Removes outliers via IF.
        If query provided, also reranks survivors by cosine similarity to query.
        If top_n provided, returns at most top_n items after filtering.

        Returns: (clean_texts, diagnostics)
        """
        if len(texts) < MIN_ITEMS:
            return texts, {"skipped": True, "reason": f"only {len(texts)} items"}

        try:
            import numpy as np

            # Build feature matrix — prefer pre-computed vectors
            if vectors and len(vectors) == len(texts):
                X = np.array(vectors, dtype=np.float32)
            else:
                X = _tfidf_matrix(texts)
                if X is None:
                    return texts, {"skipped": True, "reason": "feature extraction failed"}

            labels, scores = _run_isolation_forest(X, contamination)

            clean_texts = [t for t, l in zip(texts, labels) if l == 1]
            clean_X = X[[i for i, l in enumerate(labels) if l == 1]]
            outlier_count = labels.count(-1)

            diag = {
                "total": len(texts),
                "inliers": len(clean_texts),
                "outliers_removed": outlier_count,
            }

            if len(clean_texts) == 0:
                # IF removed everything (shouldn't happen) — fall back
                logger.warning("IF removed all items — returning originals")
                return texts, {**diag, "fallback": True}

            # Optional: rerank by query similarity
            if query and len(clean_X) > 1:
                query_X = _tfidf_matrix([query] + list(clean_texts))
                if query_X is not None:
                    q_vec = query_X[0]
                    item_vecs = query_X[1:]
                    def cosine(a, b):
                        dot = float(np.dot(a, b))
                        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
                        return dot / denom if denom else 0.0
                    ranked = sorted(
                        enumerate(clean_texts),
                        key=lambda x: cosine(item_vecs[x[0]], q_vec),
                        reverse=True,
                    )
                    clean_texts = [t for _, t in ranked]
                    diag["query_reranked"] = True

            # Optional: cap at top_n
            if top_n and len(clean_texts) > top_n:
                clean_texts = clean_texts[:top_n]
                diag["capped_at"] = top_n

            logger.debug(f"IFFilter: {len(texts)} → {len(clean_texts)} items")
            return clean_texts, diag

        except ImportError:
            logger.warning("scikit-learn not installed — IFFilter passthrough")
            return texts, {"skipped": True, "reason": "scikit-learn not installed"}
        except Exception as e:
            logger.warning(f"IFFilter failed — passthrough: {e}")
            return texts, {"skipped": True, "reason": str(e)}

    @staticmethod
    def filter_dicts(
        items: List[Dict],
        text_key: str,
        query: Optional[str] = None,
        contamination: float = DEFAULT_CONTAMINATION,
        top_n: Optional[int] = None,
    ) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        Filter a list of dicts using text from `text_key` field.
        Items missing the key are kept (conservative — don't drop what we can't score).

        Returns: (clean_items, diagnostics)
        """
        scoreable = [(i, item) for i, item in enumerate(items) if item.get(text_key)]
        unscoreable = [item for item in items if not item.get(text_key)]

        if len(scoreable) < MIN_ITEMS:
            return items, {"skipped": True, "reason": f"only {len(scoreable)} scoreable items"}

        indices, scoreable_items = zip(*scoreable)
        texts = [item[text_key][:800] for item in scoreable_items]

        clean_texts, diag = IFFilter.filter_texts(
            list(texts), query=query, contamination=contamination, top_n=top_n
        )

        # Map back to original dicts by text match
        clean_text_set = set(clean_texts)
        clean_items = [item for item in scoreable_items if item[text_key][:800] in clean_text_set]

        # Re-add unscoreable items at end (conservative keep)
        result = clean_items + unscoreable
        diag["unscoreable_kept"] = len(unscoreable)
        return result, diag

    @staticmethod
    def filter_rag_chunks(
        chunks: List[str],
        query: str,
        contamination: float = 0.15,
        top_n: int = 5,
    ) -> Tuple[List[str], Dict[str, Any]]:
        """
        Specialised wrapper for RAG chunk filtering.
        Lower contamination (0.15) — RAG chunks are already relevance-filtered by ChromaDB,
        so we only want to cut clear outliers. Reranks survivors by query similarity.
        """
        return IFFilter.filter_texts(
            chunks,
            query=query,
            contamination=contamination,
            top_n=top_n,
        )

    @staticmethod
    def filter_emails_for_twin(
        emails: List[Dict],
        text_key: str = "body",
        contamination: float = DEFAULT_CONTAMINATION,
        top_n: int = 10,
    ) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        Specialised wrapper for email batch filtering before twin drafts response.
        Removes auto-replies, newsletters, calendar noise.
        """
        return IFFilter.filter_dicts(
            emails,
            text_key=text_key,
            contamination=contamination,
            top_n=top_n,
        )
