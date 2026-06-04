#!/usr/bin/env node
import { all, get, run } from './_lib/db.mjs';
import { runServer } from './_lib/mcp.mjs';

const JOB_TYPE_RULES = [
  { label: 'Emergency', keywords: ['emergency', 'urgent', 'asap', 'immediately', 'burst pipe', 'flood', 'no power', 'sparking'] },
  { label: 'Kitchen', keywords: ['kitchen', 'cabinet', 'benchtop', 'splashback', 'pantry'] },
  { label: 'Bathroom', keywords: ['bathroom', 'shower', 'toilet', 'vanity', 'ensuite'] },
  { label: 'Plumbing', keywords: ['plumbing', 'plumber', 'pipe', 'leak', 'drain', 'tap', 'hot water'] },
  { label: 'Electrical', keywords: ['electrical', 'electrician', 'switchboard', 'power point', 'lighting', 'rewire'] },
  { label: 'Deck', keywords: ['deck', 'pergola', 'outdoor stairs', 'balustrade'] },
  { label: 'Roofing', keywords: ['roof', 'gutter', 'downpipe', 'ceiling leak'] },
  { label: 'Painting', keywords: ['paint', 'painting', 'repaint'] },
  { label: 'Flooring', keywords: ['flooring', 'timber floor', 'tiles', 'tiling', 'laminate'] },
];

const PAIN_POINT_KEYWORDS = [
  'leak', 'broken', 'damage', 'crack', 'mould', 'fault', 'urgent',
  'not working', 'replace', 'repair', 'issue', 'problem',
];

const SCOPE_KEYWORDS = [
  'install', 'replace', 'repair', 'renovate', 'build', 'quote',
  'inspect', 'fix', 'upgrade', 'supply', 'fit off', 'paint',
];

function normalizeSpace(value = '') {
  return String(value).replace(/\s+/g, ' ').trim();
}

