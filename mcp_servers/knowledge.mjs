#!/usr/bin/env node
// Shared knowledge bank — anyone on the team drops notes here, AI tools read from here.
// Schema is created by scripts/create_knowledge_table.py.

import { all, get, run } from './_lib/db.mjs';
import { runServer } from './_lib/mcp.mjs';
import { execSync } from 'node:child_process';

function gitAuthor() {
  try {
    const name = execSync('git config user.name', { encoding: 'utf8' }).trim();
    const email = execSync('git config user.email', { encoding: 'utf8' }).trim();
    const branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
    return { name, email, branch };
  } catch { return { name: null, email: null, branch: null }; }
}

const tools = {
  save_note: {
    description: 'Save a note to the shared knowledge bank with author signature',
    inputSchema: {
      type: 'object',
      properties: {
        category: { type: 'string', description: 'marketing | law | research | engineering | other' },
        title: { type: 'string' },
        body: { type: 'string' },
        tags: { type: 'string', description: 'comma-separated' },
      },
      required: ['category', 'title', 'body'],
    },
  },
  search_notes: {
    description: 'Keyword search across title/body/tags. Optionally filter by category or author.',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string' },
        category: { type: 'string' },
        author_email: { type: 'string' },
      },
    },
  },
  list_notes: {
    description: 'List most recent notes (max 50), optionally filtered by category',
    inputSchema: { type: 'object', properties: { category: { type: 'string' } } },
  },
  get_note: {
    description: 'Get one note by id',
    inputSchema: { type: 'object', properties: { id: { type: 'number' } }, required: ['id'] },
  },
};

const handlers = {
  async save_note({ category, title, body, tags }) {
    const { name, email, branch } = gitAuthor();
    const r = await run(
      `INSERT INTO knowledge_notes (category, title, body, tags, author_name, author_email, branch, source)
       VALUES (?, ?, ?, ?, ?, ?, ?, 'manual')`,
      [category, title, body, tags || null, name, email, branch]
    );
    return { note_id: r.lastID, author: email, branch };
  },
  async search_notes({ query, category, author_email }) {
    const where = ['1=1'];
    const params = [];
    if (query) {
      where.push('(title LIKE ? OR body LIKE ? OR tags LIKE ?)');
      const q = `%${query}%`;
      params.push(q, q, q);
    }
    if (category) { where.push('category = ?'); params.push(category); }
    if (author_email) { where.push('author_email = ?'); params.push(author_email); }
    const rows = await all(
      `SELECT id, category, title, author_email, branch, commit_sha, created_at
       FROM knowledge_notes WHERE ${where.join(' AND ')}
       ORDER BY created_at DESC LIMIT 50`,
      params
    );
    return { count: rows.length, notes: rows };
  },
  async list_notes({ category }) {
    const rows = category
      ? await all('SELECT id, category, title, author_email, created_at FROM knowledge_notes WHERE category = ? ORDER BY created_at DESC LIMIT 50', [category])
      : await all('SELECT id, category, title, author_email, created_at FROM knowledge_notes ORDER BY created_at DESC LIMIT 50');
    return { count: rows.length, notes: rows };
  },
  async get_note({ id }) {
    return (await get('SELECT * FROM knowledge_notes WHERE id = ?', [id])) || { error: 'not found' };
  },
};

runServer({ name: 'backpocket-knowledge', tools, handlers });
