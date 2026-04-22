import os
import asyncio
import logging
from datetime import datetime

import services.database as db
from services.gemini import pre_triage_rules, batch_triage_emails
from services.self_check import run_self_check

logger = logging.getLogger(__name__)

LAST_PATROL_TIME = "Syncing..."
SCHEDULE_JOBS_DONE = set()


async def inbox_polling_loop():
    """SUPERVISOR: Background loop to poll Gmail with bulletproof error recovery."""
    consecutive_errors = 0
    while True:
        try:
            await inbox_polling_loop_once()
            consecutive_errors = 0  # Reset on success
            await asyncio.sleep(60)
        except Exception as e:
            consecutive_errors += 1
            import traceback

            logger.error(
                f"🚨 SUPERVISOR CAUGHT ERROR in polling: {e}\n{traceback.format_exc()}"
            )

            # Smart backoff: sleep longer if it keeps failing
            backoff_time = min(300, 60 * consecutive_errors)
            logger.warning(
                f"Rebooting patrol task in {backoff_time}s (Error count: {consecutive_errors})"
            )
            await asyncio.sleep(backoff_time)


async def inbox_polling_loop_once():
    """Patrols ALL connected business accounts and performs Zen Cleanup/Admin logic."""
    loop = asyncio.get_running_loop()
    try:
        logger.info("🛡️ GLOBAL POLL: Starting Patrol...")

        from services.google_sheets import process_lead_conversions
        from services.gmail import get_all_account_tokens, get_unread_emails
        from services.imap import get_all_imap_configs, get_unread_emails_imap

        # 🟢 CRM Duty: Sync Lead Conversions
        await loop.run_in_executor(None, process_lead_conversions)

        # 🟢 Marketing Duty: Run Social Media Scheduler
        from services.marketing.scheduler import run_scheduler_tick
        await loop.run_in_executor(None, run_scheduler_tick)

        # 🧠 Self-Awareness: Check for nudges (Urgent emails pending > 4h)
        await loop.run_in_executor(None, run_self_check)

        # 🔄 WhatsApp Retry Engine
        # (It can be implemented later on whatsapp_service.resend_failed())

        all_gmail_tokens = get_all_account_tokens()
        all_imap_tokens = get_all_imap_configs()

        all_accounts = [{"file": t, "type": "gmail"} for t in all_gmail_tokens] + [
            {"file": t, "type": "imap"} for t in all_imap_tokens
        ]

        # 🕵️ ACCOUNT PATROL (Concurrent 4x Speed)
        async def fetch_acc(acc):
            t_file, a_type = acc["file"], acc["type"]
            logger.info(f"🕵️ PATROLLING Account: {t_file} ({a_type})")
            if a_type == "gmail":
                return (
                    await loop.run_in_executor(None, get_unread_emails, t_file),
                    t_file,
                    a_type,
                )
            return (
                await loop.run_in_executor(None, get_unread_emails_imap, t_file),
                t_file,
                a_type,
            )

        account_results = await asyncio.gather(*(fetch_acc(a) for a in all_accounts))

        all_emails_to_triage = []
        for unread_emails, t_file, a_type in account_results:
            for email in unread_emails:
                msg_id = email.get("id")
                if not msg_id or db.is_processed(msg_id):
                    continue

                email["token_file"], email["acc_type"] = t_file, a_type

                pre_triage = pre_triage_rules(email)
                if pre_triage:
                    logger.info(
                        f"🛡️ PRE-FILTER: {email.get('subject')[:30]}... (Tier {pre_triage['tier']})"
                    )
                    await process_triaged_email(email, pre_triage, loop)
                    db.mark_as_processed(msg_id)
                else:
                    all_emails_to_triage.append(email)

        # --- IF NOISE FILTER — strip auto-replies/newsletters before triage AI call ---
        if len(all_emails_to_triage) >= 6:
            try:
                from services.if_filter import IFFilter
                all_emails_to_triage, _if_diag = IFFilter.filter_emails_for_twin(
                    all_emails_to_triage,
                    text_key="snippet",
                    top_n=len(all_emails_to_triage),  # keep all inliers, just drop outliers
                )
                logger.info(f"🔬 IF pre-filter: {_if_diag}")
            except Exception as _e:
                logger.debug(f"IF filter skipped: {_e}")

        # --- BATCH TRIAGE REMAINING (HUGE COST SAVINGS) ---
        if all_emails_to_triage:
            logger.info(
                f"🧠 BATCH TRIAGE: Processing {len(all_emails_to_triage)} emails..."
            )

            # Using while loop to avoid potential slicing issues in some static analysis
            idx = 0
            while idx < len(all_emails_to_triage):
                batch = all_emails_to_triage[idx : idx + 5]
                # Results is now a dict {message_id: triage_data}
                results = await loop.run_in_executor(None, batch_triage_emails, batch)

                for email in batch:
                    msg_id = email.get("id")
                    triage = results.get(msg_id)

                    if triage:
                        await process_triaged_email(email, triage, loop)
                        db.mark_as_processed(msg_id)
                    else:
                        logger.warning(f"Missing triage result for {msg_id} in batch.")
                        # This should rarely happen now because batch_triage_emails has fallback

                idx += 5

        global LAST_PATROL_TIME
        LAST_PATROL_TIME = datetime.now().strftime("%I:%M %p")
        logger.info(f"🛡️ PATROL COMPLETE at {LAST_PATROL_TIME}")
    except Exception as e:
        logger.error(f"Error in global poll: {e}")


