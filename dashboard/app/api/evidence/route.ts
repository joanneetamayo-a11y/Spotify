import { env } from 'cloudflare:workers';
export async function GET(request: Request) {
  const issue = new URL(request.url).searchParams.get('issue');
  const row = await env.DB.prepare('SELECT payload FROM snapshots WHERE id=?').bind('current').first();
  if (!row) return Response.json({evidence:[]});
  const data = JSON.parse(String(row.payload));
  return Response.json({evidence:issue ? data.evidence[issue] || [] : data.evidence});
}
