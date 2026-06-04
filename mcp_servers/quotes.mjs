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

function normalizeSpace(value = '') {
  return String(value).replace(/\s+/g, ' ').trim();
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function parseListField(value) {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed)) return parsed.map((item) => normalizeSpace(item)).filter(Boolean);
  } catch {}
  return String(value)
    .split(/[,\n;]+/)
    .map(normalizeSpace)
    .filter(Boolean);
}

function topItems(values, limit = 5) {
  const counts = new Map();

  for (const value of values) {
    const key = value.toLowerCase();
    const existing = counts.get(key) || { label: value, count: 0 };
    existing.count += 1;
    counts.set(key, existing);
  }

  return [...counts.values()]
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label))
    .slice(0, limit)
    .map((item) => item.label);
}

function daysSince(value) {
  if (!value) return null;
  const diff = Date.now() - new Date(value).getTime();
  return Math.max(0, Math.floor(diff / 86400000));
}

function buildFollowUpMessage({ clientName, jobType, tone, daysOutstanding }) {
  const greeting = clientName ? `Hi ${clientName.split(/\s+/)[0]},` : 'Hi,';
  const label = jobType || 'job';
  const ageNote = daysOutstanding >= 7
    ? 'I still have room to lock this in soon if you want to move ahead.'
    : 'I can line this up once you are ready.';

  const templates = {
    friendly: `${greeting} just checking in on the ${label} quote I sent through. ${ageNote} If you want to go ahead or have any questions, reply here and I will sort it. Cheers,`,
    professional: `${greeting} following up on the ${label} quote. ${ageNote} Let me know if you would like to proceed or if you want any changes made to the scope.`,
    urgent: `${greeting} quick follow-up on the ${label} quote. I have limited availability coming up, so if you want this booked in, send me a reply and I will lock in a date.`,
  };

  return templates[tone] || templates.friendly;
}