async def background_scheduler():
    """Background task to run daily nudges and summaries."""
    global SCHEDULE_JOBS_DONE
    from services.whapi import (
        send_pending_items_summary,
        send_morning_nudge,
        send_spam_bulk_ask,
    )

    while True:
        try:
            now = datetime.now()
            hour, today = now.hour, now.strftime("%Y-%m-%d")
            if hour == 8 and f"nudge_{today}" not in SCHEDULE_JOBS_DONE:
                try:
                    send_morning_nudge()
                except Exception as nudge_err:
                    logger.error(f"Nudge error: {nudge_err}")
                SCHEDULE_JOBS_DONE.add(f"nudge_{today}")
            if hour == 16 and f"summary_{today}" not in SCHEDULE_JOBS_DONE:
                try:
                    send_pending_items_summary()
                except Exception as summary_err:
                    logger.error(f"Summary error: {summary_err}")
                try:
                    send_spam_bulk_ask()
                except Exception as spam_err:
                    logger.error(f"Spam ask error: {spam_err}")
                SCHEDULE_JOBS_DONE.add(f"summary_{today}")
            if hour == 0:
                SCHEDULE_JOBS_DONE.clear()
        except Exception as e:
            logger.error(f"Scheduler Error: {e}")
        await asyncio.sleep(300)


