// Prints the top passages for sample questions, to judge search by meaning.  node eval.mjs ["question"...]
import fs from 'node:fs';
import { pipeline } from '@huggingface/transformers';
import { passages, AI_MODEL, AI_DIMS } from '../../scripts/ai_chunks.mjs';
const R='../../';
const index=JSON.parse(fs.readFileSync(R+'dist/search-index.json','utf8'));
const items=passages(index);
const vec=new Int8Array(fs.readFileSync(R+'data/ai/vectors.bin'));
const embed=await pipeline('feature-extraction',AI_MODEL,{dtype:'q8'});
const P='Represent this sentence for searching relevant passages: ';
const Q=process.argv.length>2?process.argv.slice(2):[
'can a director borrow money from the company',
'how many directors must a private company have',
'who can be appointed as auditor of a company',
'penalty for not filing annual return',
'what happens if a company does not hold its annual general meeting',
'can a company buy back its own shares',
'how do I close down a company voluntarily',
'beneficial owner disclosure',
'tax on salary paid to employees',
'tax withheld when paying rent for a building',
'reporting suspicious transactions to the financial monitoring unit',
'money laundering punishment',
'sales tax registration threshold for a retailer',
'can the commission search premises and seize records',
'minimum number of members for a limited liability partnership',
'who regulates clearing houses',
'related party transactions approval by board',
'company name similar to an existing company',
'shareholder oppressed by majority what remedy',
'late filing of income tax return penalty',
];
for(const q of Q){
 const e=await embed(P+q,{pooling:'cls',normalize:true});
 const s=new Float32Array(items.length);
 for(let i=0;i<items.length;i++){let d=0;for(let j=0;j<AI_DIMS;j++)d+=e.data[j]*vec[i*AI_DIMS+j];s[i]=d/254;}
 const seen=new Set(),top=[];
 for(const i of [...s.keys()].sort((a,b)=>s[b]-s[a])){if(seen.has(items[i].prov))continue;seen.add(items[i].prov);top.push(i);if(top.length==5)break;}
 console.log('\nQ: '+q);
 for(const i of top){const p=index.provisions[items[i].prov];console.log(`  ${s[i].toFixed(3)} ${p.act} | ${p.no} ${p.title}`.slice(0,110));}
}
