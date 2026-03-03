#!/usr/bin/env node
const { Client } = require('pg');

async function main() {
  const dbUrl = process.env.DATABASE_URL;
  if (!dbUrl) {
    console.error('FAIL: DATABASE_URL missing');
    process.exit(2);
  }
  const client = new Client({ connectionString: dbUrl, ssl: { rejectUnauthorized: false } });
  await client.connect();
  try {
    const blocked = await client.query(`select id,title,description from tasks where coalesce(status,'todo')='blocked' order by priority asc limit 20`);
    const overdue = await client.query(`select id,title,description from tasks where coalesce(status,'todo') in ('todo','open','doing','in_progress','blocked') and coalesce(due_ts,due_at) < now() order by priority asc limit 20`);
    const stale = await client.query(`select id,title,description from tasks where coalesce(status,'todo') in ('todo','open','doing','in_progress','blocked') and (last_review_ts is null or last_review_ts < now()- interval '7 days') order by priority asc limit 20`);

    console.log('OPEN LOOPS');
    console.log(`- blocked: ${blocked.rows.length}`);
    console.log(`- overdue: ${overdue.rows.length}`);
    console.log(`- unreviewed_7d: ${stale.rows.length}`);

    const blockersRequiringInput = blocked.rows.filter(r => /user|confirm|credential|input/i.test((r.description||'') + ' ' + (r.title||'')));
    if (blockersRequiringInput.length) {
      console.log('\nACTION REQUIRED (blocked tasks need user input):');
      for (const b of blockersRequiringInput.slice(0, 10)) {
        console.log(`- ${b.id}: ${b.title}`);
      }
    }

    if (overdue.rows.length || stale.rows.length) {
      console.log('\nRESURFACE: critical open loops detected. Request direction if no progress.');
    }
  } finally {
    await client.end();
  }
}

main().catch(e => {
  console.error('FAIL', e.message);
  process.exit(1);
});
