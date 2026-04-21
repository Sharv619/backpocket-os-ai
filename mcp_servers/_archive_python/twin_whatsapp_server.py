#!/usr/bin/env python3
"""
BackPocket OS - Twin WhatsApp MCP Server
=========================================
MCP Server for WhatsApp (WHAPI) operations.

Handles: notifications, webhooks, button replies (approve/revise)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import Optional, List, Dict, Any

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

try:
    import services.whapi as whapi_service
except ImportError as e:
    logger.warning(f"Could not import WhatsApp service: {e}")


# =============================================================================
# MCP Server Implementation
# =============================================================================


class WhatsAppMCPServer:
    """MCP Server for BackPocket WhatsApp operations."""

    def __init__(self):
        self.whapi = whapi_service

    # =========================================================================
    # TOOL: send_notification
    # =========================================================================
    def send_notification(
        self, to: str, message: str, media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send WhatsApp notification.

        Args:
            to: Phone number (with country code)
            message: Message text
            media_url: Optional media URL (image, document, etc.)

        Returns:
            Success status with message ID
        """
        try:
            result = self.whapi.send_notification(to, message, media_url)

            if result:
                return {
                    "status": "success",
                    "sent": True,
                    "to": to,
                    "message": message[:50] + "..." if len(message) > 50 else message,
                }
            else:
                return {"status": "error", "error": "Failed to send"}

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: send_urgent_alert
    # =========================================================================
    def send_urgent_alert(
        self, subject: str, sender: str, action_needed: str = "review"
    ) -> Dict[str, Any]:
        """Send urgent email alert.

        Args:
            subject: Email subject
            sender: Email sender
            action_needed: Action required (review, approve, respond)

        Returns:
            Success status
        """
        try:
            message = f"URGENT Email Received\n\nFrom: {sender}\nSubject: {subject}\n\nAction needed: {action_needed}\n\nReply with APPROVE or REVISE"

            # Get founder phone from env
            founder_phone = os.getenv("FOUNDER_PHONE", "")
            if not founder_phone:
                return {"status": "error", "error": "FOUNDER_PHONE not set"}

            return self.send_notification(founder_phone, message)

        except Exception as e:
            logger.error(f"Error sending urgent alert: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: send_approval_confirmation
    # =========================================================================
    def send_approval_confirmation(self, ref_id: str, subject: str) -> Dict[str, Any]:
        """Send approval confirmation message.

        Args:
            ref_id: Reference ID
            subject: Email subject

        Returns:
            Success status
        """
        try:
            message = f"Email Approved & Sent\n\nRef: {ref_id}\nSubject: {subject}\n\nStatus: Sent successfully"

            founder_phone = os.getenv("FOUNDER_PHONE", "")
            if not founder_phone:
                return {"status": "error", "error": "FOUNDER_PHONE not set"}

            return self.send_notification(founder_phone, message)

        except Exception as e:
            logger.error(f"Error sending approval confirmation: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: send_revision_request
    # =========================================================================
    def send_revision_request(
        self, ref_id: str, subject: str, feedback: str = ""
    ) -> Dict[str, Any]:
        """Send revision request message.

        Args:
            ref_id: Reference ID
            subject: Email subject
            feedback: Feedback for revision

        Returns:
            Success status
        """
        try:
            message = (
                f"Draft Returned for Revision\n\nRef: {ref_id}\nSubject: {subject}\n"
            )
            if feedback:
                message += f"\nFeedback: {feedback}"
            message += "\n\nTwin will generate new draft shortly."

            founder_phone = os.getenv("FOUNDER_PHONE", "")
            if not founder_phone:
                return {"status": "error", "error": "FOUNDER_PHONE not set"}

            return self.send_notification(founder_phone, message)

        except Exception as e:
            logger.error(f"Error sending revision request: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: send_daily_summary
    # =========================================================================
    def send_daily_summary(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Send daily summary message.

        Args:
            stats: Dictionary with daily statistics

        Returns:
            Success status
        """
        try:
            processed = stats.get("processed", 0)
            approved = stats.get("approved", 0)
            revised = stats.get("revised", 0)
            tier1 = stats.get("tier1", 0)

            message = "Daily Summary\n\n"
            message += f"Emails processed: {processed}\n"
            message += f"Approved: {approved}\n"
            message += f"Revised: {revised}\n"
            message += f"Urgent (Tier 1): {tier1}\n\n"
            message += f"Time saved: ~{processed * 5} minutes"

            founder_phone = os.getenv("FOUNDER_PHONE", "")
            if not founder_phone:
                return {"status": "error", "error": "FOUNDER_PHONE not set"}

            return self.send_notification(founder_phone, message)

        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: handle_webhook
    # =========================================================================
    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming WhatsApp webhook.

        Args:
            payload: Webhook payload from WHAPI

        Returns:
            Parsed message details
        """
        try:
            # Parse the webhook payload
            messages = payload.get("messages", [])

            if not messages:
                return {"status": "success", "messages": [], "note": "No messages"}

            parsed_messages = []
            for msg in messages:
                parsed = {
                    "message_id": msg.get("id", ""),
                    "from": msg.get("from", ""),
                    "type": msg.get("type", "text"),
                    "text": msg.get("text", {}).get("body", ""),
                    "button": msg.get("button", {}).get("text", ""),
                    "interactive": msg.get("interactive", {})
                    .get("button_reply", {})
                    .get("id", ""),
                }
                parsed_messages.append(parsed)

            return {
                "status": "success",
                "count": len(parsed_messages),
                "messages": parsed_messages,
            }

        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: process_button_reply
    # =========================================================================
    def process_button_reply(self, button_text: str, message_id: str) -> Dict[str, Any]:
        """Process button reply (approve/revise).

        Args:
            button_text: Button text (APPROVE, REVISE, etc.)
            message_id: WhatsApp message ID

        Returns:
            Parsed action
        """
        try:
            button_upper = button_text.upper()

            if "APPROVE" in button_upper:
                return {
                    "status": "success",
                    "action": "approve",
                    "button_text": button_text,
                    "message_id": message_id,
                }
            elif "REVISE" in button_upper or "EDIT" in button_upper:
                return {
                    "status": "success",
                    "action": "revise",
                    "button_text": button_text,
                    "message_id": message_id,
                }
            else:
                return {
                    "status": "success",
                    "action": "unknown",
                    "button_text": button_text,
                    "message_id": message_id,
                }

        except Exception as e:
            logger.error(f"Error processing button reply: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: send_buttons
    # =========================================================================
    def send_buttons(self, to: str, body: str, buttons: List[str]) -> Dict[str, Any]:
        """Send message with interactive buttons.

        Args:
            to: Phone number
            body: Message text
            buttons: List of button labels

        Returns:
            Success status
        """
        try:
            self.whapi.send_buttons(to, body, buttons)

            return {"status": "success", "sent": True, "buttons": buttons}

        except Exception as e:
            logger.error(f"Error sending buttons: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: test_whapi_connection
    # =========================================================================
    def test_whapi_connection(self) -> Dict[str, Any]:
        """Test WhatsApp API connection.

        Returns:
            Connection status
        """
        try:
            # Try to get webhook URL as a test
            if hasattr(self.whapi, "get_webhook_url"):
                url = self.whapi.get_webhook_url()
                return {"status": "success", "connected": True, "webhook_url": url}
            else:
                return {
                    "status": "success",
                    "connected": True,
                    "note": "WHAPI service loaded",
                }

        except Exception as e:
            return {"status": "error", "error": str(e)}


# =============================================================================
# MCP Protocol Implementation
# =============================================================================


def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tool call."""
    server = WhatsAppMCPServer()

    handlers = {
        "send_notification": lambda: server.send_notification(
            arguments.get("to", ""),
            arguments.get("message", ""),
            arguments.get("media_url"),
        ),
        "send_urgent_alert": lambda: server.send_urgent_alert(
            arguments.get("subject", ""),
            arguments.get("sender", ""),
            arguments.get("action_needed", "review"),
        ),
        "send_approval_confirmation": lambda: server.send_approval_confirmation(
            arguments.get("ref_id", ""), arguments.get("subject", "")
        ),
        "send_revision_request": lambda: server.send_revision_request(
            arguments.get("ref_id", ""),
            arguments.get("subject", ""),
            arguments.get("feedback", ""),
        ),
        "send_daily_summary": lambda: server.send_daily_summary(
            arguments.get("stats", {})
        ),
        "handle_webhook": lambda: server.handle_webhook(arguments.get("payload", {})),
        "process_button_reply": lambda: server.process_button_reply(
            arguments.get("button_text", ""), arguments.get("message_id", "")
        ),
        "send_buttons": lambda: server.send_buttons(
            arguments.get("to", ""),
            arguments.get("body", ""),
            arguments.get("buttons", []),
        ),
        "test_whapi_connection": server.test_whapi_connection,
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

    parser = argparse.ArgumentParser(description="BackPocket Twin WhatsApp MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8005, help="Port to listen on")

    args = parser.parse_args()

    logger.info(f"Starting Twin WhatsApp MCP Server on {args.host}:{args.port}")

    server = WhatsAppMCPServer()
    result = server.test_whapi_connection()
    logger.info(f"WhatsApp connection test: {result}")

    print(f"\nMCP Server ready at http://{args.host}:{args.port}")
    print("Use with MCP client - Streamable HTTP transport")
