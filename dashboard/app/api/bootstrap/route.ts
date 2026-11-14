import { env } from 'cloudflare:workers';
import seed from '../../../lib/snapshot.json';
import reviews from '../../../lib/processed-reviews.json';
export async function POST(request: Request) {
  if (request.headers.get('origin') !== new URL(request.url).origin) return new Response('Origin rejected',{status:403});
  if (!request.headers.get('oai-authenticated-user-id')) return new Response('Sign in required',{status:401});
  const offset=Number(new URL(request.url).searchParams.get('offset')||0);
  if (!Number.isInteger(offset)||offset<0||offset%100||offset>=reviews.length) return new Response('Invalid offset',{status:400});
  const rows=reviews.slice(offset,offset+100);
  const put=(id:string,payload:unknown)=>env.DB.prepare('INSERT INTO snapshots(id,payload,source_hash,updated_at) VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,source_hash=excluded.source_hash,updated_at=excluded.updated_at').bind(id,JSON.stringify(payload),seed.analysis_sha256,seed.updatedAt);
  await env.DB.batch([put(`reviews:${seed.analysis_sha256}:${offset}`,rows)]);
  const next=offset+100<reviews.length?offset+100:null;
  if(next===null) {
    const stored=await env.DB.prepare('SELECT count(*) AS n FROM snapshots WHERE source_hash=? AND id != ? AND updated_at=?').bind(seed.analysis_sha256,'current',seed.updatedAt).first();
    if(Number(stored?.n)!==Math.ceil(reviews.length/100))return new Response('Import incomplete; restart load',{status:409});
    await put('current',seed).run();
  }
  return Response.json({ok:true,next,loaded:Math.min(offset+100,reviews.length)});
}