function titleCase(value = '') {
  return normalizeSpace(value)
    .toLowerCase()
    .split(/\s+/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function parseEmailAddress(value = '') {
  return value.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)?.[0]?.toLowerCase() || null;
}

function humanizeEmailLocalPart(email = '') {
  return email
    .split('@')[0]
    .split(/[._-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function parseSender(emailFrom = '') {
  const email = parseEmailAddress(emailFrom);
  const name = normalizeSpace(emailFrom.replace(/<[^>]+>/g, '').replace(/["']/g, ''));

  if (name && (!email || name.toLowerCase() !== email.toLowerCase())) {
    return { email: email || name, clientName: name };
  }

  if (email) {
    return { email, clientName: humanizeEmailLocalPart(email) || 'Unknown' };
  }

  return {
    email: normalizeSpace(emailFrom) || null,
    clientName: 'Unknown',
  };
}

function detectJobType(text) {
  const haystack = text.toLowerCase();
  const matched = JOB_TYPE_RULES.find((rule) => rule.keywords.some((keyword) => haystack.includes(keyword)));
  return matched?.label || 'General';
}

function extractBudget(text) {
  const contextualPatterns = [
    /\b(?:budget|quote|cost|spend|around|about|under|up to|max(?:imum)?)\D{0,12}\$?\s*(\d[\d,]*(?:\.\d+)?)\s*([kKmM])?\b/i,
    /\$\s*(\d[\d,]*(?:\.\d+)?)\s*([kKmM])?\b/,
  ];

  for (const pattern of contextualPatterns) {
    const match = text.match(pattern);
    if (!match) continue;
    let value = Number(match[1].replace(/,/g, ''));
    const suffix = match[2]?.toLowerCase();
    if (suffix === 'k') value *= 1000;
    if (suffix === 'm') value *= 1000000;
    return Number(value.toFixed(2));
  }

  return null;
}

function extractLocation(text) {
  const addressMatch = text.match(
    /\b\d{1,5}\s+[A-Za-z0-9' -]+(?:street|st|road|rd|avenue|ave|drive|dr|lane|ln|place|pl|court|ct|close|crescent|cres|terrace|tce|way)\b(?:,?\s+[A-Za-z][A-Za-z' -]+){0,2}/i
  );
  if (addressMatch) return normalizeSpace(addressMatch[0]).replace(/[.,;:]+$/, '');

  const suburbMatch = text.match(/\b(?:in|at|near|around|from)\s+([A-Za-z][A-Za-z' -]{2,}(?:\s+[A-Za-z][A-Za-z' -]{2,}){0,2})\b/i);
  if (!suburbMatch) return '';

  const cleaned = suburbMatch[1]
    .split(/\b(?:for|about|with|regarding|because|and)\b/i)[0]
    .replace(/[.,;:!?]+$/, '')
    .trim();

  return titleCase(cleaned);
}

function extractTimeline(text) {
  const patterns = [
    /\b(today|tomorrow|this week|next week|this month|next month|before [A-Za-z]+|by [A-Za-z]+)\b/i,
    /\b(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)\b/,
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) return normalizeSpace(match[1] || match[0]);
  }

  return '';
}

function detectUrgency(text) {
  if (/\b(asap|urgent|emergency|immediately|today|tonight|burst pipe|flood|no power|sparking)\b/i.test(text)) {
    return 'high';
  }
  if (/\b(no rush|whenever|sometime|next month|later on)\b/i.test(text)) {
    return 'low';
  }
  return 'medium';
}

function extractRelevantLines(text, keywords, limit = 4) {
  const lines = text
    .split(/\n+|(?<=[.!?])\s+/)
    .map(normalizeSpace)
    .filter(Boolean);

  return unique(
    lines.filter((line) => keywords.some((keyword) => line.toLowerCase().includes(keyword)))
  ).slice(0, limit);
}

function estimateConfidence(extracted) {
  let score = 0.35;
  if (extracted.client_name && extracted.client_name !== 'Unknown') score += 0.15;
  if (extracted.email) score += 0.15;
  if (extracted.job_type && extracted.job_type !== 'General') score += 0.15;
  if (extracted.location) score += 0.1;
  if (extracted.estimated_budget !== null) score += 0.1;
  if (extracted.pain_points.length) score += 0.05;
  if (extracted.scope_items.length) score += 0.05;
  if (extracted.timeline) score += 0.05;
  return Number(Math.min(score, 0.95).toFixed(2));
}

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
  extract_lead_from_email: {
    description: 'Extract structured lead details from an inbound email and optionally save the lead',
    inputSchema: {
      type: 'object',
      properties: {
        email_from: { type: 'string' },
        subject: { type: 'string' },
        body: { type: 'string' },
        save_to_db: { type: 'boolean', description: 'default false' },
      },
      required: ['email_from', 'subject', 'body'],
    },
  },
  get_client_history: {
    description: 'Summarize past leads, quotes, and payments for a client email',
    inputSchema: {
      type: 'object',
      properties: {
        client_email: { type: 'string' },
      },
      required: ['client_email'],
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
  async extract_lead_from_email({ email_from, subject, body, save_to_db }) {
    const sender = parseSender(email_from);
    const combinedText = `${subject}\n${body}`;
    const extracted = {
      client_name: sender.clientName,
      email: sender.email || normalizeSpace(email_from),
      job_type: detectJobType(combinedText),
      location: extractLocation(body),
      pain_points: extractRelevantLines(body, PAIN_POINT_KEYWORDS),
      scope_items: extractRelevantLines(body, SCOPE_KEYWORDS),
      urgency: detectUrgency(combinedText),
      estimated_budget: extractBudget(combinedText),
      timeline: extractTimeline(combinedText),
    };

    const confidence = estimateConfidence(extracted);

    if (!save_to_db) {
      return {
        status: 'analyzed',
        confidence,
        extracted_data: extracted,
        next_action: 'Use create_lead to save after review',
      };
    }

    const r = await run(
      `INSERT INTO leads
        (client_name, email, job_type, location, pain_points, scope_items, urgency, estimated_budget, timeline, status, extracted_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', CURRENT_TIMESTAMP)`,
      [
        extracted.client_name,
        extracted.email,
        extracted.job_type,
        extracted.location || null,
        JSON.stringify(extracted.pain_points),
        JSON.stringify(extracted.scope_items),
        extracted.urgency,
        extracted.estimated_budget,
        extracted.timeline || null,
      ]
    );

    return {
      status: 'created',
      lead_id: r.lastID,
      confidence,
      extracted_data: extracted,
    };
  },
  async get_client_history({ client_email }) {
    const leads = await all(
      `SELECT * FROM leads
       WHERE lower(email) = lower(?)
       ORDER BY created_at DESC
       LIMIT 100`,
      [client_email]
    );

    if (!leads.length) {
      return {
        client_email,
        found: false,
        message: 'No client history found',
      };
    }

    const leadIds = leads.map((lead) => lead.id);
    const quotePlaceholders = leadIds.map(() => '?').join(', ');
    const quotes = leadIds.length
      ? await all(
          `SELECT * FROM quotes
           WHERE lead_id IN (${quotePlaceholders})
           ORDER BY created_at DESC
           LIMIT 100`,
          leadIds
        )
      : [];

    const quoteIds = quotes.map((quote) => quote.id);
    const paymentPlaceholders = quoteIds.map(() => '?').join(', ');
    const payments = quoteIds.length
      ? await all(
          `SELECT * FROM payments
           WHERE quote_id IN (${paymentPlaceholders})
           ORDER BY COALESCE(received_date, created_at) DESC
           LIMIT 100`,
          quoteIds
        )
      : [];

    const acceptedQuotes = quotes.filter((quote) => ['accepted', 'invoiced'].includes(quote.status));
    const openQuotes = quotes.filter((quote) => ['draft', 'sent', 'invoiced'].includes(quote.status));
    const totalPaid = payments.reduce((sum, payment) => sum + Number(payment.amount || 0), 0);
    const averageQuoteValue = quotes.length
      ? Number((quotes.reduce((sum, quote) => sum + Number(quote.total_amount || 0), 0) / quotes.length).toFixed(2))
      : 0;

    const activityTimestamps = [
      ...leads.flatMap((lead) => [lead.updated_at, lead.created_at]),
      ...quotes.flatMap((quote) => [quote.accepted_date, quote.sent_date, quote.updated_at, quote.created_at]),
      ...payments.flatMap((payment) => [payment.received_date, payment.created_at]),
    ].filter(Boolean);

    activityTimestamps.sort((a, b) => new Date(b).getTime() - new Date(a).getTime());

    return {
      client_email,
      found: true,
      client_name: leads[0].client_name,
      repeat_customer: leads.length > 1 || acceptedQuotes.length > 1,
      preferred_contact: leads.some((lead) => lead.phone) ? 'phone' : 'email',
      total_leads: leads.length,
      total_quotes: quotes.length,
      accepted_quotes: acceptedQuotes.length,
      open_quotes: openQuotes.length,
      total_paid: Number(totalPaid.toFixed(2)),
      average_quote_value: averageQuoteValue,
      job_types: unique(leads.map((lead) => lead.job_type)),
      locations: unique(leads.map((lead) => lead.location)),
      last_activity_at: activityTimestamps[0] || null,
      recent_leads: leads.slice(0, 5),
      recent_quotes: quotes.slice(0, 5),
      recent_payments: payments.slice(0, 5),
    };
  },
};

runServer({ name: 'backpocket-leads', tools, handlers });
