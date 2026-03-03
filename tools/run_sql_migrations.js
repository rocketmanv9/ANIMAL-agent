#!/usr/bin/env node
const fs = require('fs');
const { Client } = require('pg');

function splitSql(sql) {
  const parts = [];
  let cur = '';
  let i = 0;
  let inSingle = false;
  let inDouble = false;
  let inDollar = false;
  while (i < sql.length) {
    const ch = sql[i];
    const next2 = sql.slice(i, i + 2);

    if (!inSingle && !inDouble && next2 === '$$') {
      inDollar = !inDollar;
      cur += next2;
      i += 2;
      continue;
    }

    if (!inDouble && !inDollar && ch === "'") inSingle = !inSingle;
    else if (!inSingle && !inDollar && ch === '"') inDouble = !inDouble;

    if (!inSingle && !inDouble && !inDollar && ch === ';') {
      if (cur.trim()) parts.push(cur.trim());
      cur = '';
      i++;
      continue;
    }

    cur += ch;
    i++;
  }
  if (cur.trim()) parts.push(cur.trim());
  return parts;
}

async function runFile(client, path) {
  const sql = fs.readFileSync(path, 'utf8');
  const stmts = splitSql(sql);
  for (const s of stmts) {
    await client.query(s);
  }
  return stmts.length;
}

async function main() {
  const dbUrl = process.env.DATABASE_URL;
  if (!dbUrl) {
    console.error('FAIL: DATABASE_URL missing');
    process.exit(2);
  }

  const files = process.argv.slice(2);
  if (!files.length) {
    console.error('Usage: run_sql_migrations.js <file1.sql> [file2.sql]');
    process.exit(2);
  }

  const client = new Client({ connectionString: dbUrl, ssl: { rejectUnauthorized: false } });
  await client.connect();
  try {
    for (const f of files) {
      const n = await runFile(client, f);
      console.log(`APPLIED ${f} (${n} statements)`);
    }
    console.log('MIGRATION_PASS');
  } finally {
    await client.end();
  }
}

main().catch((e) => {
  console.error('MIGRATION_FAIL', e.message);
  process.exit(1);
});
