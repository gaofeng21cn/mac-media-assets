import {PaperStage,phase,arc,lerp} from './paper-runtime.mjs';
const root=new URL('../../',location.href);
import {loadCatalog, available} from './catalog.mjs';
const [allRows,assemblies,kits,discovery,coverage] = await Promise.all([
 loadCatalog(root), ...['collections/assemblies.json','collections/event-kits.json','collections/discovery.json','collections/character-coverage.json'].map(async p=>{const response=await fetch(new URL(p,root));if(!response.ok)throw Error(p);return response.json()})]);
const rows=allRows.filter(available),byId=new Map(rows.map(row=>[row.id,row]));
const preferred=new Set(Object.values(coverage.roles||{}).flatMap(role=>Object.values(role.current_assets||{})));
const catalog={};
for(const row of rows){
 if(!preferred.has(catalog[row.source_id]?.id)||preferred.has(row.id))catalog[row.source_id]=row;
}
const config=[...assemblies.assemblies,...kits.kits].filter(item=>
 item.sample?.startsWith('tools/preview-engine/index.html#') &&
 item.parts.every(part=>byId.has(part.asset_id)) &&
 (!item.preview_asset_id||byId.has(item.preview_asset_id)));
const select=document.querySelector('#shot');
for(const item of config) {const o=document.createElement('option');o.value=item.id;o.textContent=item.title;select.append(o);}
const recipes={};
for(const item of config.filter(c=>c.preview_asset_id)){
 const row=byId.get(item.preview_asset_id),file=row.payload.find(p=>p.path.endsWith('/sequence.json'));
 const base=new URL(file.path.replace(/sequence\.json$/,''),root);
 const recipe=await (await fetch(new URL('sequence.json',base))).json();
 const {renderStudy}=await import(new URL('runtime.mjs',base));
 const images={};for(const [id,info] of Object.entries(recipe.images)){const image=new Image();image.src=new URL(info.path,base);await image.decode();images[id]=image;}
 recipes[item.id]={recipe,renderStudy,images};
}
const assets={};const assetVersions={};
for(const row of rows){if(!row.payload.some(p=>p.path.endsWith('.png')))continue;const rec=await(await fetch(new URL(row.portable_record,root))).json();const versionAssets={}; const parts=rec.asset_bundle?.length?rec.asset_bundle:[{asset_id:'whole',path:rec.entry,content_bounds:rec.content_bounds}];
 for(const p of parts){if(!p.path?.endsWith('.png'))continue;const file=row.payload.find(f=>f.path.endsWith('/'+p.path));if(!file)continue;const image=new Image();image.src=new URL(file.path,root);await image.decode();const id=p.asset_id==='whole'?row.source_id:row.source_id+':'+p.asset_id;versionAssets[id]={image,bounds:(p.asset_id==='whole'?(discovery.assets[row.source_id]?.geometry_revision===row.revision?discovery.assets[row.source_id]?.visible_bounds:null):null)||p.content_bounds};}assetVersions[row.id]=versionAssets;}
