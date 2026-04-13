import sqlite3pkg from 'sqlite3';
import path from 'node:path';

const sqlite3 = sqlite3pkg.verbose();
const DB_PATH = process.env.LOCAL_DB_PATH || path.resolve(process.cwd(), 'backpocket.db');

let _db;
function db() {
  if (!_db) _db = new sqlite3.Database(DB_PATH);
  return _db;
}

export const all = (sql, params = []) =>
  new Promise((res, rej) => db().all(sql, params, (e, r) => (e ? rej(e) : res(r))));

export const get = (sql, params = []) =>
  new Promise((res, rej) => db().get(sql, params, (e, r) => (e ? rej(e) : res(r))));

export const run = (sql, params = []) =>
  new Promise((res, rej) =>
    db().run(sql, params, function (e) { e ? rej(e) : res({ lastID: this.lastID, changes: this.changes }); })
  );
