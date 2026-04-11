#!/usr/bin/env node

/**
 * BackPocket Local MCP Server
 *
 * Provides tradie-specific tools for:
 * - Local database access (SQLite)
 * - Learned patterns (ChromaDB)
 * - Business logic (quote generation, job matching)
 * - Integration with other MCP servers (Gmail, Maps, Drive)
 */

const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const DB_PATH = process.env.LOCAL_DB_PATH || './backpocket.db';

// Simple MCP server implementation (stdio transport)
class BackPocketMCPServer {
  constructor() {
    this.db = null;
    this.tools = this.initTools();
  }

  async init() {
    return new Promise((resolve, reject) => {
      this.db = new sqlite3.Database(DB_PATH, (err) => {
        if (err) {
          console.error(`Error opening database at ${DB_PATH}:`, err.message);
          reject(err);
        } else {
          console.error(`[MCP] Connected to BackPocket DB at ${DB_PATH}`);
          resolve();
        }
      });
    });
  }

  initTools() {
    return {
      // ===== LEAD MANAGEMENT =====
      'search_leads': {
        description: 'Search for construction leads by criteria',
        inputSchema: {
          type: 'object',
          properties: {
            status: { type: 'string', description: 'Filter by status (new, quoted, accepted)' },
            job_type: { type: 'string', description: 'Job type (Kitchen, Deck, Emergency, etc)' },
            urgency: { type: 'string', description: 'Urgency level (high, medium, low)' },
            min_budget: { type: 'number', description: 'Minimum budget' },
            location: { type: 'string', description: 'Location or suburb' }
          }
        }
      },

      'create_quote': {
        description: 'Generate a quote for a lead with tradie pricing',
        inputSchema: {
          type: 'object',
          properties: {
            lead_id: { type: 'number', description: 'Lead ID' },
            materials_cost: { type: 'number', description: 'Material costs' },
            labor_hours: { type: 'number', description: 'Labor hours at $150/hr' },
            markup_percent: { type: 'number', description: 'Markup percentage (default 20)' }
          },
          required: ['lead_id', 'materials_cost', 'labor_hours']
        }
      },

      'get_quote_template': {
        description: 'Get pricing template for job type (e.g., Kitchen = $150/hr)',
        inputSchema: {
          type: 'object',
          properties: {
            job_type: { type: 'string', description: 'Job type (Kitchen, Plumbing, Electrical, etc)' }
          },
          required: ['job_type']
        }
      },

      // ===== LOCATION & ROUTING =====
      'calculate_job_distance': {
        description: 'Calculate distance from home base to job location (for Google Maps)',
        inputSchema: {
          type: 'object',
          properties: {
            from_location: { type: 'string', description: 'Start location (e.g., Alexandria)' },
            to_location: { type: 'string', description: 'Job location' },
            traffic: { type: 'boolean', description: 'Include traffic calculation (default true)' }
          },
          required: ['from_location', 'to_location']
        }
      },

      'estimate_travel_time': {
        description: 'Estimate travel time to job and suggest calendar block',
        inputSchema: {
          type: 'object',
          properties: {
            job_location: { type: 'string', description: 'Job address' },
            job_duration_hours: { type: 'number', description: 'Estimated job duration' },
            include_buffer: { type: 'boolean', description: 'Add 30min buffer before/after' }
          },
          required: ['job_location', 'job_duration_hours']
        }
      },

      // ===== PAYMENT & PIPELINE =====
      'get_pipeline_summary': {
        description: 'Get current quote pipeline status',
        inputSchema: {
          type: 'object',
          properties: {}
        }
      },

      'record_payment': {
        description: 'Record a payment received for a quote',
        inputSchema: {
          type: 'object',
          properties: {
            quote_id: { type: 'number', description: 'Quote ID' },
            amount: { type: 'number', description: 'Amount received' },
            payment_date: { type: 'string', description: 'Date of payment (ISO format)' }
          },
          required: ['quote_id', 'amount']
        }
      },

      'get_overdue_quotes': {
        description: 'Get list of quotes sent but not accepted (over 7 days)',
        inputSchema: {
          type: 'object',
          properties: {
            days_threshold: { type: 'number', description: 'Days since sent (default 7)' }
          }
        }
      },

      // ===== LEARNED PATTERNS =====
      'get_job_patterns': {
        description: 'Get learned patterns for a job type (price history, duration, common issues)',
        inputSchema: {
          type: 'object',
          properties: {
            job_type: { type: 'string', description: 'Job type' },
            location: { type: 'string', description: 'Suburb/area' }
          },
          required: ['job_type']
        }
      },

      'get_client_history': {
        description: 'Get client history (past jobs, preferred communication, repeat patterns)',
        inputSchema: {
          type: 'object',
          properties: {
            client_email: { type: 'string', description: 'Client email address' }
          },
          required: ['client_email']
        }
      },

      // ===== INTEGRATION HELPERS =====
      'draft_follow_up_email': {
        description: 'Generate follow-up email template (for Gmail MCP to send)',
        inputSchema: {
          type: 'object',
          properties: {
            quote_id: { type: 'number', description: 'Quote ID to follow up on' },
            tone: { type: 'string', enum: ['friendly', 'professional', 'urgent'], description: 'Email tone' }
          },
          required: ['quote_id']
        }
      },

      'match_quote_to_email': {
        description: 'Match an incoming email to a quote (for automated follow-up)',
        inputSchema: {
          type: 'object',
          properties: {
            email_from: { type: 'string', description: 'Sender email' },
            email_subject: { type: 'string', description: 'Email subject' },
            email_body: { type: 'string', description: 'Email body' }
          },
          required: ['email_from', 'email_subject', 'email_body']
        }
      },

      'suggest_next_action': {
        description: 'AI suggests next action based on current pipeline state',
        inputSchema: {
          type: 'object',
          properties: {
            context: { type: 'string', enum: ['new_lead', 'quote_sent', 'quote_accepted', 'payment_received'], description: 'Current context' }
          },
          required: ['context']
        }
      }
    };
  }

