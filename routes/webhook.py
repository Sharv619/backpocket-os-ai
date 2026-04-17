import os
import re
import asyncio
import random
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import services.database as db
from services.gmail import send_email
from services.gemini import refine_draft

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/whapi-webhook")
@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    logger.info(f"👉 WEBHOOK ATTEMPT: {request.method} {request.url}")
    loop = asyncio.get_running_loop()
    try:
        raw_body = await request.body()
        logger.info(f"📦 RAW BYTES RECEIVED: {len(raw_body)} bytes")

        # ── HMAC signature verification ───────────────────────────────────
        _webhook_secret = os.getenv("WHAPI_WEBHOOK_SECRET", "")
        if _webhook_secret:
            import hmac as _hmac
            import hashlib as _hashlib

            received_sig = request.headers.get("x-hub-signature-256", "")
            expected_sig = (
                "sha256="
                + _hmac.new(
                    _webhook_secret.encode(), raw_body, _hashlib.sha256
                ).hexdigest()
            )
            if not _hmac.compare_digest(received_sig, expected_sig):
                logger.warning("❌ Webhook HMAC mismatch — request rejected")
                return JSONResponse(
                    status_code=403, content={"detail": "Invalid signature"}
                )
        # ─────────────────────────────────────────────────────────────────

        if raw_body:
            logger.info(f"📦 RAW BODY: {raw_body.decode('utf-8', errors='ignore')}")
        data = await request.json()
        logger.info(f"📦 JSON DATA: {data}")

        messages = data.get("messages", [])
        for msg in messages:
            # Parse text body OR interactive button replies
            text_body = msg.get("text", {}).get("body", "").strip()

            # Check for interactive button replies (Whapi V3)
            interactive = msg.get("interactive", {})
            if interactive.get("type") == "button_reply":
                btn_id = interactive.get("button_reply", {}).get("id", "")
                if btn_id == "ButtonsV3:self_check" or btn_id == "self_check":
                    text_body = "self-check"
                elif btn_id == "ButtonsV3:test_approve" or btn_id == "test_approve":
                    text_body = "approve"
                elif btn_id == "ButtonsV3:test_revise" or btn_id == "test_revise":
                    text_body = "revise"
                else:
                    text_body = btn_id

            if not text_body:
                # Still check if it might be a quick_reply or action
                action = msg.get("action", {}).get("reply", {})
                if action:
                    text_body = (
                        action.get("title", "").strip() or action.get("id", "").strip()
                    )

            if not text_body:
                continue

            sender_phone = msg.get("from", "").split("@")[0]
            founder_phone = "".join(filter(str.isdigit, os.getenv("FOUNDER_PHONE", "")))

            # Only process if from the founder (linked account or specific phone)
            if not sender_phone or sender_phone != founder_phone:
                logger.warning(f"Message from unknown phone: {sender_phone}")
                continue

            from services.whapi import send_whatsapp_message
            import re

            # Flexible parsing: support both 4-digit and YYYY-MM-XXXXX formats
            ID_PATTERN = r"(\d{4}-\d{2}-\d{5}|\d{4})"

            text_body_lower = text_body.lower()

            # --- EXTRACT IDs FROM QUOTED MESSAGE ---
            quoted_text = (
                msg.get("context", {}).get("quoted_content", {}).get("body", "")
            )
            quoted_ids = re.findall(ID_PATTERN, quoted_text) if quoted_text else []

            # 1. SPECIAL CASE: List Pending
            if any(
                kw in text_body_lower for kw in ["pending", "list", "status", "summary"]
            ):
                # But don't trigger if it's a long message
                if len(text_body_lower.split()) < 6:
                    pending_refs = db.get_all_pending_refs()
                    if pending_refs:
                        summary_lines = []
                        for rid in pending_refs:
                            p = db.get_pending_approval(rid)
                            if p:
                                if rid.startswith("FIND-"):
                                    continue
                                summary_lines.append(
                                    f"*#{rid}* — {p.get('subject', 'No Subject')[:50]}"
                                )
                        summary = "\n".join(summary_lines)
                        await loop.run_in_executor(
                            None,
                            send_whatsapp_message,
                            founder_phone,
                            f"🔔 *PENDING APPROVALS:*\n\n{summary}\n\n*QUICK REPLIES:*\n✅ *approve last* - Approve most recent\n✅ *approve 1* - Approve 1st in list\n✅ *approve 00001* (short ref)\n✅ *approve 2026-04-90001* (full)\n\n✏️ *revise last: change tone*",
                        )
                    else:
                        await loop.run_in_executor(
                            None,
                            send_whatsapp_message,
                            founder_phone,
                            "✅ No pending emails right now.",
                        )
                return {"status": "success"}

            # 1.05 SPECIAL CASE: Self-Check / Diagnostic
            if any(
                kw in text_body_lower for kw in ["self-check", "diagnostic", "health"]
            ):
                from services.diagnostics import run_system_diagnostic

                diag = await loop.run_in_executor(None, run_system_diagnostic)
                status_emoji = "✅" if diag["status"] == "healthy" else "⚠️"
                report = f"{status_emoji} *TWIN HEALTH REPORT*\n\n"
                for svc, res in diag["details"].items():
                    res_emoji = "🟢" if res.get("status") == "success" else "🔴"
                    report += (
                        f"{res_emoji} *{svc.upper()}*: {res.get('message', 'Ready')}\n"
                    )

                await loop.run_in_executor(
                    None, send_whatsapp_message, founder_phone, report
                )
                return {"status": "success"}

            # 1.1 SPECIAL CASE: Find/Search
            if text_body_lower.startswith("find "):
                query = text_body[5:].strip()
                from services.gmail import search_emails, get_all_account_tokens

                all_tokens = get_all_account_tokens()

                logger.info(
                    f"🔍 SEARCHING: '{query}' across {len(all_tokens)} accounts..."
                )
                all_matches = []
                for t in all_tokens:
                    matches = await loop.run_in_executor(None, search_emails, query, t)
                    all_matches.extend(matches)

                if not all_matches:
                    await loop.run_in_executor(
                        None,
                        send_whatsapp_message,
                        founder_phone,
                        f"🔍 No emails found for '{query}'.",
                    )
                else:
                    summary_lines = []
                    for i, m in enumerate(all_matches[:5]):  # Top 5
                        search_ref = f"FIND-{random.randint(1000, 9999)}"
                        db.save_pending_approval(
                            search_ref,
                            {
                                "message_id": m["id"],
                                "thread_id": "",
                                "sender": m["sender"],
                                "subject": m["subject"],
                                "draft_body": m["token_file"],
                                "delivered_to": m["token_file"],
                                "tier": "SEARCH",
                            },
                        )
                        summary_lines.append(
                            f"*{search_ref}* — {m['subject'][:40]}\n   _From: {m['sender'][:30]}_"
                        )

                    summary = "\n\n".join(summary_lines)
                    await loop.run_in_executor(
                        None,
                        send_whatsapp_message,
                        founder_phone,
                        f"🔍 Found {len(all_matches)} results for '{query}':\n\n{summary}\n\nReply *get <ID>* to rescue to Inbox.",
                    )
                return {"status": "success"}

            # 2. MULTI-COMMAND PARSING
            keywords = [
                "approve",
                "revise",
                "add",
                "supplier",
                "spam",
                "archive",
                "delete",
                "ignore",
                "get",
            ]
            found_commands = []
            for kw in keywords:
                for match in re.finditer(rf"\b{kw}\b", text_body_lower):
                    found_commands.append({"cmd": kw, "start": match.start()})

            # Sort by position
            found_commands.sort(key=lambda x: x["start"])

            if not found_commands:
                logger.warning(f"No valid keywords found in: {text_body}")
                return {"status": "success"}

            # Get all pending for index/shortcut resolution
            all_pending_refs = db.get_all_pending_refs()

            # Process each command block
            for i in range(len(found_commands)):
                cmd_info = found_commands[i]
                cmd = cmd_info["cmd"]
                start_pos = cmd_info["start"]
                end_pos = (
                    found_commands[i + 1]["start"]
                    if i + 1 < len(found_commands)
                    else len(text_body)
                )

                block_text = text_body[start_pos:end_pos]
                block_ids = re.findall(ID_PATTERN, block_text)

                # CRITICAL: If approve/revise command but NO ref_id, DO NOT proceed
                if cmd in ["approve", "revise"]:
                    if not block_ids:
                        # Try to get from quoted message context
                        block_ids = quoted_ids if quoted_ids else []

                    if not block_ids:
                        # NEW: Try short format (just number) or "last", "1st", "2nd", etc.
                        short_match = re.search(
                            r"\b(last|first|1st|2nd|3rd|\d+)\b", block_text
                        )
                        if short_match:
                            short_val = short_match.group(1).lower()
                            if short_val == "last" or short_val == "first":
                                if all_pending_refs:
                                    block_ids = [
                                        all_pending_refs[0]
                                        if short_val == "last"
                                        else all_pending_refs[-1]
                                    ]
                            elif short_val in ["1st", "1"]:
                                if len(all_pending_refs) >= 1:
                                    block_ids = [all_pending_refs[0]]
                            elif short_val in ["2nd", "2"]:
                                if len(all_pending_refs) >= 2:
                                    block_ids = [all_pending_refs[1]]
                            elif short_val in ["3rd", "3"]:
                                if len(all_pending_refs) >= 3:
                                    block_ids = [all_pending_refs[2]]
                            elif short_val.isdigit():
                                # Match last 4+ digits against pending refs
                                for pref in all_pending_refs:
                                    if pref.endswith(short_val) or pref.endswith(
                                        short_val.zfill(5)
                                    ):
                                        block_ids = [pref]
                                        break

                    if not block_ids:
                        # No ref_id found - send error message, DO NOT send anything
                        await loop.run_in_executor(
                            None,
                            send_whatsapp_message,
                            founder_phone,
                            f"⚠️ *Missing Ref ID*\n\nTo {cmd}, please specify the reference.\n\nExamples:\n*approve 2026-04-00001* (full)\n*approve 00001* (short)\n*approve last* (most recent)\n*approve 1* (1st pending)\n\nType *pending* to see all.",
                        )
                        continue

                if not block_ids:
                    continue

                if not block_ids:
                    continue

                for ref_id in block_ids:
                    info = db.get_pending_approval(ref_id)
                    if not info:
                        continue

                    email_addr = info["sender"]
                    msg_id = info["message_id"]
                    tier = info.get("tier", "1")

                    if cmd == "get" and tier == "SEARCH":
                        from services.gmail import rescue_to_inbox

                        token = info.get(
                            "draft_body", "token.json"
                        )  # We stored token in draft_body for search results
                        res = await loop.run_in_executor(
                            None, rescue_to_inbox, msg_id, token
                        )
                        if res:
                            await loop.run_in_executor(
                                None,
                                send_whatsapp_message,
                                founder_phone,
                                f"⚓ RESCUED: Message back in Inbox ({token}).",
                            )
                            db.delete_pending_approval(ref_id)
                        else:
                            await loop.run_in_executor(
                                None,
                                send_whatsapp_message,
                                founder_phone,
                                f"❌ Rescue failed for {ref_id}.",
                            )
                        continue

                    # (Normal commands like approve, revise, etc below...)

                    # A) APPROVE
                    if cmd == "approve":
                        from_alias = info.get("delivered_to")
                        subject = info["subject"]
                        draft = info["draft_body"]

                        logger.info(f"👍 APPROVAL RECEIVED for Ref #{ref_id}")
                        if from_alias:
                            token_source = "token.json"
                            actual_alias = from_alias
                            if "|" in from_alias:
                                actual_alias, token_source = from_alias.split("|", 1)

                            if token_source.startswith("token_imap_"):
                                from services.imap import send_email_smtp

                                result = await loop.run_in_executor(
                                    None,
                                    send_email_smtp,
                                    token_source,
                                    email_addr,
                                    f"Re: {subject}",
                                    draft,
                                )
                            else:
                                result = await loop.run_in_executor(
                                    None,
                                    send_email,
                                    email_addr,
                                    f"Re: {subject}",
                                    draft,
                                    actual_alias,
                                    token_source,
                                )
                        else:
                            result = await loop.run_in_executor(
                                None, send_email, email_addr, f"Re: {subject}", draft
                            )

                        if result["status"] == "success":
                            from services.google_sheets import log_activity

                            await loop.run_in_executor(
                                None,
                                log_activity,
                                {
                                    "email_address": email_addr,
                                    "status": f"Approved & Sent (#{ref_id})",
                                },
                            )
                            db.log_action(
                                ref_id,
                                "approved",
                                info.get("tier", ""),
                                "Approved via WhatsApp",
                            )
                            db.save_correction(
                                ref_id,
                                "approve",
                                draft,
                                draft,
                                "Approved as-is via WhatsApp",
                                sender=email_addr,
                                subject=info.get("subject", ""),
                            )
                            db.delete_pending_approval(ref_id)
                            await loop.run_in_executor(
                                None,
                                send_whatsapp_message,
                                founder_phone,
                                f"✅ *Ref #{ref_id}* sent to {email_addr}!",
                            )
                        else:
                            await loop.run_in_executor(
                                None,
                                send_whatsapp_message,
                                founder_phone,
                                f"❌ Failed to send Ref #{ref_id}: {result.get('message', 'Unknown error')}",
                            )

                    # B) REVISE
                    elif cmd == "revise":
                        # Extract comment: everything after the ID in this block, or just the whole block if context used
                        comment = ""
                        user_provided_draft = ""

                        # Check if user is providing a direct edit (starts with "Hi " or "Dear " etc)
                        original_block = block_text
                        if ref_id in block_text:
                            after_id = (
                                block_text.split(ref_id, 1)[1]
                                .strip()
                                .lstrip(":")
                                .strip()
                            )
                            # If the content looks like an email (starts with Hi, Dear, Thanks, etc), treat as direct edit
                            if after_id.lower().startswith(
                                (
                                    "hi",
                                    "dear",
                                    "thanks",
                                    "hello",
                                    "best",
                                    "regards",
                                    "warm",
                                )
                            ):
                                user_provided_draft = after_id
                            else:
                                comment = after_id
                        else:
                            after_kw = (
                                block_text.replace(cmd, "", 1)
                                .strip()
                                .lstrip(":")
                                .strip()
                            )
                            if after_kw.lower().startswith(
                                (
                                    "hi",
                                    "dear",
                                    "thanks",
                                    "hello",
                                    "best",
                                    "regards",
                                    "warm",
                                )
                            ):
                                user_provided_draft = after_kw
                            else:
                                comment = after_kw

                        if user_provided_draft:
                            # User provided direct revision - save as-is
                            logger.info(f"✏️ DIRECT REVISION for Ref #{ref_id}")
                            original_draft = info["draft_body"]

                            info["draft_body"] = user_provided_draft
                            db.save_pending_approval(ref_id, info)
                            db.save_correction(
                                ref_id,
                                "revise",
                                original_draft,
                                user_provided_draft,
                                "User direct edit",
                                sender=email_addr,
                                subject=info.get("subject", ""),
                            )
                            db.log_action(
                                ref_id,
                                "revised",
                                info.get("tier", ""),
                                "WhatsApp direct edit",
                            )

                            await loop.run_in_executor(
                                None,
                                send_whatsapp_message,
                                founder_phone,
                                f"✏️ *Ref #{ref_id} UPDATED*\n\n{user_provided_draft}\n\n✅ Reply: *approve {ref_id}* to send",
                            )

                        elif comment:
                            # User gave AI instructions to rewrite
                            logger.info(
                                f"❌ REVISION REQUESTED for Ref #{ref_id}: {comment}"
                            )
                            email_object = {
                                "id": msg_id,
                                "threadId": info["thread_id"],
                                "subject": info["subject"],
                                "sender": email_addr,
                            }
                            original_draft = info["draft_body"]
                            new_draft = await loop.run_in_executor(
                                None,
                                refine_draft,
                                email_object,
                                original_draft,
                                comment,
                            )

                            info["draft_body"] = new_draft
                            db.save_pending_approval(ref_id, info)
                            db.save_correction(
                                ref_id,
                                "revise",
                                original_draft,
                                new_draft,
                                comment,
                                sender=email_addr,
                                subject=info.get("subject", ""),
                            )
                            db.log_action(
                                ref_id,
                                "revised",
                                info.get("tier", ""),
                                f"WhatsApp revision: {comment}",
                            )

                            await loop.run_in_executor(
                                None,
                                send_whatsapp_message,
                                founder_phone,
                                f"✏️ *Ref #{ref_id} REVISED*\n\n{new_draft}\n\n✅ Reply: *approve {ref_id}* to send\n✏️ Or reply with your own version directly",
                            )
                        else:
                            # No instructions - show current draft for editing
                            current_draft = info.get("draft_body", "No draft found")
                            await loop.run_in_executor(
                                None,
                                send_whatsapp_message,
                                founder_phone,
                                f"📝 *Current Draft (Ref #{ref_id}):*\n\n{current_draft}\n\n✏️ *To revise:* Reply with your new version directly, OR\n*revise {ref_id}: make it friendlier* (AI will rewrite)",
                            )

                    # C) SUPPLIER
                    elif cmd == "supplier":
                        logger.info(f"🚚 SUPPLIER CATEGORIZATION for Ref #{ref_id}")
                        from services.google_sheets import log_expense

                        log_data = {
                            "from_name": email_addr.split("@")[0],
                            "email_address": email_addr,
                            "subject": info["subject"],
                            "body": info["draft_body"],
                            "expense_data": {
                                "vendor": email_addr.split("@")[0],
                                "amount": "N/A",
                                "due_date": "N/A",
                            },
                        }
                        await loop.run_in_executor(None, log_expense, log_data)
                        db.delete_pending_approval(ref_id)
                        await loop.run_in_executor(
                            None,
                            send_whatsapp_message,
                            founder_phone,
                            f"🚚 *Ref #{ref_id}* moved to Supplier Expenses.",
                        )

                    # D) SPAM / DELETE / IGNORE
                    elif cmd in ["spam", "delete", "ignore"]:
                        logger.info(f"🗑️ DISCARDING Ref #{ref_id} (Cmd: {cmd})")
                        db.delete_pending_approval(ref_id)
                        db.mark_as_processed(msg_id)  # Prevent re-triage
                        await loop.run_in_executor(
                            None,
                            send_whatsapp_message,
                            founder_phone,
                            f"🗑️ *Ref #{ref_id}* marked as {cmd} and removed.",
                        )

                    # E) ARCHIVE
                    elif cmd == "archive":
                        logger.info(f"🗄️ ARCHIVING Ref #{ref_id}")
                        db.delete_pending_approval(ref_id)
                        await loop.run_in_executor(
                            None,
                            send_whatsapp_message,
                            founder_phone,
                            f"🗄️ *Ref #{ref_id}* archived and removed from list.",
                        )

                    # F) GET (Rescue from Archive/Trash)
                    elif cmd == "get":
                        logger.info(f"⚓ RESCUING Ref #{ref_id}")
                        token_file = info.get("delivered_to", "token.json")
                        if "|" in token_file:
                            token_file = token_file.split("|", 1)[1]

                        from services.gmail import rescue_to_inbox

                        result = await loop.run_in_executor(
                            None, rescue_to_inbox, msg_id, token_file
                        )
                        if result:
                            db.delete_pending_approval(ref_id)
                            await loop.run_in_executor(
                                None,
                                send_whatsapp_message,
                                founder_phone,
                                f"⚓ *Ref #{ref_id}* restored to Inbox & marked Unread! (Acct: {token_file})",
                            )
                        else:
                            await loop.run_in_executor(
                                None,
                                send_whatsapp_message,
                                founder_phone,
                                f"❌ Failed to rescue Ref #{ref_id}.",
                            )

                    # G) ADD (Manual Whitelist)
                    elif cmd == "add":
                        logger.info(f"🆕 WHITELISTING Ref #{ref_id}")
                        from services.google_sheets import add_new_client_to_master

                        onboard_data = {
                            "from_name": info.get("sender", "").split("@")[0],
                            "email_address": email_addr,
                            "subject": info["subject"],
                            "body": "Manual Whitelist Approval",
                            "to_email": info.get("delivered_to", "unknown"),
                        }
                        await loop.run_in_executor(
                            None, add_new_client_to_master, onboard_data
                        )
                        await loop.run_in_executor(
                            None,
                            send_whatsapp_message,
                            founder_phone,
                            f"✅ *Ref #{ref_id}* Whitelisted! {email_addr} added to BPS_Client_Master as Tier 1.",
                        )

            return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

