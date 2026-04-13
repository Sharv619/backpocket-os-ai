#!/usr/bin/env python3
"""
BackPocket OS - MCP Server Runner
==================================
Main entry point for running all MCP servers with Streamable HTTP transport.

Usage:
    python mcp_servers/run_mcp_servers.py --port 8000
    python mcp_servers/run_mcp_servers.py --port 8000 --server database
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
from typing import Dict, Any
import json
import asyncio

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import MCP servers
from twin_database_server import DatabaseMCPServer
from twin_email_server import EmailMCPServer
from twin_ai_server import AIMCPServer
from twin_sheets_server import SheetsMCPServer
from twin_whatsapp_server import WhatsAppMCPServer
from twin_audit_server import AuditMCPServer


# =============================================================================
# MCP Server Registry
# =============================================================================


class MCPServerRegistry:
    """Registry of all MCP servers."""

    def __init__(self):
        self.servers = {
            "database": DatabaseMCPServer(),
            "email": EmailMCPServer(),
            "ai": AIMCPServer(),
            "sheets": SheetsMCPServer(),
            "whatsapp": WhatsAppMCPServer(),
            "audit": AuditMCPServer(),
        }

    def get_server(self, name: str):
        """Get server by name."""
        return self.servers.get(name)

    def list_servers(self):
        """List all available servers."""
        return list(self.servers.keys())

    def get_all_tools(self) -> Dict[str, Any]:
        """Get all tools from all servers."""
        tools = {}

        # Database tools
        tools["list_tables"] = {
            "description": "List all tables in the database with row counts",
            "parameters": {},
        }
        tools["query_pending"] = {
            "description": "Get pending approvals from database",
            "parameters": {"status": "string", "limit": "integer"},
        }
        tools["get_pending_by_ref"] = {
            "description": "Get specific pending approval by ref_id",
            "parameters": {"ref_id": "string"},
        }
        tools["create_pending"] = {
            "description": "Create new pending approval",
            "parameters": {
                "ref_id": "string",
                "sender": "string",
                "subject": "string",
                "tier": "string",
            },
        }
        tools["update_pending_status"] = {
            "description": "Update status of pending approval",
            "parameters": {
                "ref_id": "string",
                "status": "string",
                "feedback": "string",
            },
        }
        tools["get_corrections"] = {
            "description": "Get user corrections",
            "parameters": {"limit": "integer"},
        }
        tools["add_correction"] = {
            "description": "Add new correction/feedback",
            "parameters": {
                "ref_id": "string",
                "correction_type": "string",
                "original_draft": "string",
            },
        }
        tools["log_action"] = {
            "description": "Log action to history",
            "parameters": {"ref_id": "string", "action": "string", "tier": "string"},
        }
        tools["get_action_history"] = {
            "description": "Get action history",
            "parameters": {"limit": "integer"},
        }
        tools["get_instructions"] = {
            "description": "Get Twin instructions",
            "parameters": {"category": "string"},
        }
        tools["add_instruction"] = {
            "description": "Add new Twin instruction",
            "parameters": {
                "instruction_text": "string",
                "category": "string",
                "priority": "integer",
            },
        }
        tools["get_sender_instructions"] = {
            "description": "Get sender-specific instructions",
            "parameters": {"email": "string"},
        }
        tools["add_sender_instruction"] = {
            "description": "Add sender-specific instruction",
            "parameters": {
                "sender_email": "string",
                "instructions": "string",
                "category": "string",
            },
        }
        tools["get_stats"] = {
            "description": "Get database statistics",
            "parameters": {},
        }

        # Email tools
        tools["fetch_gmail_emails"] = {
            "description": "Fetch emails from Gmail",
            "parameters": {"max_results": "integer", "query": "string"},
        }
        tools["fetch_imap_emails"] = {
            "description": "Fetch emails from IMAP account",
            "parameters": {"account_config": "string", "max_results": "integer"},
        }
        tools["send_email"] = {
            "description": "Send email via Gmail API",
            "parameters": {
                "to": "string",
                "subject": "string",
                "body": "string",
                "cc": "string",
            },
        }
        tools["send_draft"] = {
            "description": "Send pending draft by ref_id",
            "parameters": {"ref_id": "string"},
        }
        tools["search_emails"] = {
            "description": "Search emails in Gmail",
            "parameters": {"query": "string", "max_results": "integer"},
        }
        tools["archive_email"] = {
            "description": "Archive email (remove from inbox)",
            "parameters": {"message_id": "string"},
        }
        tools["trash_email"] = {
            "description": "Move email to trash",
            "parameters": {"message_id": "string"},
        }
        tools["get_email_details"] = {
            "description": "Get full details of an email",
            "parameters": {"message_id": "string"},
        }
        tools["test_gmail_connection"] = {
            "description": "Test Gmail API connection",
            "parameters": {},
        }

        # AI tools
        tools["triage_email"] = {
            "description": "Classify email into tier (1-5)",
            "parameters": {"sender": "string", "subject": "string", "body": "string"},
        }
        tools["draft_response"] = {
            "description": "Generate draft response to email",
            "parameters": {
                "sender": "string",
                "subject": "string",
                "body": "string",
                "tier": "string",
            },
        }
        tools["batch_triage"] = {
            "description": "Triage multiple emails in batch",
            "parameters": {"emails": "array"},
        }
        tools["refine_draft"] = {
            "description": "Refine draft based on feedback",
            "parameters": {"original_draft": "string", "feedback": "string"},
        }
        tools["analyze_tone"] = {
            "description": "Analyze communication tone",
            "parameters": {"text": "string"},
        }
        tools["extract_client_info"] = {
            "description": "Extract client information from email",
            "parameters": {"email_body": "string"},
        }
        tools["summarize_email"] = {
            "description": "Summarize an email",
            "parameters": {
                "subject": "string",
                "body": "string",
                "max_words": "integer",
            },
        }
        tools["test_gemini_connection"] = {
            "description": "Test Gemini API connection",
            "parameters": {},
        }
        tools["test_ollama_connection"] = {
            "description": "Test Ollama local LLM connection",
            "parameters": {},
        }
        tools["get_client_whitelist"] = {
            "description": "Get client whitelist for triage",
            "parameters": {},
        }
        tools["get_priority_list"] = {
            "description": "Get priority list (golden senders)",
            "parameters": {},
        }

        # Sheets tools
        tools["sync_clients"] = {
            "description": "Sync client list from Google Sheets",
            "parameters": {},
        }
        tools["get_client_emails"] = {
            "description": "Get all client emails from Sheets",
            "parameters": {},
        }
        tools["get_priority_list_from_sheets"] = {
            "description": "Get priority list from Sheets",
            "parameters": {},
        }
        tools["log_activity"] = {
            "description": "Log activity to Sheets",
            "parameters": {"action": "string", "details": "string", "tier": "string"},
        }
        tools["add_client"] = {
            "description": "Add new client to Sheets",
            "parameters": {"email": "string", "name": "string", "company": "string"},
        }
        tools["test_sheets_connection"] = {
            "description": "Test Google Sheets API connection",
            "parameters": {},
        }

        # WhatsApp tools
        tools["send_notification"] = {
            "description": "Send WhatsApp notification",
            "parameters": {"to": "string", "message": "string", "media_url": "string"},
        }
        tools["send_urgent_alert"] = {
            "description": "Send urgent email alert",
            "parameters": {
                "subject": "string",
                "sender": "string",
                "action_needed": "string",
            },
        }
        tools["send_approval_confirmation"] = {
            "description": "Send approval confirmation",
            "parameters": {"ref_id": "string", "subject": "string"},
        }
        tools["send_revision_request"] = {
            "description": "Send revision request",
            "parameters": {
                "ref_id": "string",
                "subject": "string",
                "feedback": "string",
            },
        }
        tools["send_daily_summary"] = {
            "description": "Send daily summary",
            "parameters": {"stats": "object"},
        }
        tools["handle_webhook"] = {
            "description": "Handle incoming WhatsApp webhook",
            "parameters": {"payload": "object"},
        }
        tools["process_button_reply"] = {
            "description": "Process button reply (approve/revise)",
            "parameters": {"button_text": "string", "message_id": "string"},
        }
        tools["test_whapi_connection"] = {
            "description": "Test WhatsApp API connection",
            "parameters": {},
        }

        # Audit tools
        tools["run_self_check"] = {
            "description": "Run system self-check",
            "parameters": {},
        }
        tools["run_local_audit"] = {
            "description": "Run comprehensive audit",
            "parameters": {},
        }
        tools["get_diagnostics"] = {
            "description": "Get system diagnostics",
            "parameters": {},
        }
        tools["check_database"] = {
            "description": "Check database connectivity",
            "parameters": {},
        }
        tools["check_api_keys"] = {
            "description": "Check API keys configuration",
            "parameters": {},
        }
        tools["check_error_logs"] = {
            "description": "Check recent error logs",
            "parameters": {"hours": "integer"},
        }
        tools["get_system_status"] = {
            "description": "Get overall system status",
            "parameters": {},
        }
        tools["get_uptime_stats"] = {
            "description": "Get uptime statistics",
            "parameters": {},
        }

        return tools


# =============================================================================
# FastAPI MCP Server (Streamable HTTP)
# =============================================================================

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    import uvicorn

    app = FastAPI(title="BackPocket MCP Server")
    registry = MCPServerRegistry()

    @app.get("/")
    async def root():
        return {
            "name": "BackPocket MCP Server",
            "version": "1.0.0",
            "servers": registry.list_servers(),
            "tools_count": len(registry.get_all_tools()),
        }

    @app.get("/tools")
    async def list_tools():
        return registry.get_all_tools()

    @app.post("/tools/{server_name}/{tool_name}")
    async def call_tool(server_name: str, tool_name: str, request: Request):
        """Call a tool on a specific server."""
        body = await request.json()

        server = registry.get_server(server_name)
        if not server:
            return JSONResponse(
                status_code=404, content={"error": f"Server {server_name} not found"}
            )

        # Get the appropriate handler
        handlers = {
            "database": db_handle,
            "email": email_handle,
            "ai": ai_handle,
            "sheets": sheets_handle,
            "whatsapp": wa_handle,
            "audit": audit_handle,
        }

        handler = handlers.get(server_name)
        if not handler:
            return JSONResponse(
                status_code=404,
                content={"error": f"Handler for {server_name} not found"},
            )

        try:
            result = handler(tool_name, body)
            return result
        except Exception as e:
            logger.error(f"Error calling {tool_name} on {server_name}: {e}")
            return JSONResponse(status_code=500, content={"error": str(e)})

    @app.get("/health")
    async def health():
        return {"status": "healthy", "servers": registry.list_servers()}

    def run_server(port: int = 8000, host: str = "127.0.0.1"):
        """Run the MCP server."""
        logger.info(f"Starting BackPocket MCP Server on {host}:{port}")
        uvicorn.run(app, host=host, port=port, log_level="info")

except ImportError:
    # Fallback if FastAPI not available
    def run_server(port: int = 8000, host: str = "127.0.0.1"):
        print(f"\n⚠️ FastAPI not installed. Installing...")
        import subprocess

        subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])
        print("\nPlease run: python mcp_servers/run_mcp_servers.py again")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BackPocket MCP Server Runner")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument(
        "--server",
        choices=["all", "database", "email", "ai", "sheets", "whatsapp", "audit"],
        default="all",
        help="Which server to run",
    )

    args = parser.parse_args()

    if args.server == "all":
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║           BackPocket OS - MCP Server Suite                      ║
╠══════════════════════════════════════════════════════════════════╣
║  Servers: database, email, ai, sheets, whatsapp, audit         ║
║  Tools: 60+ tools across all servers                            ║
║  Transport: Streamable HTTP                                     ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        run_server(port=args.port, host=args.host)
    else:
        print(f"Starting {args.server} MCP server on {args.host}:{args.port}")
        run_server(port=args.port, host=args.host)
