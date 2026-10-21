'use strict';
// Original case builder, geometry preserved; guards/CLI added during transfer.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const EXPECTED = Object.freeze({"scenario":"pipe-lattice-v002","units":"m","center_x":43.34540939331055,"sectors":18,"half_rows":16,"gap_m":0.0102,"depth_m":0.12,"inset_m":0.12,"source_sha256":"1d1aa779878f0dae5c42d259f1adef636ccbb397938f1a6519cd4a5564b8b1ee","reference_sha256":"cafd07441d1ab77159c3a0bc54d0e0b11181604b0979d30f0bd91c3d82634024"});
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k=>[k,canonical(value[k])]));
  return value;
}
function validateConfig(config) {
  if (JSON.stringify(canonical(config)) !== JSON.stringify(canonical(EXPECTED))) throw Error('Unsupported scenario/config drift');
}
function validateSource(source) {
  if (!Array.isArray(source) || source.length!==126 || source.some((row,i)=>!row || row.i!==i+1 || !Array.isArray(row.pos) || row.pos.length!==3 || row.pos.some(v=>typeof v!=='number'||!Number.isFinite(v)))) throw Error('Expected 126 ordered {i,pos:[x,y,z]} source rows');
  const rings=source.filter((_,i)=>i%18===0);
  if(rings.some((r,i)=>i && r.pos[2]<=rings[i-1].pos[2])) throw Error('Expected seven ascending profile rings');
}
function build(source, config=EXPECTED) { validateConfig(config);validateSource(source); return buildGeometry(source,config); }
function buildGeometry(source, config) {
const {center_x:cx,sectors:N,half_rows:J}=config,co=Math.cos(Math.PI/N);
const rings=source.filter(v=>(v.i-1)%18===0).map(v=>({z:v.pos[2],a:(v.pos[0]-cx)*co}));
const z0=rings[0].z,z1=rings.at(-1).z;
const lines=rings.slice(0,-1).map((p,i)=>{let q=rings[i+1],m=(q.a-p.a)/(q.z-p.z);return{m,b:p.a-m*p.z,k:Math.hypot(1,m)};});
function offsets(d){return rings.map((p,i)=>{if(i===0||i===rings.length-1){let l=lines[i===0?0:lines.length-1];return{z:p.z,a:l.m*p.z+l.b+d*l.k};}let l=lines[i-1],r=lines[i]; if(Math.abs(l.m-r.m)<1e-10)return{z:p.z,a:p.a+d*l.k};let z=(r.b-l.b+d*(r.k-l.k))/(l.m-r.m);return{z,a:l.m*z+l.b+d*l.k};});}
const inner=offsets(config.gap_m),outer=offsets(config.gap_m+config.depth_m);
function map(p,off){let u=p[0],z=p[1],si=Math.min(17,Math.floor(u+1e-9)),f=u-si,ri=rings.findIndex((r,i)=>i<rings.length-1&&z<=rings[i+1].z+1e-7);ri=Math.max(0,ri);let t=(z-rings[ri].z)/(rings[ri+1].z-rings[ri].z),a=off[ri].a*(1-t)+off[ri+1].a*t,zz=off[ri].z*(1-t)+off[ri+1].z*t,R=a/co,ang=si*2*Math.PI/N,ang2=(si+1)*2*Math.PI/N;return[cx+R*((1-f)*Math.cos(ang)+f*Math.cos(ang2)),R*((1-f)*Math.sin(ang)+f*Math.sin(ang2)),zz];}
function clip(poly,axis,value,sgn){let out=[];for(let i=0;i<poly.length;i++){let a=poly[i],b=poly[(i+1)%poly.length],da=sgn*(a[axis]-value),db=sgn*(b[axis]-value);if(da>=-1e-9)out.push(a);if((da>1e-9&&db<-1e-9)||(da<-1e-9&&db>1e-9)){let t=da/(da-db);out.push([a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t]);}} return out.filter((p,i)=>Math.hypot(p[0]-out[(i+out.length-1)%out.length][0],p[1]-out[(i+out.length-1)%out.length][1])>1e-8);}
function inset(poly,d,width){let scaled=poly.map(p=>[p[0]*width,p[1]]);return scaled.map((p,i)=>{let prev=scaled[(i+2)%3],next=scaled[(i+1)%3];function line(a,b){let dx=b[0]-a[0],dy=b[1]-a[1],l=Math.hypot(dx,dy);return{a:[a[0]-dy/l*d,a[1]+dx/l*d],v:[dx,dy]};}let l=line(prev,p),m=line(p,next),cross=(a,b)=>a[0]*b[1]-a[1]*b[0],t=cross([m.a[0]-l.a[0],m.a[1]-l.a[1]],m.v)/cross(l.v,m.v);return[(l.a[0]+t*l.v[0])/width,l.a[1]+t*l.v[1]];});}
const uv=[],idx=new Map(),front=[];
function id(p){let u=Math.abs(p[0]-N)<1e-7?0:p[0],key=[u,p[1]].map(v=>Math.round(v*1e7)).join(',');if(!idx.has(key)){idx.set(key,uv.length);uv.push([u,p[1]]);}return idx.get(key);}
for(let j=0;j<J;j++){let za=z0+(z1-z0)*j/J,zb=z0+(z1-z0)*(j+1)/J,s=(j%2)*.5;let zm=(za+zb)/2,ri=Math.max(0,rings.findIndex((r,k)=>k<6&&zm<=rings[k+1].z)),tt=(zm-rings[ri].z)/(rings[ri+1].z-rings[ri].z),width=2*(rings[ri].a*(1-tt)+rings[ri+1].a*tt)*Math.tan(Math.PI/18);
for(let i=-2;i<N+1;i++)for(let tri of [[[i+s,za],[i+1+s,za],[i+.5+s,zb]],[[i+1+s,za],[i+1.5+s,zb],[i+.5+s,zb]]]){
let ins=inset(tri,.12,width);for(let e=0;e<3;e++){let ring=[tri[e],tri[(e+1)%3],ins[(e+1)%3],ins[e]];let minU=Math.max(0,Math.floor(Math.min(...ring.map(p=>p[0])))),maxU=Math.min(N-1,Math.floor(Math.max(...ring.map(p=>p[0]))));for(let u=minU;u<=maxU;u++)for(let r=0;r<6;r++){if(zb<rings[r].z||za>rings[r+1].z)continue;let poly=ring;for(const[ax,val,sgn]of[[0,u,1],[0,u+1,-1],[1,rings[r].z,1],[1,rings[r+1].z,-1]])poly=clip(poly,ax,val,sgn);if(poly.length<3)continue;let area=poly.reduce((a,p,k)=>a+p[0]*poly[(k+1)%poly.length][1]-p[1]*poly[(k+1)%poly.length][0],0);if(area<1e-10)continue;let center=poly.reduce((a,p)=>[a[0]+p[0]/poly.length,a[1]+p[1]/poly.length],[0,0]);for(let k=0;k<poly.length;k++){let p=poly[k],q=poly[(k+1)%poly.length],prev=poly[(k+poly.length-1)%poly.length];front.push([id(p),id([(p[0]+q[0])/2,(p[1]+q[1])/2]),id(center),id([(p[0]+prev[0])/2,(p[1]+prev[1])/2])]);}}}
}}
let count=uv.length,vertices=uv.map(p=>map(p,outer)).concat(uv.map(p=>map(p,inner))),faces=front.concat(front.map(f=>f.map(v=>v+count).reverse()));
let edges=new Map();for(let f of front)for(let k=0;k<4;k++){let a=f[k],b=f[(k+1)%4],key=[Math.min(a,b),Math.max(a,b)].join(',');if(edges.has(key))edges.get(key).count++;else edges.set(key,{a,b,count:1});}
for(let {a,b,count:c}of edges.values())if(c===1)faces.push([b,a,a+count,b+count]);else if(c!==2)throw Error('Bad surface edge');
return{name:'DECOR_GEO_FULL_v002',vertices,faces:faces.map(f=>f.map(v=>v+1)),parameters:{N,J,inset:.12,depth:.12,gap:config.gap_m,rings,inner,outer},uv,front};
}

