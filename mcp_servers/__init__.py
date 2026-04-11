"""
BackPocket OS - MCP Servers Package
=====================================
"""

from .twin_database_server import DatabaseMCPServer, handle_tool_call as db_handle
from .twin_email_server import EmailMCPServer, handle_tool_call as email_handle
from .twin_ai_server import AIMCPServer, handle_tool_call as ai_handle
from .twin_sheets_server import SheetsMCPServer, handle_tool_call as sheets_handle
from .twin_whatsapp_server import WhatsAppMCPServer, handle_tool_call as wa_handle
from .twin_audit_server import AuditMCPServer, handle_tool_call as audit_handle

__all__ = [
    "DatabaseMCPServer",
    "EmailMCPServer",
    "AIMCPServer",
    "SheetsMCPServer",
    "WhatsAppMCPServer",
    "AuditMCPServer",
    "db_handle",
    "email_handle",
    "ai_handle",
    "sheets_handle",
    "wa_handle",
    "audit_handle",
]

__version__ = "1.0.0"
