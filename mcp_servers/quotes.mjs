#!/usr/bin/env node
import { all, get, run } from './_lib/db.mjs';
import { runServer } from './_lib/mcp.mjs';

const TEMPLATES = {
  Kitchen:    { rate: 150, materials_buffer: 0.30, avg_duration: 5 },
  Bathroom:   { rate: 150, materials_buffer: 0.30, avg_duration: 4 },
  Plumbing:   { rate: 150, materials_buffer: 0.20, avg_duration: 3 },
  Electrical: { rate: 160, materials_buffer: 0.25, avg_duration: 2 },
  Deck:       { rate: 140, materials_buffer: 0.40, avg_duration: 3 },
  Emergency:  { rate: 200, materials_buffer: 0.20, avg_duration: 1 },
  General:    { rate: 150, materials_buffer: 0.25, avg_duration: 2 },
};

const tools = {
  create_quote: {
    description: 'Create a quote for a lead. Total = (materials + labor_hours * rate) * (1 + markup%)',
    inputSchema: {
      type: 'object',
      properties: {
        lead_id: { type: 'number' },
        materials_cost: { type: 'number' },
        labor_hours: { type: 'number' },
        markup_percent: { type: 'number', description: 'default 20' },
        rate: { type: 'number', description: 'default 150 $/hr' },
      },
      required: ['lead_id', 'materials_cost', 'labor_hours'],
    },
  },
  get_quote: {
    description: 'Get one quote by id',
    inputSchema: { type: 'object', properties: { id: { type: 'number' } }, required: ['id'] },
  },
  get_quote_template: {
    description: 'Return labor rate, materials buffer, avg duration for a job_type',
    inputSchema: { type: 'object', properties: { job_type: { type: 'string' } }, required: ['job_type'] },
  },
  get_overdue_quotes: {
    description: 'Quotes sent but not accepted beyond days_threshold (default 7)',
    inputSchema: { type: 'object', properties: { days_threshold: { type: 'number' } } },
  },
};

const handlers = {
  async create_quote(a) {
    const rate = a.rate || 150;
    const laborCost = (a.labor_hours || 0) * rate;
    const subtotal = (a.materials_cost || 0) + laborCost;
    const markup = a.markup_percent ?? 20;
    const total = subtotal * (1 + markup / 100);
    const lead = await get('SELECT client_name, job_type FROM leads WHERE id = ?', [a.lead_id]);
    const r = await run(
      `INSERT INTO quotes (lead_id, client_name, job_type, materials_cost, labor_cost, markup_percent, total_amount, status)
       VALUES (?, ?, ?, ?, ?, ?, ?, 'draft')`,
      [a.lead_id, lead?.client_name || null, lead?.job_type || null, a.materials_cost, laborCost, markup, total]
    );
    return { quote_id: r.lastID, materials: a.materials_cost, labor: laborCost, markup_percent: markup, total_amount: total };
  },
  async get_quote({ id }) {
    return (await get('SELECT * FROM quotes WHERE id = ?', [id])) || { error: 'not found' };
  },
  async get_quote_template({ job_type }) {
    const t = TEMPLATES[job_type] || TEMPLATES.General;
    return { job_type, labor_rate_per_hour: t.rate, materials_markup_percent: t.materials_buffer * 100, estimated_duration_hours: t.avg_duration };
  },
  async get_overdue_quotes(a) {
    const days = a.days_threshold || 7;
    const rows = await all(
      `SELECT id, client_name, job_type, total_amount, sent_date
       FROM quotes
       WHERE status = 'sent' AND datetime(sent_date, '+' || ? || ' days') < datetime('now')
       ORDER BY sent_date ASC`,
      [days]
    );
    return { count: rows.length, overdue: rows };
  },
};

runServer({ name: 'backpocket-quotes', tools, handlers });