  // Tool implementations
  async execute(toolName, args) {
    switch (toolName) {
      case 'search_leads':
        return this.searchLeads(args);
      case 'create_quote':
        return this.createQuote(args);
      case 'get_quote_template':
        return this.getQuoteTemplate(args);
      case 'get_pipeline_summary':
        return this.getPipelineSummary();
      case 'record_payment':
        return this.recordPayment(args);
      case 'get_overdue_quotes':
        return this.getOverdueQuotes(args);
      case 'get_job_patterns':
        return this.getJobPatterns(args);
      case 'calculate_job_distance':
        return this.calculateJobDistance(args);
      case 'estimate_travel_time':
        return this.estimateTravelTime(args);
      case 'draft_follow_up_email':
        return this.draftFollowUpEmail(args);
      case 'match_quote_to_email':
        return this.matchQuoteToEmail(args);
      case 'suggest_next_action':
        return this.suggestNextAction(args);
      default:
        return { error: `Unknown tool: ${toolName}` };
    }
  }

  searchLeads(args) {
    return new Promise((resolve, reject) => {
      let query = 'SELECT * FROM leads WHERE 1=1';
      const params = [];

      if (args.status) {
        query += ' AND status = ?';
        params.push(args.status);
      }
      if (args.job_type) {
        query += ' AND job_type LIKE ?';
        params.push(`%${args.job_type}%`);
      }
      if (args.urgency) {
        query += ' AND urgency = ?';
        params.push(args.urgency);
      }
      if (args.min_budget) {
        query += ' AND estimated_budget >= ?';
        params.push(args.min_budget);
      }
      if (args.location) {
        query += ' AND location LIKE ?';
        params.push(`%${args.location}%`);
      }

      query += ' ORDER BY created_at DESC LIMIT 50';

      this.db.all(query, params, (err, rows) => {
        if (err) {
          reject(err);
        } else {
          resolve({
            count: rows.length,
            leads: rows
          });
        }
      });
    });
  }

