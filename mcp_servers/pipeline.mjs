#!/usr/bin/env node
import { all, get, run } from './_lib/db.mjs';
import { runServer } from './_lib/mcp.mjs';

function daysSince(value) {
  if (!value) return null;
  const diff = Date.now() - new Date(value).getTime();
  return Math.max(0, Math.floor(diff / 86400000));
}

function buildResponse(fields) {
  return {
    priority: fields.priority,
    suggested_action: fields.suggested_action,
    reason: fields.reason,
    next_steps: fields.next_steps,
    context: fields.context,
    entity_id: fields.entity_id || null,
  };
}

async function fetchPipelineSummary() {
  const row = await get(`
    SELECT
      COUNT(*) AS total_quotes,
      SUM(CASE WHEN status='draft' THEN 1 ELSE 0 END) AS draft,
      SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) AS sent,
      SUM(CASE WHEN status='accepted' THEN 1 ELSE 0 END) AS accepted,
      SUM(CASE WHEN status IN ('accepted','invoiced') THEN total_amount ELSE 0 END) AS revenue_pipeline
    FROM quotes`);

  return row || {
    total_quotes: 0,
    draft: 0,
    sent: 0,
    accepted: 0,
    revenue_pipeline: 0,
  };
}

const tools = {
  get_pipeline_summary: {
    description: 'Totals across quote pipeline (draft, sent, accepted, revenue)',
    inputSchema: { type: 'object', properties: {} },
  },
  record_payment: {
    description: 'Log a payment received against a quote',
    inputSchema: {
      type: 'object',
      properties: {
        quote_id: { type: 'number' },
        amount: { type: 'number' },
        payment_date: { type: 'string', description: 'ISO date; defaults to today' },
      },
      required: ['quote_id', 'amount'],
    },
  },
  list_payments: {
    description: 'List recent payments (max 50)',
    inputSchema: { type: 'object', properties: {} },
  },
  suggest_next_action: {
    description: 'Suggest the next operational action for a lead, quote, or the overall pipeline',
    inputSchema: {
      type: 'object',
      properties: {
        context: { type: 'string' },
        lead_id: { type: 'number' },
        quote_id: { type: 'number' },
      },
    },
  },
};

