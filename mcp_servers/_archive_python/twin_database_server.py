#!/usr/bin/env python3
"""
BackPocket OS - Twin Database MCP Server
=========================================
MCP Server for SQLite database operations in BackPocket OS.

Handles: pending approvals, corrections, action history, instructions, sessions
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import logging
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_PATH = "backpocket.db"

# =============================================================================
# MCP Server Implementation
# =============================================================================


class DatabaseMCPServer:
    """MCP Server for BackPocket database operations."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Ensure database exists, create if not."""
        if not os.path.exists(self.db_path):
            # Import and run init from original database module
            import services.database as db_module

            db_module.init_db()
            logger.info(f"Created new database at {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper settings."""
        conn = sqlite3.connect(self.db_path, timeout=20)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    # =========================================================================
    # TOOL: list_tables
    # =========================================================================
    def list_tables(self) -> Dict[str, Any]:
        """List all tables in the database with their row counts.

        Returns:
            Dictionary with table names and row counts
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)

            tables = []
            for row in cursor.fetchall():
                table_name = row["name"]
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = cursor.fetchone()["count"]
                tables.append({"name": table_name, "row_count": count})

            conn.close()
            return {"status": "success", "tables": tables}

        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: query_pending
    # =========================================================================
    def query_pending(self, status: str = "pending", limit: int = 50) -> Dict[str, Any]:
        """Get pending approvals from the database.

        Args:
            status: Filter by status (pending, approved, revised, archived)
            limit: Maximum number of results

        Returns:
            List of pending approvals
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT ref_id, message_id, sender, subject, draft_body, 
                       tier, status, created_at, delivered_to
                FROM pending_approvals
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (status, limit),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "ref_id": row["ref_id"],
                        "message_id": row["message_id"],
                        "sender": row["sender"],
                        "subject": row["subject"],
                        "draft_body": row["draft_body"],
                        "tier": row["tier"],
                        "status": row["status"],
                        "created_at": row["created_at"],
                        "delivered_to": row["delivered_to"],
                    }
                )

            conn.close()
            return {"status": "success", "count": len(results), "pending": results}

        except Exception as e:
            logger.error(f"Error querying pending: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_pending_by_ref
    # =========================================================================
    def get_pending_by_ref(self, ref_id: str) -> Dict[str, Any]:
        """Get a specific pending approval by ref_id.

        Args:
            ref_id: The reference ID (e.g., '2026-04-00001')

        Returns:
            The pending approval record
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM pending_approvals WHERE ref_id = ?
            """,
                (ref_id,),
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return {"status": "success", "pending": dict(row)}
            else:
                return {
                    "status": "error",
                    "error": f"Pending approval {ref_id} not found",
                }

        except Exception as e:
            logger.error(f"Error getting pending by ref: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: create_pending
    # =========================================================================
    def create_pending(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pending approval.

        Args:
            data: Dictionary with pending approval data

        Required fields: ref_id, sender, subject, tier
        Optional: message_id, thread_id, draft_body, delivered_to
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO pending_approvals 
                (ref_id, message_id, thread_id, sender, subject, draft_body, 
                 delivered_to, tier, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
                (
                    data.get("ref_id"),
                    data.get("message_id", ""),
                    data.get("thread_id", ""),
                    data.get("sender"),
                    data.get("subject"),
                    data.get("draft_body", ""),
                    data.get("delivered_to", ""),
                    data.get("tier", "3"),
                ),
            )

            conn.commit()
            conn.close()

            return {"status": "success", "ref_id": data.get("ref_id")}

        except sqlite3.IntegrityError:
            return {
                "status": "error",
                "error": f"Ref ID {data.get('ref_id')} already exists",
            }
        except Exception as e:
            logger.error(f"Error creating pending: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: update_pending_status
    # =========================================================================
    def update_pending_status(
        self, ref_id: str, status: str, feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update the status of a pending approval.

        Args:
            ref_id: The reference ID
            status: New status (approved, revised, archived, trashed)
            feedback: Optional feedback for revisions

        Returns:
            Success or error status
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE pending_approvals 
                SET status = ? 
                WHERE ref_id = ?
            """,
                (status, ref_id),
            )

            if cursor.rowcount == 0:
                conn.close()
                return {"status": "error", "error": f"Ref ID {ref_id} not found"}

            # If there's feedback, also update draft_body
            if feedback and status == "revised":
                cursor.execute(
                    """
                    UPDATE pending_approvals 
                    SET draft_body = ? 
                    WHERE ref_id = ?
                """,
                    (feedback, ref_id),
                )

            conn.commit()
            conn.close()

            return {"status": "success", "ref_id": ref_id, "new_status": status}

        except Exception as e:
            logger.error(f"Error updating pending status: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_corrections
    # =========================================================================
    def get_corrections(self, limit: int = 20) -> Dict[str, Any]:
        """Get user corrections (feedback on drafts).

        Args:
            limit: Maximum number of results

        Returns:
            List of corrections
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM corrections
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            results = []
            for row in cursor.fetchall():
                results.append(dict(row))

            conn.close()
            return {"status": "success", "count": len(results), "corrections": results}

        except Exception as e:
            logger.error(f"Error getting corrections: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: add_correction
    # =========================================================================
    def add_correction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new correction/feedback.

        Args:
            data: Dictionary with correction data
            Required: ref_id, correction_type, original_draft
            Optional: corrected_draft, feedback, sender, subject
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO corrections 
                (ref_id, correction_type, sender, subject, original_draft, 
                 corrected_draft, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data.get("ref_id"),
                    data.get("correction_type", "revise"),
                    data.get("sender", ""),
                    data.get("subject", ""),
                    data.get("original_draft", ""),
                    data.get("corrected_draft", ""),
                    data.get("feedback", ""),
                ),
            )

            conn.commit()
            correction_id = cursor.lastrowid
            conn.close()

            return {"status": "success", "correction_id": correction_id}

        except Exception as e:
            logger.error(f"Error adding correction: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: log_action
    # =========================================================================
    def log_action(
        self, ref_id: str, action: str, tier: str = "", notes: str = ""
    ) -> Dict[str, Any]:
        """Log an action to the action_history table.

        Args:
            ref_id: Reference ID of the item
            action: Action taken (approved, revised, archived, trashed)
            tier: Tier level (1-5)
            notes: Optional notes

        Returns:
            Success status with action ID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO action_history (ref_id, action, tier, notes)
                VALUES (?, ?, ?, ?)
            """,
                (ref_id, action, tier, notes),
            )

            conn.commit()
            action_id = cursor.lastrowid
            conn.close()

            return {"status": "success", "action_id": action_id, "ref_id": ref_id}

        except Exception as e:
            logger.error(f"Error logging action: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_action_history
    # =========================================================================
    def get_action_history(self, limit: int = 50) -> Dict[str, Any]:
        """Get action history.

        Args:
            limit: Maximum number of results

        Returns:
            List of actions
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM action_history
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            results = []
            for row in cursor.fetchall():
                results.append(dict(row))

            conn.close()
            return {"status": "success", "count": len(results), "history": results}

        except Exception as e:
            logger.error(f"Error getting action history: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_instructions
    # =========================================================================
    def get_instructions(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get Twin instructions.

        Args:
            category: Optional category filter

        Returns:
            List of instructions
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if category:
                cursor.execute(
                    """
                    SELECT * FROM instructions 
                    WHERE category = ?
                    ORDER BY priority DESC
                """,
                    (category,),
                )
            else:
                cursor.execute("""
                    SELECT * FROM instructions 
                    ORDER BY priority DESC
                """)

            results = []
            for row in cursor.fetchall():
                results.append(dict(row))

            conn.close()
            return {"status": "success", "count": len(results), "instructions": results}

        except Exception as e:
            logger.error(f"Error getting instructions: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: add_instruction
    # =========================================================================
    def add_instruction(
        self, instruction_text: str, category: str = "general", priority: int = 5
    ) -> Dict[str, Any]:
        """Add a new Twin instruction.

        Args:
            instruction_text: The instruction text
            category: Category (general, email, triage, etc.)
            priority: Priority level (1-10)

        Returns:
            Success status with instruction ID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO instructions (instruction_text, category, priority)
                VALUES (?, ?, ?)
            """,
                (instruction_text, category, priority),
            )

            conn.commit()
            instruction_id = cursor.lastrowid
            conn.close()

            return {"status": "success", "instruction_id": instruction_id}

        except Exception as e:
            logger.error(f"Error adding instruction: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_sessions
    # =========================================================================
    def get_sessions(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent chat sessions.

        Args:
            limit: Maximum number of sessions

        Returns:
            List of sessions
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if session_log table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='session_log'
            """)

            if not cursor.fetchone():
                conn.close()
                return {
                    "status": "success",
                    "count": 0,
                    "sessions": [],
                    "note": "No session_log table",
                }

            cursor.execute(
                """
                SELECT * FROM session_log
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            results = []
            for row in cursor.fetchall():
                results.append(dict(row))

            conn.close()
            return {"status": "success", "count": len(results), "sessions": results}

        except Exception as e:
            logger.error(f"Error getting sessions: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_sender_instructions
    # =========================================================================
    def get_sender_instructions(self, email: Optional[str] = None) -> Dict[str, Any]:
        """Get sender-specific instructions.

        Args:
            email: Optional email filter

        Returns:
            List of sender instructions
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if email:
                cursor.execute(
                    """
                    SELECT * FROM sender_instructions 
                    WHERE sender_email = ?
                """,
                    (email,),
                )
            else:
                cursor.execute("""
                    SELECT * FROM sender_instructions
                """)

            results = []
            for row in cursor.fetchall():
                results.append(dict(row))

            conn.close()
            return {
                "status": "success",
                "count": len(results),
                "sender_instructions": results,
            }

        except Exception as e:
            logger.error(f"Error getting sender instructions: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: add_sender_instruction
    # =========================================================================
    def add_sender_instruction(
        self, sender_email: str, instructions: str, category: str = "client"
    ) -> Dict[str, Any]:
        """Add sender-specific instruction.

        Args:
            sender_email: Email address of sender
            instructions: Instructions for this sender
            category: Category (client, supplier, builder, etc.)

        Returns:
            Success status
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO sender_instructions 
                (sender_email, instructions, category)
                VALUES (?, ?, ?)
            """,
                (sender_email, instructions, category),
            )

            conn.commit()
            conn.close()

            return {"status": "success", "sender_email": sender_email}

        except Exception as e:
            logger.error(f"Error adding sender instruction: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # TOOL: get_stats
    # =========================================================================
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Statistics about the database
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            stats = {}

            # Pending count by status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM pending_approvals 
                GROUP BY status
            """)
            stats["pending_by_status"] = {
                row["status"]: row["count"] for row in cursor.fetchall()
            }

            # Pending count by tier
            cursor.execute("""
                SELECT tier, COUNT(*) as count 
                FROM pending_approvals 
                GROUP BY tier
            """)
            stats["pending_by_tier"] = {
                row["tier"]: row["count"] for row in cursor.fetchall()
            }

            # Action history count
            cursor.execute("SELECT COUNT(*) as count FROM action_history")
            stats["total_actions"] = cursor.fetchone()["count"]

            # Corrections count
            cursor.execute("SELECT COUNT(*) as count FROM corrections")
            stats["total_corrections"] = cursor.fetchone()["count"]

            # Instructions count
            cursor.execute("SELECT COUNT(*) as count FROM instructions")
            stats["total_instructions"] = cursor.fetchone["count"]

            conn.close()
            return {"status": "success", "stats": stats}

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"status": "error", "error": str(e)}


# =============================================================================
# MCP Protocol Implementation (Streamable HTTP)
# =============================================================================


def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tool call."""
    server = DatabaseMCPServer()

    # Route to appropriate method
    handlers = {
        "list_tables": server.list_tables,
        "query_pending": lambda: server.query_pending(
            arguments.get("status", "pending"), arguments.get("limit", 50)
        ),
        "get_pending_by_ref": lambda: server.get_pending_by_ref(
            arguments.get("ref_id", "")
        ),
        "create_pending": lambda: server.create_pending(arguments),
        "update_pending_status": lambda: server.update_pending_status(
            arguments.get("ref_id", ""),
            arguments.get("status", ""),
            arguments.get("feedback"),
        ),
        "get_corrections": lambda: server.get_corrections(arguments.get("limit", 20)),
        "add_correction": lambda: server.add_correction(arguments),
        "log_action": lambda: server.log_action(
            arguments.get("ref_id", ""),
            arguments.get("action", ""),
            arguments.get("tier", ""),
            arguments.get("notes", ""),
        ),
        "get_action_history": lambda: server.get_action_history(
            arguments.get("limit", 50)
        ),
        "get_instructions": lambda: server.get_instructions(arguments.get("category")),
        "add_instruction": lambda: server.add_instruction(
            arguments.get("instruction_text", ""),
            arguments.get("category", "general"),
            arguments.get("priority", 5),
        ),
        "get_sessions": lambda: server.get_sessions(arguments.get("limit", 10)),
        "get_sender_instructions": lambda: server.get_sender_instructions(
            arguments.get("email")
        ),
        "add_sender_instruction": lambda: server.add_sender_instruction(
            arguments.get("sender_email", ""),
            arguments.get("instructions", ""),
            arguments.get("category", "client"),
        ),
        "get_stats": server.get_stats,
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

    parser = argparse.ArgumentParser(description="BackPocket Twin Database MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to listen on")
    parser.add_argument("--db-path", default=DB_PATH, help="Path to database")

    args = parser.parse_args()

    logger.info(f"Starting Twin Database MCP Server on {args.host}:{args.port}")
    logger.info(f"Database path: {args.db_path}")

    # For now, just run a quick test
    server = DatabaseMCPServer(args.db_path)
    result = server.list_tables()
    logger.info(f"Database tables: {result}")

    print(f"\nMCP Server ready at http://{args.host}:{args.port}")
    print("Use with MCP client - Streamable HTTP transport")