async def process_triaged_email(email, triage, loop):
    """Handles the logic after an email has been triaged, following Steve's Handwritten Map."""
    from services.google_sheets import log_activity, check_client_identity
    from services.gmail import get_historical_context, archive_message
    from services.imap import archive_message_imap
    from services.whapi import send_notification, send_whatsapp_message
    from services.gemini import draft_response
    import json

    clean_email = email.get("clean_email", "")
    token_file = email.get("token_file")
    acc_type = email.get("acc_type")
    msg_id = email.get("id")
    tier = triage.get("tier", 5)

    from_name = email.get("sender", "Unknown")
    snippet = email.get("snippet", "")
    is_gmail = acc_type == "gmail"
    # 🌟 0. SPECIAL ONBOARDING FLOW
    if triage.get("is_onboarding_triggered"):
        from services.google_sheets import add_new_client_to_master
        from services.gemini import get_gemini_client

        logger.info(f"🆕 RUNNING AUTO-ONBOARDING for {msg_id}")
        prompt = f"Extract Name and Email from this form:\n\n{email['snippet']}\n\nReturn ONLY JSON with 'name' and 'email' keys."
        ai = get_gemini_client()
        if not ai:
            logger.error("Gemini client not initialized for onboarding")
            return
        res = ai.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        import json

        response_text = res.text.strip() if res and res.text else "{}"
        client_details = json.loads(response_text)
        onboard_data = {
            "from_name": client_details.get("name", "Unknown Name"),
            "email_address": client_details.get("email", "unknown@link.com"),
            "subject": email["subject"],
            "body": email["snippet"],
            "to_email": email["delivered_to"],
            "actionable_items": "Client successfully auto-onboarded.",
        }
        await loop.run_in_executor(None, add_new_client_to_master, onboard_data)
        from services.whapi import send_whatsapp_message

        await loop.run_in_executor(
            None,
            send_whatsapp_message,
            os.getenv("FOUNDER_PHONE"),
            f"✨ *NEW CLIENT ONBOARDED!* \n\nName: {onboard_data['from_name']}\nEmail: {onboard_data['email_address']}",
        )
        return  # Complete.

    # 🛡️ 1. CLIENT IDENTITY CHECK
    client = await loop.run_in_executor(None, check_client_identity, clean_email)
    if client:
        from_name = (
            f"{client.get('first_name', '')} {client.get('last_name', '')}".strip()
            or from_name
        )

    log_data = {
        "from_name": from_name.replace("'", "").replace('"', ""),
        "email_address": clean_email,
        "subject": email.get("subject", "No Subject"),
        "body": snippet,
        "tier": str(tier),
        "status": "Pending",
        "actionable_items": triage.get("action_plan", "None Needed"),
    }

    # Log all activity to the main Action Log (which also handles tier-routing)
    await loop.run_in_executor(None, log_activity, log_data, "Action_Log")

    # --- TIER 1 / 2 / 3 (CHERRY'S REFINED RULES - UPDATED FOR DEMO) ---
    if tier in [1, 2, 3]:
        from routes.email import generate_ref_id
        ref_id = generate_ref_id()

        # ... (is_doc_signed / is_call / is_new_client checks)

        # For the demo, let's draft for Tier 1, 2, and 3
        hist_context = await loop.run_in_executor(
            None, get_historical_context, clean_email
        )
        draft_result = await loop.run_in_executor(
            None, draft_response, email, tier, hist_context, client
        )

        if isinstance(draft_result, dict):
            draft_body = draft_result.get("draft", "Error generating draft")
            suggested_actions = draft_result.get("suggested_actions", [])
            ai_reasoning = draft_result.get("ai_reasoning", triage.get("reason", ""))
        else:
            draft_body = draft_result
            ai_reasoning = triage.get("reason", "")
            suggested_actions = []

        # Save full email content for client extraction later
        email_body = email.get("snippet", "") + "\n\n" + email.get("body", "")

        db.save_pending_approval(
            ref_id,
            {
                "message_id": msg_id,
                "thread_id": email.get("threadId", ""),
                "sender": clean_email,
                "subject": email["subject"],
                "draft_body": draft_body,
                "delivered_to": f"{email.get('delivered_to', 'unknown')}|{token_file}",
                "tier": str(tier),
                "workflow_stage": "draft",
                "email_body": email_body[:5000],
                "suggested_actions": json.dumps(suggested_actions),
                "ai_reasoning": ai_reasoning,
            },
        )

        # Index email to ChromaDB RAG (single sovereign source of truth)
        try:
            from services.twin_engine import rag, TwinType

            rag_text = (
                f"Email from: {clean_email}\n"
                f"Subject: {email.get('subject', '')}\n"
                f"Tier: {tier}\n"
                f"AI Draft Response:\n{draft_body}"
            )
            rag_meta = {
                "source": "email_triage",
                "ref_id": ref_id,
                "sender": clean_email,
                "subject": email.get("subject", ""),
                "tier": str(tier),
            }
            twin = TwinType.ACCOUNTANT if any(
                w in email.get("subject", "").lower()
                for w in ("invoice", "tax", "bas", "gst", "expense")
            ) else TwinType.ADMIN
            rag.ingest(twin, f"triage-{ref_id}", rag_text, rag_meta)
        except Exception as rag_err:
            logger.warning(f"RAG ingest skipped: {rag_err}")

        action_hint = (
            f"Draft ready. (Ref #{ref_id}) Stay in Inbox."
            if tier == 1
            else f"Logged. (Ref #{ref_id}) No reply needed."
        )
        await loop.run_in_executor(
            None, send_notification, email, tier, action_hint, ref_id
        )

        # Auto-acknowledge for Tier 1 (existing clients) - DISABLED for now
        # TODO: Re-enable after testing - needs to happen AFTER approval, not during triage
        # if tier == 1 and not is_new_client:
        #     whitelist_emails, whitelist_domains = _get_client_whitelist()
        #     is_existing_client = clean_email in whitelist_emails or any(clean_email.endswith('@' + d) for d in whitelist_domains)
        #
        #     if is_existing_client:
        #         logger.info(f"AUTO-ACK: Would send acknowledgement to existing client {clean_email}")

    # --- TIER 3 / 4 (ARCHIVE & LOG) ---
    elif tier == 3 or tier == 4:
        has_activity, is_portal = (
            triage.get("has_activity"),
            triage.get("is_portal_update"),
        )
        is_portal_digest = triage.get("is_portal_digest", False)

        # Portal Daily Digest special handling
        if is_portal_digest:
            # 1. Log to Activity_Log sheet (always)
            await loop.run_in_executor(None, log_activity, log_data, "Action_Log")

            # 2. Log to Updates_Archive sheet (always)
            await loop.run_in_executor(None, log_activity, log_data, "Portal_Updates")

            # 3. Send WhatsApp only if has activity
            if has_activity:
                logger.info("PORTAL DIGEST WITH ACTIVITY: Sending WhatsApp reminder.")
                await loop.run_in_executor(
                    None,
                    send_whatsapp_message,
                    os.getenv("FOUNDER_PHONE"),
                    f"Suitedash Portal Activity: {email['subject']}\nCheck: {snippet[:150]}...",
                )
            else:
                logger.info("PORTAL DIGEST: No activity. Silent.")
        else:
            # Normal portal updates handling
            if is_portal and "digest" in email["subject"].lower():
                if has_activity:
                    logger.info("PORTAL ACTIVITY: Notifying Steve.")
                    await loop.run_in_executor(
                        None,
                        send_whatsapp_message,
                        os.getenv("FOUNDER_PHONE"),
                        f"Suitedash Portal Activity: {email['subject']}\nCheck: {snippet[:150]}...",
                    )
                    await loop.run_in_executor(
                        None, log_activity, log_data, "Portal_Updates"
                    )
                else:
                    logger.info("PORTAL DIGEST: No activity. Archiving silently.")

        # Archive or Move to Special Label (e.g. Quickbooks)
        logger.info(f"TIER {tier} ARCHIVE.")
        is_qb = "quickbooks" in clean_email or (
            "intuit.com" in clean_email and "invoice" in email["subject"].lower()
        )

        if is_qb and "your webestimator" in email["subject"].lower():
            from services.gmail import move_to_label

            logger.info(
                "QUICKBOOKS RULE: Moving to 'Quickbooks Recurring Invoice' label."
            )
            if is_gmail:
                await loop.run_in_executor(
                    None,
                    move_to_label,
                    msg_id,
                    "Quickbooks Recurring Invoice",
                    token_file,
                )
            else:
                await loop.run_in_executor(
                    None, archive_message_imap, msg_id, token_file
                )
        else:
            if is_gmail:
                await loop.run_in_executor(None, archive_message, msg_id, token_file)
            else:
                await loop.run_in_executor(
                    None, archive_message_imap, msg_id, token_file
                )

        # Specialized Logging (only for non-digest portal updates)
        if is_portal and not is_portal_digest:
            await loop.run_in_executor(None, log_activity, log_data, "Portal_Updates")
        elif not is_portal_digest:
            # Tier 3 = Suppliers (log to Supplier_Expenses, stay in inbox)
            if tier == 3:
                await loop.run_in_executor(
                    None, log_activity, log_data, "Supplier_Expenses"
                )
                logger.info(
                    "TIER 3 (Supplier): Logged to Supplier_Expenses, STAYING in Inbox."
                )
                # Don't archive - stay in inbox for now
            else:
                await loop.run_in_executor(None, log_activity, log_data, "Action_Log")

    elif tier == 5:
        # SPAM: Log to SPAM sheet and archive
        logger.info(f"TIER 5 SPAM: Logging to SPAM sheet and archiving {clean_email}.")
        await loop.run_in_executor(None, log_activity, log_data, "SPAM")
        if is_gmail:
            await loop.run_in_executor(None, archive_message, msg_id, token_file)
        else:
            await loop.run_in_executor(None, archive_message_imap, msg_id, token_file)



