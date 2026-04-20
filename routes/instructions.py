import logging
from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/sops")
async def get_sops(category: str = None):
    try:
        from services.memory import get_sops, get_sop_categories

        sops = get_sops(category=category)
        categories = get_sop_categories()
        return {"sops": sops, "categories": categories}
    except Exception as e:
        logger.error(f"Get SOPs error: {e}")
        return {"sops": [], "categories": [], "error": str(e)}


@router.get("/api/instructions")
async def get_instructions():
    try:
        from services.twin_brain import get_all_instructions, get_sender_instructions

        general = get_all_instructions()
        sender = get_sender_instructions()
        return {
            "general_instructions": general,
            "sender_instructions": sender,
            "total": len(general) + len(sender),
        }
    except Exception as e:
        logger.error(f"Get instructions error: {e}")
        return {"general_instructions": [], "sender_instructions": [], "error": str(e)}


@router.post("/api/instructions")
async def save_instruction(request: Request):
    try:
        from services.database import save_instruction

        data = await request.json()
        result = save_instruction(
            instruction_text=data.get("instruction_text"),
            category=data.get("category", "general"),
            target=data.get("target", ""),
            target_type=data.get("target_type", ""),
            is_critical=data.get("is_critical", False),
            is_active=data.get("is_active", True),
            description=data.get("description", ""),
        )
        return {"status": "success", "id": result}
    except Exception as e:
        logger.error(f"Save instruction error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/api/instructions/promote")
async def promote_instruction(request: Request):
    """
    Promotes a one-off correction or feedback into a permanent rule (Fixes Amnesia).
    """
    try:
        from services.database import save_instruction

        data = await request.json()
        instruction_text = data.get("instruction_text")
        
        if not instruction_text:
            return {"status": "error", "message": "Instruction text is required"}

        # Promote it by saving it to the instructions table
        result = save_instruction(
            instruction_text=instruction_text,
            category=data.get("category", "learned_pattern"),
            target=data.get("ref_id", ""),
            target_type="promotion",
            is_critical=True, # Promoted rules from Steve are treated as critical
            is_active=True,
            description="Learned automatically from user feedback"
        )
        return {"status": "success", "message": "Instruction permanently promoted", "id": result}
    except Exception as e:
        logger.error(f"Promote instruction error: {e}")
        return {"status": "error", "message": str(e)}


@router.put("/api/instructions/{instruction_id}")
async def update_instruction(instruction_id: int, request: Request):
    try:
        from services.database import (
            update_instruction,
            save_revision,
            get_instructions,
        )

        data = await request.json()

        current = get_instructions()
        old_instruction = None
        for inst in current:
            if inst.get("id") == instruction_id:
                old_instruction = inst
                break

        if old_instruction:
            changes = {"old": old_instruction, "new": data}
            save_revision(instruction_id, changes, action="update")

        update_instruction(
            instruction_id,
            instruction_text=data.get("instruction_text"),
            category=data.get("category"),
            is_critical=data.get("is_critical"),
            is_active=data.get("is_active"),
        )
        return {
            "status": "success",
            "message": "Instruction updated with revision history saved",
        }
    except Exception as e:
        logger.error(f"Update instruction error: {e}")
        return {"status": "error", "message": str(e)}


@router.delete("/api/instructions/{instruction_id}")
async def delete_instruction(instruction_id: int):
    try:
        from services.database import (
            delete_instruction,
            save_revision,
            get_instructions,
        )

        current = get_instructions()
        old_instruction = None
        for inst in current:
            if inst.get("id") == instruction_id:
                old_instruction = inst
                break

        if old_instruction:
            changes = {"old": old_instruction, "new": None, "action": "deleted"}
            save_revision(instruction_id, changes, action="delete")

        delete_instruction(instruction_id)
        return {
            "status": "success",
            "message": "Instruction deleted (can be recovered from revisions)",
        }
    except Exception as e:
        logger.error(f"Delete instruction error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/api/instructions/{instruction_id}/revisions")
async def get_instruction_revisions(instruction_id: int):
    try:
        from services.database import get_revisions

        revisions = get_revisions(instruction_id=instruction_id, limit=20)
        return {"revisions": revisions}
    except Exception as e:
        logger.error(f"Get revisions error: {e}")
        return {"revisions": [], "error": str(e)}


@router.post("/api/instructions/{instruction_id}/restore")
async def restore_instruction(instruction_id: int, request: Request):
    try:
        from services.database import save_instruction

        data = await request.json()
        revision_data = data.get("revision_data")

        if not revision_data:
            return {"status": "error", "message": "No revision data provided"}

        result = save_instruction(
            instruction_text=revision_data.get("instruction_text"),
            category=revision_data.get("category", "general"),
            target=revision_data.get("target", ""),
            target_type=revision_data.get("target_type", ""),
            is_critical=revision_data.get("is_critical", False),
            is_active=True,
            description=revision_data.get("description", ""),
        )

        return {
            "status": "success",
            "id": result,
            "message": "Instruction restored from revision",
        }
    except Exception as e:
        logger.error(f"Restore instruction error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/api/sops/categories")
async def get_sop_categories():
    try:
        from services.memory import get_sop_categories

        categories = get_sop_categories()
        return {"categories": categories}
    except Exception as e:
        return {"categories": [], "error": str(e)}


@router.get("/api/sops/search")
async def search_sops(q: str = ""):
    try:
        from services.memory import search_sops

        results = search_sops(q)
        return {"results": results, "count": len(results)}
    except Exception as e:
        return {"results": [], "error": str(e)}


@router.get("/api/sops/{sop_id}")
async def get_sop(sop_id: int):
    try:
        from services.memory import get_sops

        sops = get_sops()
        for sop in sops:
            if sop.get("id") == sop_id:
                return {"sop": sop}
        return {"sop": None, "error": "SOP not found"}
    except Exception as e:
        return {"sop": None, "error": str(e)}
