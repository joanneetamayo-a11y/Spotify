import progress from '../../../lib/progress.json';
import seed from '../../../lib/snapshot.json';
import { env } from 'cloudflare:workers';
export async function GET() {
  const result = await env.DB.prepare('SELECT payload, updated_at FROM snapshots WHERE id = ?').bind('current').first();
  if (!result || JSON.parse(String(result.payload)).updatedAt !== seed.updatedAt) return Response.json({status:'awaiting_import'}, {status:404});
  return Response.json({...JSON.parse(String(result.payload)), databaseUpdatedAt:result.updated_at,...progress}, {headers:{'Cache-Control':'no-store'}});
}