function scoreQuoteMatch(quote, emailInput) {
  const from = String(emailInput.email_from || '').toLowerCase();
  const text = normalizeSpace(`${emailInput.email_subject || ''} ${emailInput.email_body || ''}`).toLowerCase();
  const explicitQuoteId = text.match(/\bquote\s*#?\s*(\d+)\b/i);
  let score = 0;
  const reasons = [];

  if (explicitQuoteId && Number(explicitQuoteId[1]) === Number(quote.id)) {
    score += 0.6;
    reasons.push('Quote number mentioned');
  }

  if (quote.email && from.includes(String(quote.email).toLowerCase())) {
    score += 0.45;
    reasons.push('Sender email matches lead');
  }

  if (quote.client_name) {
    const nameParts = String(quote.client_name)
      .toLowerCase()
      .split(/\s+/)
      .filter((part) => part.length > 2);
    if (nameParts.some((part) => text.includes(part))) {
      score += 0.15;
      reasons.push('Client name referenced');
    }
  }

  if (quote.job_type && text.includes(String(quote.job_type).toLowerCase())) {
    score += 0.15;
    reasons.push('Job type referenced');
  }

  if (quote.location && text.includes(String(quote.location).toLowerCase())) {
    score += 0.1;
    reasons.push('Location referenced');
  }

  if (quote.status === 'sent') {
    score += 0.05;
    reasons.push('Quote is currently active');
  }

  return {
    score: Number(Math.min(score, 0.98).toFixed(2)),
    reasons,
  };
}

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
  draft_follow_up_email: {
    description: 'Draft a follow-up email for a quote without calling an external model',
    inputSchema: {
      type: 'object',
      properties: {
        quote_id: { type: 'number' },
        tone: { type: 'string', enum: ['friendly', 'professional', 'urgent'] },
      },
      required: ['quote_id'],
    },
  },
  match_quote_to_email: {
    description: 'Match an inbound client email to likely quote records',
    inputSchema: {
      type: 'object',
      properties: {
        email_from: { type: 'string' },
        email_subject: { type: 'string' },
        email_body: { type: 'string' },
      },
      required: ['email_from', 'email_subject', 'email_body'],
    },
  },
  get_job_patterns: {
    description: 'Summarize historical pricing and scope patterns for a job type',
    inputSchema: {
      type: 'object',
      properties: {
        job_type: { type: 'string' },
        location: { type: 'string' },
      },
      required: ['job_type'],
    },
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
    await run(
      `UPDATE leads
       SET status = 'quoted', updated_at = CURRENT_TIMESTAMP
       WHERE id = ?`,
      [a.lead_id]
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
  async draft_follow_up_email({ quote_id, tone = 'friendly' }) {
    const quote = await get(
      `SELECT q.*, l.email
       FROM quotes q
       LEFT JOIN leads l ON l.id = q.lead_id
       WHERE q.id = ?`,
      [quote_id]
    );

    if (!quote) return { error: 'not found' };

    const daysOutstanding = daysSince(quote.sent_date || quote.created_at) || 0;
    const emailBody = buildFollowUpMessage({
      clientName: quote.client_name,
      jobType: quote.job_type,
      tone,
      daysOutstanding,
    });

    return {
      quote_id,
      tone,
      recipient_email: quote.email || null,
      quote_status: quote.status,
      days_outstanding: daysOutstanding,
      subject_suggestion: `Follow-up on your ${quote.job_type || 'BackPocket'} quote`,
      email_body: emailBody,
      action: 'Ready to send via email workflow',
    };
  },
  async match_quote_to_email({ email_from, email_subject, email_body }) {
    const quotes = await all(
      `SELECT q.id, q.client_name, q.job_type, q.status, q.total_amount, q.sent_date, l.email, l.location
       FROM quotes q
       LEFT JOIN leads l ON l.id = q.lead_id
       ORDER BY q.created_at DESC
       LIMIT 200`
    );

    const matches = quotes
      .map((quote) => {
        const scored = scoreQuoteMatch(quote, { email_from, email_subject, email_body });
        return {
          id: quote.id,
          client_name: quote.client_name,
          job_type: quote.job_type,
          status: quote.status,
          total_amount: quote.total_amount,
          confidence: scored.score,
          reasons: scored.reasons,
        };
      })
      .filter((match) => match.confidence >= 0.25)
      .sort((a, b) => b.confidence - a.confidence || b.id - a.id)
      .slice(0, 5);

    const combinedText = `${email_subject} ${email_body}`.toLowerCase();
    let suggestedAction = 'No confident match. Review manually.';
    if (matches.length) {
      if (/\b(accept|accepted|approve|approved|go ahead|proceed|book it)\b/i.test(combinedText)) {
        suggestedAction = 'Likely acceptance. Update the matched quote and schedule next steps.';
      } else if (/\b(question|clarify|clarification|change|update)\b/i.test(combinedText)) {
        suggestedAction = 'Client likely has questions. Reply with clarification before changing status.';
      } else {
        suggestedAction = 'Likely quote reply. Review the top match and respond or follow up.';
      }
    }

    return {
      status: 'analysis_complete',
      email_from,
      matched_quote_ids: matches.map((match) => match.id),
      confidence: matches[0]?.confidence || 0,
      matches,
      suggested_action: suggestedAction,
    };
  },
  async get_job_patterns({ job_type, location }) {
    const params = [`%${job_type}%`];
    let locationClause = '';
    if (location) {
      locationClause = 'AND lower(COALESCE(l.location, "")) LIKE lower(?)';
      params.push(`%${location}%`);
    }

    const rows = await all(
      `SELECT q.total_amount, q.materials_cost, q.labor_cost, q.markup_percent, q.status,
              l.pain_points, l.scope_items, l.location
       FROM quotes q
       LEFT JOIN leads l ON l.id = q.lead_id
       WHERE lower(COALESCE(q.job_type, "")) LIKE lower(?)
       ${locationClause}
       ORDER BY q.created_at DESC
       LIMIT 200`,
      params
    );

    const template = TEMPLATES[job_type] || TEMPLATES.General;
    if (!rows.length) {
      return {
        job_type,
        location: location || null,
        sample_size: 0,
        avg_price: null,
        avg_duration_hours: template.avg_duration,
        labor_rate_per_hour: template.rate,
        materials_markup_percent: template.materials_buffer * 100,
        acceptance_rate: null,
        common_issues: [],
        note: 'No local quote history yet; using the default pricing template only.',
      };
    }

    const totalAmount = rows.reduce((sum, row) => sum + Number(row.total_amount || 0), 0);
    const acceptedCount = rows.filter((row) => ['accepted', 'invoiced'].includes(row.status)).length;
    const materialsRatios = rows
      .filter((row) => Number(row.total_amount || 0) > 0)
      .map((row) => Number(row.materials_cost || 0) / Number(row.total_amount || 1));
    const commonIssues = topItems(
      rows.flatMap((row) => [
        ...parseListField(row.pain_points),
        ...parseListField(row.scope_items),
      ]),
      5
    );

    return {
      job_type,
      location: location || null,
      sample_size: rows.length,
      avg_price: Number((totalAmount / rows.length).toFixed(2)),
      avg_duration_hours: template.avg_duration,
      labor_rate_per_hour: template.rate,
      materials_markup_percent: template.materials_buffer * 100,
      materials_percentage: materialsRatios.length
        ? Number((materialsRatios.reduce((sum, ratio) => sum + ratio, 0) / materialsRatios.length * 100).toFixed(1))
        : null,
      acceptance_rate: Number((acceptedCount / rows.length).toFixed(2)),
      common_issues: commonIssues,
      locations_seen: unique(rows.map((row) => row.location)).slice(0, 5),
      note: 'Historical pricing derived from local quote records.',
    };
  },
};

runServer({ name: 'backpocket-quotes', tools, handlers });
