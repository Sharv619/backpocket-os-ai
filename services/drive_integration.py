"""
Google Drive Integration for BackPocket.

Syncs files from a specified Google Drive folder and makes them available
as context for the RAG system and blog/content generation.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DriveIntegration:
    """Interface with Google Drive to sync folder contents."""

    def __init__(self):
        self.service = self._get_drive_service()

    def _get_drive_service(self):
        """Initialize Google Drive API service."""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            # Try to use credentials from GOOGLE_APPLICATION_CREDENTIALS
            creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if creds_file and os.path.exists(creds_file):
                credentials = service_account.Credentials.from_service_account_file(
                    creds_file, scopes=["https://www.googleapis.com/auth/drive.readonly"]
                )
                service = build("drive", "v3", credentials=credentials)
                logger.info("✓ Google Drive service initialized")
                return service
        except Exception as e:
            logger.warning(f"Drive service not available: {e}")
            return None

    def list_folder_contents(
        self, folder_id: str, file_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """List all files in a Drive folder.

        Args:
            folder_id: Google Drive folder ID
            file_types: Filter by MIME types (e.g., ['application/pdf', 'application/vnd.google-apps.document'])

        Returns:
            List of file metadata dictionaries
        """
        if not self.service:
            logger.error("Drive service not available")
            return []

        try:
            query = f"'{folder_id}' in parents and trashed=false"

            # Add file type filters
            if file_types:
                type_queries = [f"mimeType='{mime}'" for mime in file_types]
                query += f" and ({' or '.join(type_queries)})"

            results = (
                self.service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="files(id, name, mimeType, createdTime, modifiedTime, webViewLink, size)",
                    pageSize=100,
                )
                .execute()
            )

            files = results.get("files", [])
            logger.info(f"✓ Found {len(files)} files in Drive folder")
            return files

        except Exception as e:
            logger.error(f"Error listing Drive folder: {e}")
            return []

    def download_file_content(self, file_id: str, export_mime_type: Optional[str] = None) -> str:
        """Download file content as text.

        Args:
            file_id: Google Drive file ID
            export_mime_type: MIME type for export (e.g., 'text/plain' for Docs)

        Returns:
            File content as string
        """
        if not self.service:
            return ""

        try:
            if export_mime_type:
                # For Google Docs, Sheets, etc. - export as different format
                request = self.service.files().export(
                    fileId=file_id, mimeType=export_mime_type
                )
            else:
                # For regular files - just download
                request = self.service.files().get_media(fileId=file_id)

            content = request.execute()
            if isinstance(content, bytes):
                return content.decode("utf-8", errors="ignore")
            return str(content)

        except Exception as e:
            logger.warning(f"Error downloading file {file_id}: {e}")
            return ""

    def sync_folder_to_rag(
        self, folder_id: str, twin_type: str = "admin"
    ) -> Dict[str, Any]:
        """Sync all files from a Drive folder into the RAG system.

        Args:
            folder_id: Google Drive folder ID to sync
            twin_type: Which twin to ingest files into ('estimator', 'site_manager', 'admin')

        Returns:
            Sync summary
        """
        try:
            from services.agentic_rag import get_agentic_rag

            files = self.list_folder_contents(folder_id)
            rag = get_agentic_rag()

            ingested_count = 0
            for file_info in files:
                try:
                    file_id = file_info.get("id")
                    file_name = file_info.get("name")
                    mime_type = file_info.get("mimeType")

                    # Determine export MIME type for Google docs
                    export_mime = None
                    if mime_type == "application/vnd.google-apps.document":
                        export_mime = "text/plain"
                    elif mime_type == "application/vnd.google-apps.spreadsheet":
                        export_mime = "text/csv"

                    # Download content
                    content = self.download_file_content(file_id, export_mime)
                    if content:
                        # Ingest into RAG
                        metadata = {
                            "source": "drive",
                            "file_name": file_name,
                            "file_id": file_id,
                            "mime_type": mime_type,
                            "ingested_at": datetime.now().isoformat(),
                        }

                        rag.ingest_document_to_rag(twin_type, file_id, content, metadata)
                        ingested_count += 1
                        logger.info(f"✓ Ingested: {file_name}")

                except Exception as e:
                    logger.warning(f"Failed to ingest {file_info.get('name')}: {e}")

            return {
                "folder_id": folder_id,
                "total_files": len(files),
                "ingested": ingested_count,
                "status": "success" if ingested_count > 0 else "no_files_ingested",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error syncing folder: {e}")
            return {"error": str(e), "status": "failed"}


# ─── Module-level utilities ───────────────────────────────────────────

_drive = None


def get_drive_integration() -> DriveIntegration:
    """Get or create the Drive Integration singleton."""
    global _drive
    if _drive is None:
        _drive = DriveIntegration()
    return _drive