  createQuote(args) {
    const laborCost = (args.labor_hours || 0) * 150; // $150/hr standard rate
    const subtotal = (args.materials_cost || 0) + laborCost;
    const markup = args.markup_percent || 20;
    const total = subtotal * (1 + markup / 100);

    return new Promise((resolve, reject) => {
      const query = `
        INSERT INTO quotes (lead_id, materials_cost, labor_cost, markup_percent, total_amount, status)
        VALUES (?, ?, ?, ?, ?, 'draft')
      `;
      this.db.run(query, [
        args.lead_id,
        args.materials_cost,
        laborCost,
        markup,
        total
      ], function(err) {
        if (err) {
          reject(err);
        } else {
          resolve({
            quote_id: this.lastID,
            materials: args.materials_cost,
            labor: laborCost,
            subtotal: subtotal,
            markup_percent: markup,
            total_amount: total
          });
        }
      });
    });
  }

  getQuoteTemplate(args) {
    const templates = {
      'Kitchen': { rate: 150, materials_buffer: 0.3, avg_duration: 5 },
      'Bathroom': { rate: 150, materials_buffer: 0.3, avg_duration: 4 },
      'Plumbing': { rate: 150, materials_buffer: 0.2, avg_duration: 3 },
      'Electrical': { rate: 160, materials_buffer: 0.25, avg_duration: 2 },
      'Deck': { rate: 140, materials_buffer: 0.4, avg_duration: 3 },
      'Emergency': { rate: 200, materials_buffer: 0.2, avg_duration: 1 },
      'General': { rate: 150, materials_buffer: 0.25, avg_duration: 2 }
    };

    const template = templates[args.job_type] || templates['General'];
    return {
      job_type: args.job_type,
      labor_rate: template.rate + '/hour',
      materials_markup: (template.materials_buffer * 100) + '%',
      estimated_duration: template.avg_duration + ' hours',
      note: 'Based on historical tradie pricing in Sydney region'
    };
  }

  getPipelineSummary() {
    return new Promise((resolve, reject) => {
      this.db.all(`
        SELECT
          COUNT(*) as total_quotes,
          SUM(CASE WHEN status='draft' THEN 1 ELSE 0 END) as draft,
          SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) as sent,
          SUM(CASE WHEN status='accepted' THEN 1 ELSE 0 END) as accepted,
          SUM(CASE WHEN status IN ('accepted', 'invoiced') THEN total_amount ELSE 0 END) as revenue_pipeline
        FROM quotes
      `, (err, rows) => {
        if (err) {
          reject(err);
        } else {
          const row = rows[0] || {};
          resolve({
            total_quotes: row.total_quotes || 0,
            draft: row.draft || 0,
            sent: row.sent || 0,
            accepted: row.accepted || 0,
            revenue_pipeline: row.revenue_pipeline || 0
          });
        }
      });
    });
  }

  recordPayment(args) {
    return new Promise((resolve, reject) => {
      const paymentDate = args.payment_date || new Date().toISOString();
      this.db.run(`
        INSERT INTO payments (quote_id, amount, received_date, status)
        VALUES (?, ?, ?, 'received')
      `, [args.quote_id, args.amount, paymentDate], function(err) {
        if (err) {
          reject(err);
        } else {
          resolve({
            payment_id: this.lastID,
            quote_id: args.quote_id,
            amount: args.amount,
            status: 'received'
          });
        }
      });
    });
  }

  getOverdueQuotes(args) {
    const daysThreshold = args.days_threshold || 7;
    return new Promise((resolve, reject) => {
      this.db.all(`
        SELECT id, client_name, job_type, total_amount, sent_date
        FROM quotes
        WHERE status='sent' AND datetime(sent_date, '+${daysThreshold} days') < datetime('now')
        ORDER BY sent_date ASC
      `, (err, rows) => {
        if (err) {
          reject(err);
        } else {
          resolve({
            count: rows.length,
            overdue_quotes: rows,
            message: rows.length > 0 ? `${rows.length} quotes overdue - consider follow-up` : 'No overdue quotes'
          });
        }
      });
    });
  }

