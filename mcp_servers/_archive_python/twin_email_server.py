#!/usr/bin/env python3
"""
BackPocket OS - Twin Email MCP Server
======================================
MCP Server for Gmail and IMAP email operations.

Handles: fetching emails, sending drafts, searching, archiving
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import Optional, Dict, Any

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import existing services
try:
    import services.gmail as gmail_service
    import services.imap as imap_service
except ImportError as e:
    logger.warning(f"Could not import email services: {e}")


# =============================================================================
# MCP Server Implementation
# =============================================================================


class EmailMCPServer:
    """MCP Server for BackPocket email operations."""

    def __init__(self):
        self.gmail_service = gmail_service
        self.imap_service = imap_service

    # =========================================================================
    # TOOL: fetch_gmail_emails
    # =========================================================================
    def fetch_gmail_emails(
        self, max_results: int = 10, query: str = "is:unread"
    ) -> Dict[str, Any]:
        """Fetch emails from Gmail.

        Args:
            max_results: Maximum number of emails to fetch
            query: Gmail search query (default: unread emails)

        Returns:
            List of emails with headers, snippets, and metadata
        """
        try:
            service = self.gmail_service.get_gmail_service()
            if not service:
                return {"status": "error", "error": "Gmail service not available"}

            results = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])
            emails = []

            for msg in messages:
                msg_data = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="full")
                    .execute()
                )

                headers = msg_data.get("headers", [])
                subject = next(
                    (h["value"] for h in headers if h["name"] == "Subject"), ""
                )
                sender = next((h["value"] for h in headers if h["name"] == "From"), "")
                date = next((h["value"] for h in headers if h["name"] == "Date"), "")

                emails.append(
                    {
                        "message_id": msg_data["id"],
                        "thread_id": msg_data.get("threadId", ""),
                        "subject": subject,
                        "sender": sender,
                        "date": date,
                        "snippet": msg_data.get("snippet", ""),
                        "label_ids": msg_data.get("labelIds", []),
                        "internal_date": msg_data.get("internalDate", ""),
                    }
                )

            return {
                "status": "success",
                "count": len(emails),
                "emails": emails,
                "query": query,
            }

        except Exception as e:
            logger.error(f"Error fetching Gmail emails: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: fetch_imap_emails
    # =========================================================================
    def fetch_imap_emails(
        self, account_config: str, max_results: int = 10
    ) -> Dict[str, Any]:
        """Fetch emails from IMAP account.

        Args:
            account_config: Path to account config JSON or account name
            max_results: Maximum number of emails to fetch

        Returns:
            List of emails from IMAP account
        """
        try:
            if hasattr(self.imap_service, "fetch_emails"):
                result = self.imap_service.fetch_emails(
                    account_config=account_config, max_results=max_results
                )
                return {"status": "success", **result}
            else:
                return {"status": "error", "error": "IMAP service not available"}

        except Exception as e:
            logger.error(f"Error fetching IMAP emails: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: send_email
    # =========================================================================
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send an email via Gmail API.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (can be HTML)
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            thread_id: Optional thread ID for reply

        Returns:
            Success status with message ID
        """
        try:
            result = self.gmail_service.send_email(
                to=to, subject=subject, body=body, cc=cc, bcc=bcc, thread_id=thread_id
            )

            if result.get("status") == "sent":
                return {
                    "status": "success",
                    "message_id": result.get("message_id"),
                    "to": to,
                    "subject": subject,
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "Unknown error"),
                }

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: send_draft
    # =========================================================================
    def send_draft(self, ref_id: str) -> Dict[str, Any]:
        """Send a pending draft by ref_id.

        Args:
            ref_id: Reference ID of the pending approval

        Returns:
            Success status with message ID
        """
        try:
            # Import database module
            import services.database as db

            # Get the pending approval
            conn = sqlite3.connect(db.DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT sender, subject, draft_body, thread_id 
                FROM pending_approvals 
                WHERE ref_id = ?
            """,
                (ref_id,),
            )

            row = cursor.fetchone()
            if not row:
                conn.close()
                return {"status": "error", "error": f"Pending {ref_id} not found"}

            sender, subject, draft_body, thread_id = row
            conn.close()

            # Send the email
            result = self.send_email(
                to=sender, subject=subject, body=draft_body, thread_id=thread_id
            )

            if result.get("status") == "success":
                # Update status in database
                conn = sqlite3.connect(db.DB_PATH)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE pending_approvals 
                    SET status = 'approved' 
                    WHERE ref_id = ?
                """,
                    (ref_id,),
                )
                conn.commit()
                conn.close()

                return {
                    "status": "success",
                    "ref_id": ref_id,
                    "message_id": result.get("message_id"),
                }

            return result

        except Exception as e:
            logger.error(f"Error sending draft: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: search_emails
    # =========================================================================
    def search_emails(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        """Search emails in Gmail.

        Args:
            query: Gmail search query
            max_results: Maximum number of results

        Returns:
            List of matching emails
        """
        try:
            return self.fetch_gmail_emails(max_results=max_results, query=query)

        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: archive_email
    # =========================================================================
    def archive_email(self, message_id: str) -> Dict[str, Any]:
        """Archive an email (remove from inbox, keep in All Mail).

        Args:
            message_id: Gmail message ID

        Returns:
            Success status
        """
        try:
            service = self.gmail_service.get_gmail_service()
            if not service:
                return {"status": "error", "error": "Gmail service not available"}

            # Remove INBOX label, add ARCHIVE label implicitly
            service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["INBOX"]}
            ).execute()

            return {"status": "success", "message_id": message_id, "action": "archived"}

        except Exception as e:
            logger.error(f"Error archiving email: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: trash_email
    # =========================================================================
    def trash_email(self, message_id: str) -> Dict[str, Any]:
        """Move an email to trash.

        Args:
            message_id: Gmail message ID

        Returns:
            Success status
        """
        try:
            service = self.gmail_service.get_gmail_service()
            if not service:
                return {"status": "error", "error": "Gmail service not available"}

            service.users().messages().trash(userId="me", id=message_id).execute()

            return {"status": "success", "message_id": message_id, "action": "trashed"}

        except Exception as e:
            logger.error(f"Error trashing email: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_email_details
    # =========================================================================
    def get_email_details(self, message_id: str) -> Dict[str, Any]:
        """Get full details of an email.

        Args:
            message_id: Gmail message ID

        Returns:
            Full email details including body
        """
        try:
            service = self.gmail_service.get_gmail_service()
            if not service:
                return {"status": "error", "error": "Gmail service not available"}

            msg = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            headers = msg.get("headers", [])

            return {
                "status": "success",
                "message_id": msg["id"],
                "thread_id": msg.get("threadId", ""),
                "subject": next(
                    (h["value"] for h in headers if h["name"] == "Subject"), ""
                ),
                "sender": next(
                    (h["value"] for h in headers if h["name"] == "From"), ""
                ),
                "to": next((h["value"] for h in headers if h["name"] == "To"), ""),
                "date": next((h["value"] for h in headers if h["name"] == "Date"), ""),
                "snippet": msg.get("snippet", ""),
                "label_ids": msg.get("labelIds", []),
                "internal_date": msg.get("internalDate", ""),
            }

        except Exception as e:
            logger.error(f"Error getting email details: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_all_account_tokens
    # =========================================================================
    def get_all_account_tokens(self) -> Dict[str, Any]:
        """Get list of all configured email accounts.

        Returns:
            List of account token files
        """
        try:
            tokens = self.gmail_service.get_all_account_tokens()
            return {"status": "success", "accounts": tokens, "count": len(tokens)}
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: test_gmail_connection
    # =========================================================================
    def test_gmail_connection(self) -> Dict[str, Any]:
        """Test Gmail API connection.

        Returns:
            Connection status and details
        """
        try:
            result = self.gmail_service.test_gmail_connection()
            return {"status": "success" if result else "error", "connected": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# =============================================================================
# MCP Protocol Implementation
# =============================================================================


def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tool call."""
    server = EmailMCPServer()

    handlers = {
        "fetch_gmail_emails": lambda: server.fetch_gmail_emails(
            arguments.get("max_results", 10), arguments.get("query", "is:unread")
        ),
        "fetch_imap_emails": lambda: server.fetch_imap_emails(
            arguments.get("account_config", ""), arguments.get("max_results", 10)
        ),
        "send_email": lambda: server.send_email(
            arguments.get("to", ""),
            arguments.get("subject", ""),
            arguments.get("body", ""),
            arguments.get("cc"),
            arguments.get("bcc"),
            arguments.get("thread_id"),
        ),
        "send_draft": lambda: server.send_draft(arguments.get("ref_id", "")),
        "search_emails": lambda: server.search_emails(
            arguments.get("query", ""), arguments.get("max_results", 20)
        ),
        "archive_email": lambda: server.archive_email(arguments.get("message_id", "")),
        "trash_email": lambda: server.trash_email(arguments.get("message_id", "")),
        "get_email_details": lambda: server.get_email_details(
            arguments.get("message_id", "")
        ),
        "get_all_account_tokens": server.get_all_account_tokens,
        "test_gmail_connection": server.test_gmail_connection,
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

    parser = argparse.ArgumentParser(description="BackPocket Twin Email MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8002, help="Port to listen on")

    args = parser.parse_args()

    logger.info(f"Starting Twin Email MCP Server on {args.host}:{args.port}")

    server = EmailMCPServer()
    result = server.test_gmail_connection()
    logger.info(f"Gmail connection test: {result}")

    print(f"\nMCP Server ready at http://{args.host}:{args.port}")
    print("Use with MCP client - Streamable HTTP transport")