const stage=new PaperStage(document.querySelector('#stage'),assets);
const r=n=>'reserve_'+n+'_v1';const draw=(id,x,y,w,o={})=>stage.piece(id,{x,y,w,...o});
const move=(id,a,b,w,t,start=0,end=2,options={})=>{const p=arc(a,b,phase(t,start,end),options.lift||35);draw(id,p.x,p.y,w,options);};
function scene(id,t){stage.begin(t); if(recipes[id]){const {recipe,renderStudy,images}=recipes[id];window.__state=renderStudy(stage.ctx,images,recipe,t);return;}  const u=phase(t,.5,2),v=phase(t,3,4.5),p=phase(t,1,3);
 const base=(name,x,y,w)=>draw(r(name),x,y,w);
 if(['door'].includes(id)){
  const hinge=Math.max(.05,1-p*.95);draw(r('door_leaf'),514+126*hinge,360,252,{h:555,hinge,shadow:0});base('door_frame',640,360,380);
 }else if(['calendar','followup'].includes(id)){
  const cx=id==='calendar'?640:390;
  base('calendar_base',cx,415,340);
  // The page stays under the binding; the old page turns around its top edge.
  const top=270,h=290,turn=Math.cos(Math.PI*u);
  draw(r('calendar_leaf'),cx+25,top+h/2,230,{h,shadow:2});
  if(u<.98)draw(r('calendar_leaf'),cx+25,top+h/2*turn,230,{h,hingeY:turn,shadow:2});
  if(id==='followup'){base('notebook_cover',930,410,420);draw(r('notebook_page'),1040,lerp(-180,410,phase(t,2.7,4.5)),170,{h:240});}
 }else if(id==='notebook'){
  const turn=Math.cos(Math.PI*u);
  base('notebook_cover',640,380,680);
  draw(r('notebook_page'),495,380,260,{h:360});draw(r('notebook_page'),785,380,260,{h:360});
  draw(r('notebook_page'),640+130*turn,380,260,{h:360,hinge:turn});
 }else if(id==='specimen'){
  base('tube',560,400,85);move(r('tube_cap'),{x:800,y:130},{x:560,y:175},94,t,.4,2,{angle:0,lift:35});base('tube_rack',930,480,300);stage.contact('cap_contact',2,{x:560,y:214});
 }else if(id==='room'){
  base('wall',640,300,1160);draw(r('floor'),640,590,1160,{h:220,shadow:0});base('shelf',970,365,240);base('chair',390,420,175);base('table',615,478,600);
 }else if(id==='evidence_compare'){
  base('mri',290,380,300);base('tube',760,370,55);base('folder',1060,440,245);move('paper_blank_report',{x:620,y:230},{x:590,y:380},180,t,1,3,{lift:15});
 }else if(id==='meal'||id==='meal_action'){
  base('plate',600,360,560);move(r('rice'),{x:235,y:-150},{x:500,y:365},170,t,.2,1.6);move(r('broccoli'),{x:630,y:-180},{x:615,y:270},105,t,1.8,3);
  const served=arc({x:980,y:-150},{x:695,y:410},phase(t,1,2.4),35),take=id==='meal_action'?phase(t,3,4.5):0;
  const fish={x:lerp(served.x,900,take),y:lerp(served.y,240,take)};
  draw(r('fish'),fish.x,fish.y,180);
  if(id==='meal_action'&&t>=2.8)draw(r('hand_pinch'),fish.x+135,fish.y-15,280,{opacity:phase(t,2.8,3)});
 }else if(id==='anatomy_focus'||id==='structure_focus'){
  const source=t<3?r('heart'):r('heart_cut');draw(source,lerp(430,580,p),360,lerp(300,560,p));if(t>=3){const a=assets[r('heart_cut')];const b=a.bounds||[0,0,a.image.width,a.image.height];const bw=b[2]-b[0],bh=b[3]-b[1];draw(r('heart_cut'),1040,355,330,{crop:[b[0]+bw*.25,b[1]+bh*.35,b[0]+bw*.65,b[1]+bh*.75]});}
 }else if(id==='glucose'||id==='glucose_action'){
  draw('paper_glucose_meter_parts_v1:body',640,270,310);move('paper_glucose_meter_parts_v1:strip',{x:640,y:760},{x:640,y:505},17,t,1,3,{angle:Math.PI,lift:0});draw('paper_glucose_meter_parts_v1:body',640,270,310);if(id==='glucose_action')move(r('notebook_page'),{x:1060,y:800},{x:1040,y:365},280,t,3,4.5);stage.contact('strip_contact',3,{x:650,y:480});
 }else if(id==='pressure'){
  draw('paper_upper_arm_monitor_parts_v1:body',460,370,390);draw('paper_upper_arm_monitor_parts_v1:cuff',850,380,350,{angle:-.08*u});
 }else if(id==='medicine'||id==='medicine_action'){
  draw('paper_medicine_bottle_parts_v1:body',640,420,240);move('paper_medicine_bottle_parts_v1:cap',{x:640,y:180},{x:820,y:150},158,t,.6,2.4,{angle:u*.6});if(id==='medicine_action'){move(r('pillbox'),{x:1000,y:800},{x:1010,y:450},240,t,2,3.3);move(r('notebook_page'),{x:300,y:800},{x:300,y:400},300,t,3.2,4.5);}
 }else if(id==='report_handoff'){
  const handoff=phase(t,.4,2.5),archive=phase(t,3,4.5),release=phase(t,4.5,5.5);
  const paper={x:lerp(730,600,handoff)+440*archive,y:lerp(355,390,handoff)+65*archive-Math.sin(Math.PI*archive)*90};
  draw('paper_open_envelope',1040,490,300);
  draw('mac_left_receive_v1',420+440*archive-180*release,440+(paper.y-390)*archive+180*release,390,{opacity:1-release});
  draw('paper_blank_report',paper.x,paper.y,190);
  // The thumb overlaps the paper until transfer; then the giving hand withdraws.
  const away=phase(t,2.5,3.1);
  draw('mac_right_pinch_v1',940-130*handoff+190*away,300+35*handoff-130*away,370,{opacity:1-away});
  // Redraw only the envelope's front pocket. Its opening remains behind the paper.
  const c=stage.ctx;c.save();c.beginPath();
  c.moveTo(891,450);c.lineTo(1034,509);c.lineTo(1174,432);c.lineTo(1190,620);c.lineTo(890,620);c.closePath();c.clip();
  draw('paper_open_envelope',1040,490,300);c.restore();
  stage.contact('paper_transfer',2.5,{x:600,y:470});

 }
}
let selected=location.hash.slice(1)||'report_handoff';if(!config.some(c=>c.id===selected))selected='report_handoff';select.value=selected;
const slider=document.querySelector('#time'),clock=document.querySelector('#clock'),notes=document.querySelector('#notes');let start=0,playing=false,enableSound=false,audio=null;
function duration(){return recipes[selected]?.recipe.duration||6;}
function render(t){scene(selected,t);slider.value=t;clock.value=t.toFixed(2);window.__layout=stage.layout;window.__events=stage.events;}
async function sound(){audio?.pause();if(!enableSound)return;const kit=config.find(c=>c.id===selected);const soundPart=kit.parts.find(p=>['audio','music_score'].includes(byId.get(p.asset_id)?.kind));if(!soundPart)return;const row=byId.get(soundPart.asset_id);const file=row.payload.find(p=>p.path.endsWith('audition.wav'))||row.payload.find(p=>p.path.endsWith('.wav'));if(!file)return;audio=new Audio(new URL(file.path,root));audio.volume=.18;await audio.play();}
function choose(){selected=select.value;if(!config.some(c=>c.id===selected))throw Error('未知或已撤回的预览');location.hash=selected;for(const key of Object.keys(assets))delete assets[key];for(const part of config.find(c=>c.id===selected).parts)Object.assign(assets,assetVersions[part.asset_id]||{});slider.max=duration();playing=false;audio?.pause();notes.textContent=(config.find(c=>c.id===selected).relationship||config.find(c=>c.id===selected).event_chain)+'；样例边界见组合登记。';render(0);}
select.onchange=choose;slider.oninput=()=>{playing=false;audio?.pause();render(+slider.value);};document.querySelector('#play').onclick=()=>{playing=!playing;start=performance.now()-Number(slider.value)*1000;if(playing)sound();else audio?.pause();};document.querySelector('#sound').onclick=()=>{enableSound=!enableSound;document.querySelector('#sound').textContent='试听声音：'+(enableSound?'开':'关');if(playing)sound();else audio?.pause();};
function loop(now){if(playing){let t=(now-start)/1000;if(t>=duration()){t=duration();playing=false;audio?.pause();}render(t);}requestAnimationFrame(loop);}choose();requestAnimationFrame(loop);
window.__seek=(t)=>{playing=false;audio?.pause();render(Math.max(0,Math.min(duration(),t)));};window.__select=(id)=>{select.value=id;choose();};window.__ready=true;window.__samples=config.map(c=>c.id);window.__duration=duration;
