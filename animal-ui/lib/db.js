import { Pool } from 'pg';

let pool;

export function getDb() {
  if (!process.env.DATABASE_URL) {
    throw new Error('DATABASE_URL missing');
  }
  if (!pool) {
    pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: { rejectUnauthorized: false },
      max: 5
    });
  }
  return pool;
}
