#!/usr/bin/env node
import { all, get, run } from './_lib/db.mjs';
import { runServer } from './_lib/mcp.mjs';

const tools = {
  search_leads: {
    description: 'Find leads by status, job_type, urgency, location, or min budget',
    inputSchema: {
      type: 'object',
      properties: {
        status: { type: 'string' },
        job_type: { type: 'string' },
        urgency: { type: 'string' },
        location: { type: 'string' },
        min_budget: { type: 'number' },
      },
    },
  },
  get_lead: {
    description: 'Get one lead by id',
    inputSchema: { type: 'object', properties: { id: { type: 'number' } }, required: ['id'] },
  },
  create_lead: {
    description: 'Create a new lead row',
    inputSchema: {
      type: 'object',
      properties: {
        client_name: { type: 'string' },
        email: { type: 'string' },
        job_type: { type: 'string' },
        location: { type: 'string' },
        urgency: { type: 'string' },
        estimated_budget: { type: 'number' },
      },
      required: ['client_name', 'email'],
    },
  },
};

const handlers = {
  async search_leads(a) {
    const where = ['1=1'];
    const params = [];
    if (a.status) { where.push('status = ?'); params.push(a.status); }
    if (a.job_type) { where.push('job_type LIKE ?'); params.push(`%${a.job_type}%`); }
    if (a.urgency) { where.push('urgency = ?'); params.push(a.urgency); }
    if (a.location) { where.push('location LIKE ?'); params.push(`%${a.location}%`); }
    if (a.min_budget) { where.push('estimated_budget >= ?'); params.push(a.min_budget); }
    const rows = await all(`SELECT * FROM leads WHERE ${where.join(' AND ')} ORDER BY created_at DESC LIMIT 50`, params);
    return { count: rows.length, leads: rows };
  },
  async get_lead({ id }) {
    return (await get('SELECT * FROM leads WHERE id = ?', [id])) || { error: 'not found' };
  },
  async create_lead(a) {
    const r = await run(
      `INSERT INTO leads (client_name, email, job_type, location, urgency, estimated_budget, status)
       VALUES (?, ?, ?, ?, ?, ?, 'new')`,
      [a.client_name, a.email, a.job_type || null, a.location || null, a.urgency || null, a.estimated_budget || null]
    );
    return { lead_id: r.lastID, status: 'new' };
  },
};

runServer({ name: 'backpocket-leads', tools, handlers });