const handlers = {
  async get_pipeline_summary() {
    return fetchPipelineSummary();
  },
  async record_payment({ quote_id, amount, payment_date }) {
    const date = payment_date || new Date().toISOString().slice(0, 10);
    const quote = await get('SELECT client_name FROM quotes WHERE id = ?', [quote_id]);
    const r = await run(
      `INSERT INTO payments (quote_id, client_name, amount, received_date, status)
       VALUES (?, ?, ?, ?, 'received')`,
      [quote_id, quote?.client_name || null, amount, date]
    );
    return { payment_id: r.lastID, quote_id, amount, status: 'received' };
  },
  async list_payments() {
    const rows = await all('SELECT * FROM payments ORDER BY created_at DESC LIMIT 50');
    return { count: rows.length, payments: rows };
  },
  async suggest_next_action({ context, lead_id, quote_id }) {
    if (quote_id) {
      const quote = await get(
        `SELECT q.*, l.location, l.urgency
         FROM quotes q
         LEFT JOIN leads l ON l.id = q.lead_id
         WHERE q.id = ?`,
        [quote_id]
      );
      if (!quote) return { error: 'quote not found' };

      const paymentSummary = await get(
        `SELECT COUNT(*) AS payment_count, COALESCE(SUM(amount), 0) AS total_paid
         FROM payments
         WHERE quote_id = ?`,
        [quote_id]
      );
      const sentDays = daysSince(quote.sent_date || quote.created_at);

      if (quote.status === 'draft') {
        return buildResponse({
          priority: quote.urgency === 'high' ? 'high' : 'medium',
          suggested_action: 'Review and send the draft quote.',
          reason: 'Draft quotes do not convert until they are sent to the client.',
          next_steps: ['Confirm scope and pricing', 'Send the quote', 'Set a follow-up reminder'],
          context: 'quote_draft',
          entity_id: quote_id,
        });
      }

      if (quote.status === 'sent') {
        const overdue = sentDays !== null && sentDays >= 7;
        return buildResponse({
          priority: overdue ? 'high' : 'medium',
          suggested_action: overdue
            ? 'Follow up on the sent quote now.'
            : 'Wait briefly, then follow up if the client stays quiet.',
          reason: overdue
            ? `The quote has been out for ${sentDays} days without a recorded acceptance.`
            : `The quote was sent recently${sentDays !== null ? ` (${sentDays} days ago)` : ''}.`,
          next_steps: overdue
            ? ['Send a short follow-up', 'Answer any client questions', 'Update status if they accept']
            : ['Hold for a few days', 'Prepare a follow-up message', 'Track reply status'],
          context: 'quote_sent',
          entity_id: quote_id,
        });
      }

      if (quote.status === 'accepted') {
        const hasPayments = Number(paymentSummary?.payment_count || 0) > 0;
        return buildResponse({
          priority: 'high',
          suggested_action: hasPayments
            ? 'Schedule the job and confirm the start date.'
            : 'Collect the deposit or first payment.',
          reason: hasPayments
            ? 'The quote is accepted and at least one payment is already recorded.'
            : 'The quote is accepted but there is no payment recorded yet.',
          next_steps: hasPayments
            ? ['Book the work in the calendar', 'Confirm materials', 'Send start confirmation']
            : ['Issue deposit request', 'Confirm payment timing', 'Only then lock in the schedule'],
          context: 'quote_accepted',
          entity_id: quote_id,
        });
      }

      if (quote.status === 'invoiced') {
        const paidInFull = Number(paymentSummary?.total_paid || 0) >= Number(quote.total_amount || 0);
        return buildResponse({
          priority: paidInFull ? 'low' : 'high',
          suggested_action: paidInFull
            ? 'Close the job and archive the paperwork.'
            : 'Chase the outstanding invoice payment.',
          reason: paidInFull
            ? 'Payments recorded meet or exceed the invoiced amount.'
            : 'The invoice is out but payments do not yet cover the quote total.',
          next_steps: paidInFull
            ? ['Mark the job complete', 'Store final documents', 'Request a review if appropriate']
            : ['Send payment reminder', 'Confirm due date', 'Escalate if overdue'],
          context: 'quote_invoiced',
          entity_id: quote_id,
        });
      }
    }

    if (lead_id) {
      const lead = await get('SELECT * FROM leads WHERE id = ?', [lead_id]);
      if (!lead) return { error: 'lead not found' };

      if (lead.status === 'new') {
        return buildResponse({
          priority: lead.urgency === 'high' ? 'high' : 'medium',
          suggested_action: 'Contact the lead and qualify the job.',
          reason: 'New leads are highest value when contacted quickly.',
          next_steps: ['Call or reply to the client', 'Confirm scope and site details', 'Book a visit or prepare a quote'],
          context: 'new_lead',
          entity_id: lead_id,
        });
      }

      if (lead.status === 'quoted') {
        return buildResponse({
          priority: 'medium',
          suggested_action: 'Check the linked quote status and plan follow-up.',
          reason: 'This lead has already moved into quoting and now needs conversion work.',
          next_steps: ['Find the quote record', 'Confirm it was sent', 'Set a follow-up date'],
          context: 'lead_quoted',
          entity_id: lead_id,
        });
      }

      if (lead.status === 'accepted') {
        return buildResponse({
          priority: 'high',
          suggested_action: 'Move the accepted lead into delivery.',
          reason: 'The client has effectively converted and now expects scheduling and execution.',
          next_steps: ['Confirm the start date', 'Assign labour/materials', 'Track deposit and paperwork'],
          context: 'lead_accepted',
          entity_id: lead_id,
        });
      }
    }

    if (context) {
      const canned = {
        new_lead: buildResponse({
          priority: 'high',
          suggested_action: 'Reply quickly and qualify the scope.',
          reason: 'Fast response matters most at the top of the funnel.',
          next_steps: ['Confirm location', 'Clarify job details', 'Book a site visit or quote'],
          context: 'new_lead',
        }),
        quote_sent: buildResponse({
          priority: 'medium',
          suggested_action: 'Follow up within 5 to 7 days if there is no reply.',
          reason: 'Most sent quotes need a light follow-up to convert.',
          next_steps: ['Check sent date', 'Prepare follow-up message', 'Update status after reply'],
          context: 'quote_sent',
        }),
        quote_accepted: buildResponse({
          priority: 'high',
          suggested_action: 'Collect payment and lock in the schedule.',
          reason: 'Acceptance needs immediate operational follow-through.',
          next_steps: ['Record deposit', 'Confirm dates', 'Allocate materials and labour'],
          context: 'quote_accepted',
        }),
        payment_received: buildResponse({
          priority: 'medium',
          suggested_action: 'Confirm receipt and move the job forward.',
          reason: 'Payment is a handoff point into delivery or close-out.',
          next_steps: ['Send receipt', 'Update job status', 'Schedule work or finalise documents'],
          context: 'payment_received',
        }),
      };

      return canned[context] || {
        error: `unknown context: ${context}`,
      };
    }

    const summary = await fetchPipelineSummary();
    const overdueSent = await get(
      `SELECT COUNT(*) AS overdue_count
       FROM quotes
       WHERE status = 'sent'
         AND datetime(sent_date, '+7 days') < datetime('now')`
    );

    if (Number(overdueSent?.overdue_count || 0) > 0) {
      return buildResponse({
        priority: 'high',
        suggested_action: 'Work the overdue sent quotes first.',
        reason: `${overdueSent.overdue_count} sent quotes are older than 7 days.`,
        next_steps: ['List overdue quotes', 'Send follow-up messages', 'Close out stale opportunities'],
        context: 'pipeline_overdue',
      });
    }

    if (Number(summary.draft || 0) > 0) {
      return buildResponse({
        priority: 'medium',
        suggested_action: 'Send the draft quotes waiting in the pipeline.',
        reason: `${summary.draft} draft quotes are sitting unsent.`,
        next_steps: ['Review pricing', 'Send drafts', 'Set follow-up reminders'],
        context: 'pipeline_drafts',
      });
    }

    return buildResponse({
      priority: 'low',
      suggested_action: 'Review new leads and keep the pipeline moving.',
      reason: 'No urgent quote or payment blockers were detected.',
      next_steps: ['Check incoming leads', 'Review pipeline summary', 'Update statuses as work progresses'],
      context: 'pipeline_general',
    });
  },
};

runServer({ name: 'backpocket-pipeline', tools, handlers });