  getJobPatterns(args) {
    // Mock learned patterns (in production, pull from ChromaDB)
    const patterns = {
      'Kitchen': {
        avg_price: 8500,
        avg_duration: 5,
        materials_percentage: 40,
        common_issues: ['Cabinet alignment', 'Plumbing conflicts', 'Electrical upgrades'],
        repeat_rate: 0.65
      },
      'Plumbing': {
        avg_price: 2100,
        avg_duration: 2,
        materials_percentage: 35,
        common_issues: ['Hidden corrosion', 'Access difficulty', 'Code compliance'],
        repeat_rate: 0.78
      }
    };

    const pattern = patterns[args.job_type] || {
      avg_price: 3000,
      avg_duration: 2.5,
      materials_percentage: 35,
      common_issues: ['Access', 'Hidden issues', 'Timeline'],
      repeat_rate: 0.5
    };

    if (args.location) {
      pattern.location = args.location;
      pattern.local_multiplier = 1.1; // +10% for metro areas
    }

    return pattern;
  }

  calculateJobDistance(args) {
    // Mock response (in production, use Google Maps MCP)
    return {
      from: args.from_location,
      to: args.to_location,
      distance_km: 15.3,
      estimated_travel_time: '25 minutes',
      note: 'Use Google Maps MCP for real calculation'
    };
  }

  estimateTravelTime(args) {
    const duration = args.job_duration_hours || 2;
    const buffer = args.include_buffer ? 1 : 0; // 30min before + after
    const totalTime = duration + buffer;

    return {
      job_location: args.job_location,
      job_duration: duration + ' hours',
      travel_buffer: buffer + ' hours (30min before, 30min after)',
      total_calendar_block: totalTime + ' hours',
      suggested_time_slot: 'Morning (8am) or Afternoon (1pm) for optimal schedule'
    };
  }

  draftFollowUpEmail(args) {
    const tone = args.tone || 'friendly';
    const templates = {
      friendly: `Hi, just checking in on the quote I sent over. Hope it all made sense. My schedule is filling up fast, so let me know if you want to lock in a date. Cheers!`,
      professional: `I wanted to follow up regarding the quote submitted last week. Please let me know if you have any questions or if you'd like to proceed.`,
      urgent: `Quick follow-up: I have availability next week to start your job, but my schedule is tight. Please confirm within 48 hours if interested.`
    };

    return {
      quote_id: args.quote_id,
      tone: tone,
      email_body: templates[tone],
      subject_suggestion: `Follow-up: Your Quote from BackPocket`,
      action: 'Ready to send via Gmail MCP'
    };
  }

  matchQuoteToEmail(args) {
    // Mock matching (in production, use semantic similarity from ChromaDB)
    return {
      status: 'analysis_complete',
      email_from: args.email_from,
      matched_quote_ids: [1, 2], // Would be semantic search result
      confidence: 0.85,
      suggested_action: 'Send follow-up or update quote status'
    };
  }

  suggestNextAction(args) {
    const actions = {
      'new_lead': 'Send quote within 24 hours for best conversion',
      'quote_sent': 'Follow up in 5 days if no response',
      'quote_accepted': 'Schedule site visit and confirm start date',
      'payment_received': 'Send invoice and thank you email'
    };

    return {
      context: args.context,
      suggested_action: actions[args.context] || 'Unknown context',
      next_steps: ['Update CRM', 'Calendar block', 'Send communication']
    };
  }

  // MCP Protocol: handle stdin/stdout messages
  async handleRequest(request) {
    try {
      const { jsonrpc, id, method, params } = request;

      if (method === 'tools/list') {
        return {
          jsonrpc,
          id,
          result: {
            tools: Object.entries(this.tools).map(([name, config]) => ({
              name,
              ...config
            }))
          }
        };
      }

      if (method === 'tools/call') {
        const result = await this.execute(params.name, params.arguments);
        return {
          jsonrpc,
          id,
          result: {
            content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
          }
        };
      }

      return {
        jsonrpc,
        id,
        error: { code: -32601, message: 'Method not found' }
      };
    } catch (error) {
      return {
        jsonrpc,
        id,
        error: { code: -32603, message: error.message }
      };
    }
  }

  async start() {
    await this.init();
    console.error('[MCP] BackPocket Local MCP Server started');

    // Read from stdin, write to stdout (MCP protocol)
    process.stdin.on('data', async (data) => {
      try {
        const request = JSON.parse(data.toString());
        const response = await this.handleRequest(request);
        process.stdout.write(JSON.stringify(response) + '\n');
      } catch (error) {
        console.error('[MCP Error]', error);
      }
    });
  }
}

// Start server
const server = new BackPocketMCPServer();
server.start().catch(console.error);
