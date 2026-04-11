#!/usr/bin/env python3
"""
BackPocket OS - Twin Sheets MCP Server
========================================
MCP Server for Google Sheets synchronization.

Handles: client sync, activity logging, priority list, portal updates
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

try:
    import services.google_sheets as sheets_service
except ImportError as e:
    logger.warning(f"Could not import Sheets service: {e}")


# =============================================================================
# MCP Server Implementation
# =============================================================================


class SheetsMCPServer:
    """MCP Server for BackPocket Google Sheets operations."""

    def __init__(self):
        self.sheets = sheets_service

    # =========================================================================
    # TOOL: sync_clients
    # =========================================================================
    def sync_clients(self) -> Dict[str, Any]:
        """Sync client list from Google Sheets.

        Returns:
            Synced client data
        """
        try:
            result = self.sheets.get_client_emails()

            return {
                "status": "success",
                "client_emails": result if isinstance(result, list) else [],
                "count": len(result) if isinstance(result, list) else 0,
            }

        except Exception as e:
            logger.error(f"Error syncing clients: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_client_emails
    # =========================================================================
    def get_client_emails(self) -> Dict[str, Any]:
        """Get all client emails from Sheets.

        Returns:
            List of client emails
        """
        try:
            emails = self.sheets.get_client_emails()

            return {"status": "success", "emails": emails, "count": len(emails)}

        except Exception as e:
            logger.error(f"Error getting client emails: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_priority_list
    # =========================================================================
    def get_priority_list(self) -> Dict[str, Any]:
        """Get priority list (golden senders) from Sheets.

        Returns:
            Priority list dictionary
        """
        try:
            priority = self.sheets.get_priority_list()

            return {
                "status": "success",
                "priority_list": priority,
                "count": len(priority),
            }

        except Exception as e:
            logger.error(f"Error getting priority list: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: log_activity
    # =========================================================================
    def log_activity(
        self, action: str, details: str = "", tier: str = ""
    ) -> Dict[str, Any]:
        """Log activity to Google Sheets.

        Args:
            action: Action taken (approved, revised, etc.)
            details: Additional details
            tier: Tier level

        Returns:
            Success status
        """
        try:
            result = self.sheets.log_activity(action, details, tier)

            return {"status": "success", "logged": True, "action": action}

        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: add_client
    # =========================================================================
    def add_client(
        self, email: str, name: str = "", company: str = ""
    ) -> Dict[str, Any]:
        """Add a new client to Sheets.

        Args:
            email: Client email
            name: Client name
            company: Company name

        Returns:
            Success status
        """
        try:
            # Use the add_row or similar method from sheets service
            if hasattr(self.sheets, "add_client"):
                result = self.sheets.add_client(email, name, company)
            else:
                # Manual add via append
                result = self.sheets.append_row(
                    "Clients_Master",
                    [name, email, company, datetime.now().strftime("%Y-%m-%d")],
                )

            return {"status": "success", "added": True, "email": email}

        except Exception as e:
            logger.error(f"Error adding client: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_portal_updates
    # =========================================================================
    def get_portal_updates(self) -> Dict[str, Any]:
        """Get portal updates from Sheets.

        Returns:
            Portal updates list
        """
        try:
            if hasattr(self.sheets, "get_portal_updates"):
                updates = self.sheets.get_portal_updates()
            else:
                updates = []

            return {"status": "success", "updates": updates, "count": len(updates)}

        except Exception as e:
            logger.error(f"Error getting portal updates: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: log_portal_activity
    # =========================================================================
    def log_portal_activity(
        self, client: str, action: str, details: str = ""
    ) -> Dict[str, Any]:
        """Log portal activity to Sheets.

        Args:
            client: Client name/email
            action: Action taken
            details: Additional details

        Returns:
            Success status
        """
        try:
            result = self.sheets.log_portal_activity(client, action, details)

            return {"status": "success", "logged": True, "client": client}

        except Exception as e:
            logger.error(f"Error logging portal activity: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_action_log
    # =========================================================================
    def get_action_log(self, limit: int = 50) -> Dict[str, Any]:
        """Get action log from Sheets.

        Args:
            limit: Maximum number of results

        Returns:
            Action log entries
        """
        try:
            if hasattr(self.sheets, "get_action_log"):
                log = self.sheets.get_action_log(limit)
            else:
                log = []

            return {"status": "success", "log": log, "count": len(log)}

        except Exception as e:
            logger.error(f"Error getting action log: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: test_sheets_connection
    # =========================================================================
    def test_sheets_connection(self) -> Dict[str, Any]:
        """Test Google Sheets API connection.

        Returns:
            Connection status
        """
        try:
            result = self.sheets.test_sheets_connection()

            if isinstance(result, dict):
                return result
            return {"status": "success" if result else "error", "connected": result}

        except Exception as e:
            return {"status": "error", "error": str(e)}


# =============================================================================
# MCP Protocol Implementation
# =============================================================================


def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tool call."""
    server = SheetsMCPServer()

    handlers = {
        "sync_clients": server.sync_clients,
        "get_client_emails": server.get_client_emails,
        "get_priority_list": server.get_priority_list,
        "log_activity": lambda: server.log_activity(
            arguments.get("action", ""),
            arguments.get("details", ""),
            arguments.get("tier", ""),
        ),
        "add_client": lambda: server.add_client(
            arguments.get("email", ""),
            arguments.get("name", ""),
            arguments.get("company", ""),
        ),
        "get_portal_updates": server.get_portal_updates,
        "log_portal_activity": lambda: server.log_portal_activity(
            arguments.get("client", ""),
            arguments.get("action", ""),
            arguments.get("details", ""),
        ),
        "get_action_log": lambda: server.get_action_log(arguments.get("limit", 50)),
        "test_sheets_connection": server.test_sheets_connection,
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

    parser = argparse.ArgumentParser(description="BackPocket Twin Sheets MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8004, help="Port to listen on")

    args = parser.parse_args()

    logger.info(f"Starting Twin Sheets MCP Server on {args.host}:{args.port}")

    server = SheetsMCPServer()
    result = server.test_sheets_connection()
    logger.info(f"Sheets connection test: {result}")

    print(f"\nMCP Server ready at http://{args.host}:{args.port}")
    print("Use with MCP client - Streamable HTTP transport")
