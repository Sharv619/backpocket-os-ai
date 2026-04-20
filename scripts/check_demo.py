import uuid
import asyncio
import json

# Import DB utilities
import services.database as db

# Initialize DB (creates tables if needed)
db.init_db()

# Create a dummy pending approval entry
ref_id = f"test-{uuid.uuid4().hex[:8]}"
pending_data = {
    "message_id": f"msg-{uuid.uuid4().hex[:8]}",
    "thread_id": f"thr-{uuid.uuid4().hex[:8]}",
    "sender": "alice@example.com",
    "subject": "Quote request for kitchen remodel",
    "draft_body": "Dear Alice, here's the draft...",
    "delivered_to": "alice@example.com",
    "tier": "2",
    "workflow_stage": "2",  # simulate being in Draft stage
}

saved = db.save_pending_approval(ref_id, pending_data)
print(f"Saved pending approval? {saved}, ref_id={ref_id}")

# Verify pending approvals list
all_refs = db.get_all_pending_refs()
print(f"All pending refs: {all_refs}")

# Retrieve the pending approval record
record = db.get_pending_approval(ref_id)
print(f"Record retrieved: {record}")

# Import the async endpoint function
from routes.utilities import get_current_workflow_stage

async def run_stage():
    result = await get_current_workflow_stage()
    print("Current workflow stage endpoint response:", json.dumps(result, indent=2))

asyncio.run(run_stage())

# Extract emails (sender) from all pending approvals
emails = []
for r in all_refs:
    rec = db.get_pending_approval(r)
    if rec:
        emails.append({"ref_id": r, "sender": rec.get("sender"), "subject": rec.get("subject")})
print("Extracted email entries:", json.dumps(emails, indent=2))
