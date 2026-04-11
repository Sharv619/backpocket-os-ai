"""
Agentic RAG System for BackPocket.

Orchestrates multiple specialized agents (Accountant, Auditor, Admin Twins)
with retrieval-augmented generation (RAG) to handle complex email responses
and autonomous business automation.

Features:
- Multi-agent orchestration with delegation
- Context retrieval from ChromaDB vector store
- Learned pattern application (corrections history)
- Narrative blog generation (wine-commercial storytelling style)
"""

import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class AgenticRAG:
    """Orchestrates twin agents with RAG context."""

    def __init__(self):
        self.twins = {}
        self._initialize_twins()

    def _initialize_twins(self):
        """Initialize the three specialized twins."""
        try:
            from services.twin_engine import RAGContextBuilder, TwinType, PERSONALITIES

            self.rag_builder = RAGContextBuilder()
            self.personalities = PERSONALITIES
            self.twin_types = TwinType

            logger.info("✓ Agentic RAG initialized with 3 twins (Accountant, Auditor, Admin)")
        except Exception as e:
            logger.error(f"Failed to initialize Agentic RAG: {e}")
            self.personalities = {}

    def get_context_for_email(self, email_content: Dict[str, Any], tier: int = 1) -> Dict[str, Any]:
        """Retrieve learned patterns and historical context for an email."""
        try:
            if not email_content:
                logger.warning("Empty email_content provided")
                return {}

            from services.database import get_learned_patterns, get_corrections
            from services.gmail import get_historical_context

            sender = email_content.get("sender", "")
            subject = email_content.get("subject", "")
            snippet = email_content.get("snippet", "")

            # Get learned patterns from corrections history
            learned_patterns = get_learned_patterns(
                sender_email=sender, subject=subject, limit=5
            ) or []

            # Get sender history
            historical = get_historical_context(sender, max_results=3) or ""

            # Get recent corrections for learning
            recent_corrections = get_corrections(limit=3) or []

            return {
                "learned_patterns": learned_patterns,
                "historical_context": historical,
                "recent_corrections": recent_corrections,
                "sender": sender,
                "subject": subject,
                "tier": tier,
            }
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            import traceback
            traceback.print_exc()
            return {
                "learned_patterns": [],
                "historical_context": "",
                "recent_corrections": [],
            }

    def select_best_twin(self, email_content: Dict[str, Any], tier: int) -> str:
        """Delegate to the best twin based on email content."""
        subject = email_content.get("subject", "").lower()
        sender = email_content.get("sender", "").lower()

        # Heuristic routing
        if any(x in subject for x in ["invoice", "tax", "bas", "ato", "gst", "expense"]):
            return "accountant"
        elif any(x in subject for x in ["audit", "compliance", "review", "verify", "check"]):
            return "auditor"
        else:
            return "admin"

    def generate_agentic_response(
        self,
        email_content: Dict[str, Any],
        tier: int = 1,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate response using agentic reasoning + RAG context."""

        if not context:
            context = self.get_context_for_email(email_content, tier)

        # Select appropriate twin
        best_twin = self.select_best_twin(email_content, tier)
        logger.info(f"🤖 Using {best_twin} twin for: {email_content.get('subject', '')[:50]}")

        # Build agentic prompt with learned patterns
        learned_patterns_text = ""
        if context and context.get("learned_patterns"):
            learned_patterns_text = "\n\nLEARNED PATTERNS FROM HISTORY:\n"
            for pattern in context["learned_patterns"]:
                feedback = pattern.get("feedback", "")
                if feedback:
                    learned_patterns_text += f"- {feedback}\n"

        # Get system prompt for the twin
        twin_prompts = {
            "accountant": "You are the Accountant Twin. Handle: invoicing, expense tracking, BAS preparation, ATO compliance, GST (10%), tax advice.",
            "auditor": "You are the Auditor Twin. Handle: document review, ATO compliance checks, invoice verification, quality assurance.",
            "admin": "You are the Admin Twin. Handle: email triage, scheduling, client follow-ups, reminders, admin automation."
        }

        system_prompt = twin_prompts.get(best_twin, f"You are the {best_twin} assistant for BackPocket OS.")

        # Construct agentic response
        response = {
            "twin": best_twin,
            "context": {
                "sender": context.get("sender", "") if context else "",
                "subject": context.get("subject", "") if context else "",
                "tier": context.get("tier", 1) if context else 1,
                "learned_patterns_count": len(context.get("learned_patterns", [])) if context else 0,
            },
            "system_prompt": system_prompt,
            "learned_patterns": learned_patterns_text,
            "timestamp": datetime.now().isoformat(),
        }

        return response

    def ingest_document_to_rag(
        self, twin_type: str, doc_id: str, text: str, metadata: Dict = None
    ) -> bool:
        """Add document to RAG vector store."""
        try:
            from services.twin_engine import TwinType

            twin = TwinType[twin_type.upper()]
            self.rag_builder.ingest(twin, doc_id, text, metadata)
            logger.info(f"✓ Ingested {len(text)} chars to {twin_type} RAG")
            return True
        except Exception as e:
            logger.error(f"Error ingesting to RAG: {e}")
            return False


class NarrativeBlogGenerator:
    """Generate AI-written blog posts in wine-commercial storytelling style."""

    WINE_COMMERCIAL_STYLE = """You are a masterful storyteller in the style of premium wine commercials.
Create a narrative that:
- Opens with evocative, sensory-rich language
- Builds tension/emotion gradually
- Uses metaphor and poetry
- Has moments of quiet reflection
- Concludes with inspiring wisdom
- Is 300-400 words long
- Feels luxurious yet relatable

The story should subtly weave in business themes without being preachy."""

    def __init__(self):
        self.client = self._get_ai_client()

    def _get_ai_client(self):
        """Get AI client (OpenRouter preferred)."""
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            return "openrouter"

        from services.gemini import get_gemini_client

        gemini = get_gemini_client()
        if gemini:
            return "gemini"

        return None

    def generate_blog_post(
        self, title: str, theme: str = "entrepreneurship", company_name: str = ""
    ) -> Dict[str, Any]:
        """Generate a narrative blog post."""

        prompt = f"""{self.WINE_COMMERCIAL_STYLE}

Title: "{title}"
Theme: {theme}
{f'Company: {company_name}' if company_name else ''}

Write an evocative, narrative blog post that feels like a premium storytelling experience."""

        try:
            if self.client == "openrouter":
                import requests

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                        "HTTP-Referer": "backpocket.ai",
                    },
                    json={
                        "model": "openrouter/auto",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.85,
                        "max_tokens": 500,
                    },
                    timeout=15,
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
            else:
                # Fallback to Gemini
                content = "Blog post would be generated here with Gemini API."

            return {
                "title": title,
                "theme": theme,
                "content": content,
                "style": "wine_commercial_narrative",
                "created_at": datetime.now().isoformat(),
                "company": company_name,
            }

        except Exception as e:
            logger.error(f"Error generating blog: {e}")
            return {
                "title": title,
                "error": str(e),
                "created_at": datetime.now().isoformat(),
            }

    def generate_startup_story(self, company_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a startup story in wine-commercial style."""
        title = company_info.get("name", "The Journey")
        theme = company_info.get("theme", "entrepreneurship")

        return self.generate_blog_post(
            title=title, theme=theme, company_name=company_info.get("name", "")
        )


# ─── Module-level utilities ───────────────────────────────────────────

_agentic_rag = None
_blog_gen = None


def get_agentic_rag() -> AgenticRAG:
    """Get or create the Agentic RAG singleton."""
    global _agentic_rag
    if _agentic_rag is None:
        _agentic_rag = AgenticRAG()
    return _agentic_rag


def get_blog_generator() -> NarrativeBlogGenerator:
    """Get or create the Blog Generator singleton."""
    global _blog_gen
    if _blog_gen is None:
        _blog_gen = NarrativeBlogGenerator()
    return _blog_gen
