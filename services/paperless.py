import os
import requests
import time
import logging

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("PAPERLESS_URL", "http://localhost:8010")
TOKEN = os.getenv("PAPERLESS_TOKEN", "")

if not TOKEN:
    logger.warning("PAPERLESS_TOKEN is not set. Paperless-ngx integration will be disabled.")

def _get_headers():
    return {"Authorization": f"Token {TOKEN}"}

def upload_document(file_bytes, filename, title=None, document_type=None):
    """Uploads a document and returns the task ID."""
    if not TOKEN:
        return {"error": "Paperless not configured"}
    
    url = f"{BASE_URL}/api/documents/post_document/"
    files = {'document': (filename, file_bytes)}
    data = {}
    if title:
        data['title'] = title
    if document_type:
        # We need to get the ID for the document type name
        doc_type_id = get_document_type_id_by_name(document_type)
        if doc_type_id:
            data['document_type'] = doc_type_id

    try:
        response = requests.post(url, headers=_get_headers(), files=files, data=data, timeout=30)
        response.raise_for_status()
        task_id = response.json()
        return {"task_id": task_id}
    except requests.exceptions.RequestException as e:
        logger.error(f"Paperless upload failed: {e}")
        return {"error": str(e)}

def get_task_status(task_id):
    """Polls for the status of a task and returns the related document ID on success."""
    if not TOKEN:
        return {"error": "Paperless not configured"}
        
    url = f"{BASE_URL}/api/tasks/?task_id={task_id}"
    try:
        response = requests.get(url, headers=_get_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            task_info = data["results"][0]
            if task_info["status"] == "SUCCESS":
                return {"status": "SUCCESS", "document_id": task_info.get("related_document")}
            elif task_info["status"] == "FAILURE":
                return {"status": "FAILURE", "error": task_info.get("result")}
            else:
                return {"status": task_info["status"]}
        return {"status": "PENDING"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get task status: {e}")
        return {"error": str(e)}

def get_document(document_id, poll_retries=10, poll_interval=2):
    """
    Waits for a document to be ready and fetches its details, including OCR'd content.
    This is useful for getting content immediately after upload.
    """
    if not TOKEN:
        return {"error": "Paperless not configured"}

    url = f"{BASE_URL}/api/documents/{document_id}/"
    for _ in range(poll_retries):
        try:
            response = requests.get(url, headers=_get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('content'):
                    return data
            time.sleep(poll_interval)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return {"error": str(e)}
    return {"error": "Polling timed out, document not ready."}

def list_documents(page=1, page_size=25, query=""):
    """Lists documents from Paperless."""
    if not TOKEN:
        return {"error": "Paperless not configured"}

    url = f"{BASE_URL}/api/documents/?page={page}&page_size={page_size}&query={query}"
    try:
        response = requests.get(url, headers=_get_headers(), timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def download_document(document_id):
    """Downloads the original document file."""
    if not TOKEN:
        return None
    url = f"{BASE_URL}/api/documents/{document_id}/download/"
    try:
        response = requests.get(url, headers=_get_headers(), timeout=30)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException:
        return None

# Helper functions for metadata
def list_correspondents():
    return _list_metadata_endpoint("correspondents")

def list_document_types():
    return _list_metadata_endpoint("document_types")

def list_tags():
    return _list_metadata_endpoint("tags")

def _list_metadata_endpoint(endpoint):
    if not TOKEN: return []
    url = f"{BASE_URL}/api/{endpoint}/"
    try:
        response = requests.get(url, headers=_get_headers(), timeout=10)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.exceptions.RequestException:
        return []

def get_document_type_id_by_name(name):
    """Finds a document type ID by its name."""
    doc_types = list_document_types()
    for dt in doc_types:
        if dt.get("name", "").lower() == name.lower():
            return dt.get("id")
    return None