function hash(bytes) {return crypto.createHash('sha256').update(bytes).digest('hex');}
function readBound(filename, expectedHash, label) {
  const bytes=fs.readFileSync(filename);
  if(hash(bytes)!==expectedHash) throw Error(label+' SHA256 mismatch');
  return JSON.parse(bytes.toString('utf8'));
}
function compare(mesh, reference) {
  if(mesh.vertices.length!==reference.vertices.length || JSON.stringify(mesh.faces)!==JSON.stringify(reference.faces)) throw Error('Reference topology mismatch');
  let max=0;
  for(let i=0;i<mesh.vertices.length;i++) for(let j=0;j<3;j++) {
    const error=Math.abs(mesh.vertices[i][j]-reference.vertices[i][j]);
    if(!Number.isFinite(error)) throw Error('Nonfinite coordinate');
    max=Math.max(max,error);
  }
  if(max>1e-12) throw Error('Reference coordinates differ beyond 1e-12 m');
  return max;
}
function run(args) {
  const allowed=['--source','--reference','--output-directory','--config'];
  const options={};
  for(let i=0;i<args.length;i+=2) {
    if(!allowed.includes(args[i]) || !args[i+1] || Object.hasOwn(options,args[i])) throw Error('Use --source ABS --reference ABS --output-directory NEW_ABS [--config ABS]');
    options[args[i]]=args[i+1];
  }
  for(const key of allowed.slice(0,3)) if(!options[key] || !path.isAbsolute(options[key])) throw Error(key+' must be absolute');
  if(options['--config'] && !path.isAbsolute(options['--config'])) throw Error('--config must be absolute');
  const destination=options['--output-directory'];
  if(fs.existsSync(destination)) throw Error('Output directory exists; refusing overwrite');
  const config=JSON.parse(fs.readFileSync(options['--config']||path.join(__dirname,'scenario.json'),'utf8'));
  validateConfig(config);
  const source=readBound(options['--source'],config.source_sha256,'Source');
  const reference=readBound(options['--reference'],config.reference_sha256,'Reference');
  const mesh=build(source,config), max=compare(mesh,reference);
  // The original intermediate UV/front arrays are geometry recipes, not texture UVs.
  const output={name:mesh.name,vertices:mesh.vertices,faces:mesh.faces,parameters:mesh.parameters};
  const bytes=JSON.stringify(output)+'\n';
  const report={scenario:config.scenario,units:'m',source_sha256:config.source_sha256,reference_sha256:config.reference_sha256,mesh_sha256:hash(bytes),vertices:mesh.vertices.length,faces:mesh.faces.length,ordered_faces_equal:true,max_coordinate_error_m:max,coordinate_tolerance_m:1e-12,gap_m:config.gap_m,geometry_replay_passed:true,delivery_passed:false,native_reopen:'not performed',posts_builder:'not transferred',texture_variant:'not transferred'};
  // mkdir without recursive makes an existing directory/racing writer a hard failure.
  fs.mkdirSync(destination);
  fs.writeFileSync(path.join(destination,'mesh.json'),bytes,{flag:'wx'});
  fs.writeFileSync(path.join(destination,'report.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify(report));
  return report;
}
module.exports={build,run,validateConfig,validateSource};
if(require.main===module) { try {run(process.argv.slice(2));} catch(error) {console.error(error.message);process.exitCode=1;} }
