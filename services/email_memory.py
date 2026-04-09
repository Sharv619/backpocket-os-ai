"""
BackPocket OS - Email Memory (Semantic Search)
==============================================
FTS5 + Gemini re-ranking for semantic email search
"""

import sqlite3
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

DB_PATH = "backpocket.db"

def init_email_fts():
    """Initialize FTS5 table for email indexing."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS email_fts USING fts5(
            ref_id,
            subject,
            snippet,
            sender,
            date
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("EMAIL FTS INITIALIZED")

def index_email(ref_id: str, subject: str = "", snippet: str = "", sender: str = "", date: str = ""):
    """Index an email for search."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    
    try:
        # Delete existing entry first (FTS5 doesn't support INSERT OR REPLACE)
        cursor.execute('DELETE FROM email_fts WHERE ref_id = ?', (ref_id,))
        cursor.execute('''
            INSERT INTO email_fts (ref_id, subject, snippet, sender, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (ref_id, subject, snippet, sender, date))
        conn.commit()
    except Exception as e:
        logger.warning(f"Index email error: {e}")
    finally:
        conn.close()

def reindex_all_emails():
    """Reindex all pending emails to FTS."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT ref_id, subject, draft_body, sender, created_at FROM pending_approvals")
        rows = cursor.fetchall()
        for row in rows:
            ref_id, subject, draft_body, sender, created_at = row
            snippet = (draft_body or "")[:500]
            index_email(ref_id, subject or "", snippet, sender or "", created_at or "")
        logger.info(f"Reindexed {len(rows)} emails")
    except Exception as e:
        logger.error(f"Reindex error: {e}")
    finally:
        conn.close()

def semantic_search(query: str, limit: int = 5) -> List[Dict]:
    """Search emails using FTS5 + Gemini re-ranking.
    
    Returns semantically relevant results even for natural language queries.
    """
    if not query or len(query.strip()) < 2:
        return []
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=20)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        fts_query = query.replace('"', '').replace("'", "").replace(".", " ").strip()
        search_terms = fts_query.split()
        
        if len(search_terms) == 1:
            match_query = f'"{search_terms[0]}"'
        else:
            match_query = ' OR '.join([f'"{t}"' for t in search_terms if t])
        
        cursor.execute('''
            SELECT ref_id, subject, snippet, sender, date
            FROM email_fts
            WHERE email_fts MATCH ?
        ''', (match_query,))
        
        raw_results = cursor.fetchall()
        conn.close()
        
        if not raw_results:
            return []
        
        if len(raw_results) <= limit:
            return [dict(r) for r in raw_results]
        
        reranked = rerank_with_gemini(query, [dict(r) for r in raw_results], limit)
        return reranked
        
    except Exception as e:
        logger.warning(f"Email search error: {e}")
        return []

def rerank_with_gemini(query: str, results: List[Dict], limit: int) -> List[Dict]:
    """Re-rank FTS results using Gemini semantic understanding."""
    try:
        from services.gemini import get_gemini_client
        
        client = get_gemini_client()
        if not client:
            return results[:limit]
        
        items_text = "\n".join([
            f"{i+1}. Ref: {r.get('ref_id', 'N/A')} | From: {r.get('sender', 'N/A')} | Subject: {r.get('subject', 'N/A')[:50]}"
            for i, r in enumerate(results[:10])
        ])
        
        prompt = f"""Given this query: "{query}"

Which of these emails are most relevant to the query? Consider:
- Does the sender match the query?
- Does the subject/topics match?
- Is the email content related?

Rank by relevance (1=most relevant). Return ONLY a JSON list of the top {limit} indices in order:
[1, 3, 2, 5, 4]

Emails:
{items_text}

JSON list of indices:"""
        
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        response_text = response.text.strip() if response and response.text else "[]"
        
        import json
        try:
            indices = json.loads(response_text)
            reranked = [results[i-1] for i in indices if 0 < i <= len(results)]
            return reranked[:limit]
        except Exception:
            return results[:limit]
            
    except Exception as e:
        logger.warning(f"Rerank error: {e}")
        return results[:limit]

def search_emails_natural(query: str, limit: int = 5) -> List[Dict]:
    """Search emails with natural language query.
    
    Example: "Has Angelo asked about SMSF before?"
    """
    keywords = extract_search_keywords(query)
    
    if keywords:
        search_query = " OR ".join(keywords)
    else:
        search_query = query
    
    return semantic_search(search_query, limit)

def extract_search_keywords(query: str) -> List[str]:
    """Extract key search terms from natural language query."""
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "have", "has", "had", 
                  "do", "does", "did", "will", "would", "could", "should", "can", "may",
                  "about", "from", "to", "for", "in", "on", "at", "by", "with", "been",
                  "being", "been", "before", "after", "asked", "asked", "mention", "said",
                  "has", "have", "his", "her", "their", "them", "this", "that", "these", "those"}
    
    words = query.lower().split()
    keywords = [w.strip(".,!?") for w in words if len(w) > 2 and w not in stop_words]
    
    return keywords[:5]

def get_email_context(ref_id: str) -> Optional[Dict]:
    """Get full email context for a search result."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM pending_approvals WHERE ref_id = ?", (ref_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

init_email_fts()