async def background_scheduler():
    """Background task to run daily nudges and summaries."""
    global SCHEDULE_JOBS_DONE
    from services.whapi import (
        send_pending_items_summary,
        send_morning_nudge,
        send_spam_bulk_ask,
    )

    while True:
        try:
            now = datetime.now()
            hour, today = now.hour, now.strftime("%Y-%m-%d")
            if hour == 8 and f"nudge_{today}" not in SCHEDULE_JOBS_DONE:
                try:
                    send_morning_nudge()
                except Exception as nudge_err:
                    logger.error(f"Nudge error: {nudge_err}")
                SCHEDULE_JOBS_DONE.add(f"nudge_{today}")
            if hour == 16 and f"summary_{today}" not in SCHEDULE_JOBS_DONE:
                try:
                    send_pending_items_summary()
                except Exception as summary_err:
                    logger.error(f"Summary error: {summary_err}")
                try:
                    send_spam_bulk_ask()
                except Exception as spam_err:
                    logger.error(f"Spam ask error: {spam_err}")
                SCHEDULE_JOBS_DONE.add(f"summary_{today}")
            if hour == 0:
                SCHEDULE_JOBS_DONE.clear()
        except Exception as e:
            logger.error(f"Scheduler Error: {e}")
        await asyncio.sleep(300)

