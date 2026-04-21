#!/usr/bin/env python3
"""
BackPocket OS - Twin AI MCP Server
===================================
MCP Server for Gemini/Ollama AI operations.

Handles: email triage, draft generation, client extraction, tone analysis
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import List, Dict, Any

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import existing services
try:
    import services.gemini as gemini_service
except ImportError as e:
    logger.warning(f"Could not import Gemini service: {e}")


# =============================================================================
# MCP Server Implementation
# =============================================================================


class AIMCPServer:
    """MCP Server for BackPocket AI operations."""

    def __init__(self):
        self.gemini = gemini_service

    # =========================================================================
    # TOOL: triage_email
    # =========================================================================
    def triage_email(self, sender: str, subject: str, body: str) -> Dict[str, Any]:
        """Classify an email into tier (1-5) with reasoning.

        Args:
            sender: Email sender address
            subject: Email subject
            body: Email body content

        Returns:
            Tier classification with confidence and reasoning
        """
        try:
            result = self.gemini.triage_email(sender, subject, body)

            if result:
                return {
                    "status": "success",
                    "tier": result.get("tier", "3"),
                    "reasoning": result.get("reasoning", ""),
                    "category": result.get("category", ""),
                    "priority_score": result.get("priority_score", 0),
                }
            else:
                return {"status": "error", "error": "Triage failed"}

        except Exception as e:
            logger.error(f"Error triaging email: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: draft_response
    # =========================================================================
    def draft_response(
        self, sender: str, subject: str, body: str, tier: str = "2"
    ) -> Dict[str, Any]:
        """Generate a draft response to an email.

        Args:
            sender: Email sender address
            subject: Email subject
            body: Email body content
            tier: Tier level (1-5) affecting tone

        Returns:
            Generated draft response
        """
        try:
            result = self.gemini.draft_response(sender, subject, body)

            if result:
                return {
                    "status": "success",
                    "draft": result.get("draft", ""),
                    "tone": result.get("tone", "professional"),
                    "tier": tier,
                }
            else:
                return {"status": "error", "error": "Draft generation failed"}

        except Exception as e:
            logger.error(f"Error drafting response: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: batch_triage
    # =========================================================================
    def batch_triage(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Triage multiple emails in batch.

        Args:
            emails: List of email dictionaries with sender, subject, body

        Returns:
            List of tier classifications
        """
        try:
            results = self.gemini.batch_triage_emails(emails)

            return {"status": "success", "count": len(results), "results": results}

        except Exception as e:
            logger.error(f"Error in batch triage: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: refine_draft
    # =========================================================================
    def refine_draft(self, original_draft: str, feedback: str) -> Dict[str, Any]:
        """Refine a draft based on user feedback.

        Args:
            original_draft: The original draft text
            feedback: User feedback for refinement

        Returns:
            Refined draft
        """
        try:
            result = self.gemini.refine_draft(original_draft, feedback)

            if result:
                return {
                    "status": "success",
                    "refined_draft": result.get("draft", ""),
                    "changes_made": result.get("changes", []),
                }
            else:
                return {"status": "error", "error": "Refinement failed"}

        except Exception as e:
            logger.error(f"Error refining draft: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: analyze_tone
    # =========================================================================
    def analyze_tone(self, text: str) -> Dict[str, Any]:
        """Analyze communication tone of text.

        Args:
            text: Text to analyze

        Returns:
            Tone analysis results
        """
        try:
            result = self.gemini.analyze_tone(text)

            if result:
                return {
                    "status": "success",
                    "tone": result.get("tone", "neutral"),
                    "formality": result.get("formality", "neutral"),
                    "sentiment": result.get("sentiment", "neutral"),
                    "suggestions": result.get("suggestions", []),
                }
            else:
                return {"status": "error", "error": "Tone analysis failed"}

        except Exception as e:
            logger.error(f"Error analyzing tone: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: extract_client_info
    # =========================================================================
    def extract_client_info(self, email_body: str) -> Dict[str, Any]:
        """Extract client information from email.

        Args:
            email_body: Email body text

        Returns:
            Extracted client information
        """
        try:
            result = self.gemini.extract_client_info(email_body)

            if result:
                return {"status": "success", "client": result}
            else:
                return {"status": "error", "error": "Client extraction failed"}

        except Exception as e:
            logger.error(f"Error extracting client: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: summarize_email
    # =========================================================================
    def summarize_email(
        self, subject: str, body: str, max_words: int = 50
    ) -> Dict[str, Any]:
        """Summarize an email.

        Args:
            subject: Email subject
            body: Email body
            max_words: Maximum words in summary

        Returns:
            Email summary
        """
        try:
            prompt = f"""Summarize this email in {max_words} words or less:

Subject: {subject}
Body: {body}

Summary:"""

            # Try Gemini first, then Ollama fallback
            client = self.gemini.get_gemini_client()
            if client:
                response = client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                summary = response.text.strip() if response and response.text else ""
            else:
                summary = self.gemini.get_ollama_response(prompt) or ""

            return {
                "status": "success",
                "summary": summary,
                "word_count": len(summary.split()),
            }

        except Exception as e:
            logger.error(f"Error summarizing email: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: test_gemini_connection
    # =========================================================================
    def test_gemini_connection(self) -> Dict[str, Any]:
        """Test Gemini API connection.

        Returns:
            Connection status
        """
        try:
            result = self.gemini.test_gemini_connection()
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: test_ollama_connection
    # =========================================================================
    def test_ollama_connection(self) -> Dict[str, Any]:
        """Test Ollama local LLM connection.

        Returns:
            Connection status
        """
        try:
            result = self.gemini.get_ollama_response(
                "Say 'Ollama connected'", json_mode=False
            )
            return {
                "status": "success" if result else "error",
                "connected": bool(result),
                "response": result[:100] if result else None,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_client_whitelist
    # =========================================================================
    def get_client_whitelist(self) -> Dict[str, Any]:
        """Get client whitelist for email triage.

        Returns:
            Client emails and domains
        """
        try:
            emails, domains = self.gemini._get_client_whitelist()
            return {
                "status": "success",
                "client_emails": list(emails),
                "client_domains": list(domains),
                "count": len(emails),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_priority_list
    # =========================================================================
    def get_priority_list(self) -> Dict[str, Any]:
        """Get priority list for golden senders.

        Returns:
            Priority list dictionary
        """
        try:
            priority = self.gemini._get_cached_priority_list()
            return {
                "status": "success",
                "priority_list": priority,
                "count": len(priority),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: pre_triage_rules
    # =========================================================================
    def pre_triage_rules(self, sender: str, subject: str) -> Dict[str, Any]:
        """Run pre-triage rules (fast, before AI).

        Args:
            sender: Email sender
            subject: Email subject

        Returns:
            Pre-triage result with tier if matched
        """
        try:
            result = self.gemini.pre_triage_rules(sender, subject)

            if result and result.get("tier"):
                return {
                    "status": "success",
                    "matched": True,
                    "tier": result.get("tier"),
                    "reason": result.get("reason", ""),
                }
            else:
                return {"status": "success", "matched": False, "tier": None}

        except Exception as e:
            logger.error(f"Error in pre-triage: {e}")
            return {"status": "error", "error": str(e)}


# =============================================================================
# MCP Protocol Implementation
# =============================================================================


def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tool call."""
    server = AIMCPServer()

    handlers = {
        "triage_email": lambda: server.triage_email(
            arguments.get("sender", ""),
            arguments.get("subject", ""),
            arguments.get("body", ""),
        ),
        "draft_response": lambda: server.draft_response(
            arguments.get("sender", ""),
            arguments.get("subject", ""),
            arguments.get("body", ""),
            arguments.get("tier", "2"),
        ),
        "batch_triage": lambda: server.batch_triage(arguments.get("emails", [])),
        "refine_draft": lambda: server.refine_draft(
            arguments.get("original_draft", ""), arguments.get("feedback", "")
        ),
        "analyze_tone": lambda: server.analyze_tone(arguments.get("text", "")),
        "extract_client_info": lambda: server.extract_client_info(
            arguments.get("email_body", "")
        ),
        "summarize_email": lambda: server.summarize_email(
            arguments.get("subject", ""),
            arguments.get("body", ""),
            arguments.get("max_words", 50),
        ),
        "test_gemini_connection": server.test_gemini_connection,
        "test_ollama_connection": server.test_ollama_connection,
        "get_client_whitelist": server.get_client_whitelist,
        "get_priority_list": server.get_priority_list,
        "pre_triage_rules": lambda: server.pre_triage_rules(
            arguments.get("sender", ""), arguments.get("subject", "")
        ),
    }

    if tool_name in handlers:
        try:
            return handlers[tool_name]()
        except Exception as e:
            logger.error(f"Error handling {tool_name}: {e}")
            return {"status": "error", "error": str(e)}
    else:
        return {"status": "error", "error": f"Unknown tool: {tool_name}"}


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BackPocket Twin AI MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8003, help="Port to listen on")

    args = parser.parse_args()

    logger.info(f"Starting Twin AI MCP Server on {args.host}:{args.port}")

    server = AIMCPServer()
    result = server.test_gemini_connection()
    logger.info(f"Gemini connection test: {result}")

    print(f"\nMCP Server ready at http://{args.host}:{args.port}")
    print("Use with MCP client - Streamable HTTP transport")
