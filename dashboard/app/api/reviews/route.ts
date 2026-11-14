import { env } from 'cloudflare:workers';
export async function GET(request:Request){
 const offset=Number(new URL(request.url).searchParams.get('offset')||0);
 if(!Number.isInteger(offset)||offset<0||offset%100)return new Response('Offset must be a nonnegative multiple of 100',{status:400});
 const current=await env.DB.prepare('SELECT payload FROM snapshots WHERE id=?').bind('current').first();
 if(!current)return Response.json({status:'awaiting_import'},{status:404});
 const meta=JSON.parse(String(current.payload));
 const row=await env.DB.prepare('SELECT payload FROM snapshots WHERE id=?').bind(`reviews:${meta.analysis_sha256}:${offset}`).first();
 return Response.json({scope:meta.analysisCount,offset,reviews:row?JSON.parse(String(row.payload)):[],next:offset+100<meta.analysisCount?offset+100:null},{headers:{'Cache-Control':'no-store'}});
}
