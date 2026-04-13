#!/usr/bin/env node
import { all, get, run } from './_lib/db.mjs';
import { runServer } from './_lib/mcp.mjs';

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
};

const handlers = {
  async get_pipeline_summary() {
    const r = await get(`
      SELECT
        COUNT(*) AS total_quotes,
        SUM(CASE WHEN status='draft' THEN 1 ELSE 0 END) AS draft,
        SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) AS sent,
        SUM(CASE WHEN status='accepted' THEN 1 ELSE 0 END) AS accepted,
        SUM(CASE WHEN status IN ('accepted','invoiced') THEN total_amount ELSE 0 END) AS revenue_pipeline
      FROM quotes`);
    return r || { total_quotes: 0 };
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
};

runServer({ name: 'backpocket-pipeline', tools, handlers });
