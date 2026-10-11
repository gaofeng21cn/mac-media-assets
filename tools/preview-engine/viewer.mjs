import {PaperStage,phase,arc,lerp} from './paper-runtime.mjs';
const root=new URL('../../',location.href);
const [rows,assemblies,kits,discovery] = await Promise.all(['catalog/assets.jsonl','collections/assemblies.json','collections/event-kits.json','collections/discovery.json'].map(async p=>{const text=await(await fetch(new URL(p,root))).text();return p.endsWith('jsonl')?text.trim().split('\n').map(JSON.parse):JSON.parse(text);}));
const catalog=Object.fromEntries(rows.map(r=>[r.source_id,r]));
const config=[...assemblies.assemblies,...kits.kits];const select=document.querySelector('#shot');
for(const item of config) {const o=document.createElement('option');o.value=item.id;o.textContent=item.title;select.append(o);}
const assets={};const recordCache={};
for(const row of rows){if(!row.payload.some(p=>p.path.endsWith('.png')))continue;const rec=await(await fetch(new URL(row.portable_record,root))).json();recordCache[row.source_id]=rec; const parts=rec.asset_bundle?.length?rec.asset_bundle:[{asset_id:'whole',path:rec.entry,content_bounds:rec.content_bounds}];
 for(const p of parts){if(!p.path?.endsWith('.png'))continue;const file=row.payload.find(f=>f.path.endsWith('/'+p.path));if(!file)continue;const image=new Image();image.src=new URL(file.path,root);await image.decode();const id=p.asset_id==='whole'?row.source_id:row.source_id+':'+p.asset_id;assets[id]={image,bounds:(p.asset_id==='whole'?(discovery.assets[row.source_id]?.geometry_revision===row.revision?discovery.assets[row.source_id]?.visible_bounds:null):null)||p.content_bounds};}}
const stage=new PaperStage(document.querySelector('#stage'),assets);
const r=n=>'reserve_'+n+'_v1';const draw=(id,x,y,w,o={})=>stage.piece(id,{x,y,w,...o});
const move=(id,a,b,w,t,start=0,end=2,options={})=>{const p=arc(a,b,phase(t,start,end),options.lift||35);draw(id,p.x,p.y,w,options);};
function scene(id,t){stage.begin(t); const u=phase(t,.5,2),v=phase(t,3,4.5),p=phase(t,1,3);
 const base=(name,x,y,w)=>draw(r(name),x,y,w);
 if(['door'].includes(id)){
  base('wall',640,360,1100);base('door_frame',640,360,380);draw(r('door_leaf'),545+95*Math.max(.05,1-p*.9),360,190,{hinge:Math.max(.05,1-p*.9),shadow:5});
 }else if(['calendar','followup'].includes(id)){
  base('calendar_base',450,445,420);base('calendar_leaf',450,345,340);draw(r('calendar_leaf'),450+250*u,345-90*Math.sin(Math.PI*u),340,{hinge:Math.cos(Math.PI*u),angle:u*.07});if(id==='followup'){base('notebook_cover',950,420,370);move(r('notebook_page'),{x:960,y:-200},{x:955,y:370},310,t,2.7,4.5);}
 }else if(id==='notebook'){
  base('notebook_cover',640,370,560);base('notebook_page',640,345,480);draw(r('notebook_page'),640+200*u,345,480,{hinge:Math.cos(Math.PI*u)});
 }else if(id==='specimen'){
  base('tube',640,335,115);move(r('tube_cap'),{x:850,y:190},{x:640,y:178},90,t,.4,2);base('tube_rack',640,505,390);stage.contact('cap_contact',2,{x:640,y:178});
 }else if(id==='bed'||id==='daily_activity'){
  if(id==='daily_activity'&&t<3){base('floor',640,580,1150);move(r('person_walk'),{x:320,y:355},{x:800,y:355},230,t,0,3,{lift:0});base('shoe',1040,545,170);}
  else{base('bed',640,435,1000);move(r('pillow'),{x:960,y:-200},{x:930,y:340},270,t,id==='bed'?0:3,id==='bed'?2:4);move(r('blanket'),{x:600,y:-250},{x:510,y:385},350,t,id==='bed'?2:4,id==='bed'?4:5.8);}
 }else if(id==='room'||id==='evidence_compare'){
  base('wall',640,320,1200);base('floor',640,600,1250);base('shelf',1060,310,250);base('chair',360,435,230);base('table',650,475,850);
  if(id==='evidence_compare'){base('mri',430,360,220);base('tube',830,350,45);move('paper_blank_report',{x:490,y:200},{x:650,y:405},140,t,1,3);move(r('folder'),{x:930,y:750},{x:890,y:430},240,t,3,4.5);}
 }else if(id==='meal'||id==='meal_action'){
  base('table',640,510,1100);base('plate',640,395,620);move(r('rice'),{x:250,y:-150},{x:530,y:360},190,t,.2,1.6);move(r('fish'),{x:1040,y:-150},{x:740,y:390},180,t,1,2.4);move(r('broccoli'),{x:640,y:-180},{x:640,y:295},120,t,1.8,3);base('cup',1020,385,130);
  if(id==='meal_action'){draw(r('hand_pinch'),925-230*v,300,300);draw(r('fish'),740+v*130,390-v*160,180);}
 }else if(id==='pose'){
  base('chair',750,470,320);const seated=t>3.05;const y=lerp(320,385,phase(t,1.5,3.05));draw(r(seated?'person_seated':'person_stand'),640,y,seated?300:230);draw(r('table'),490,490,700,{angle:.01});
 }else if(id==='anatomy_focus'||id==='structure_focus'){
  const source=t<3?r('heart'):r('heart_cut');draw(source,lerp(430,580,p),360,lerp(300,560,p));if(t>=3){const a=assets[r('heart_cut')];const b=a.bounds||[0,0,a.image.width,a.image.height];const bw=b[2]-b[0],bh=b[3]-b[1];draw(r('heart_cut'),1040,355,330,{crop:[b[0]+bw*.25,b[1]+bh*.35,b[0]+bw*.65,b[1]+bh*.75]});}
 }else if(id==='glucose'||id==='glucose_action'){
  draw('paper_glucose_meter_parts_v1:body',640,270,310);move('paper_glucose_meter_parts_v1:strip',{x:640,y:760},{x:640,y:555},17,t,1,3,{angle:Math.PI,lift:0});draw('paper_glucose_meter_parts_v1:body',640,270,310);if(id==='glucose_action')move(r('notebook_page'),{x:1060,y:800},{x:1040,y:365},280,t,3,4.5);stage.contact('strip_contact',3,{x:650,y:480});
 }else if(id==='pressure'){
  draw('paper_upper_arm_monitor_parts_v1:body',460,370,390);draw('paper_upper_arm_monitor_parts_v1:cuff',850,380,350,{angle:-.08*u});
 }else if(id==='medicine'||id==='medicine_action'){
  draw('paper_medicine_bottle_parts_v1:body',640,420,240);move('paper_medicine_bottle_parts_v1:cap',{x:640,y:180},{x:820,y:150},158,t,.6,2.4,{angle:u*.6});if(id==='medicine_action'){move(r('pillbox'),{x:1000,y:800},{x:1010,y:450},240,t,2,3.3);move(r('notebook_page'),{x:300,y:800},{x:300,y:400},300,t,3.2,4.5);}
 }else if(id==='cuff_contact'){
  draw('mac_bare_arm_v1',700,385,750);move('mac_open_cuff_v1',{x:200,y:140},{x:475,y:385},155,t,.5,2.5,{angle:.55,lift:20});
 }else if(id==='report_handoff'){
  const q=phase(t,.4,2.5),s=phase(t,3,4.5);draw('mac_left_receive_v1',415+s*460,440-s*75*Math.sin(Math.PI*s),390);draw('mac_right_pinch_v1',940+q*50,300-q*90,370);draw('paper_blank_report',710-q*130+s*460,395+q*35-Math.sin(Math.PI*s)*75+s*30,190,{angle:lerp(-.07,.05,q)});draw('paper_open_envelope',1040,490,300);stage.contact('paper_transfer',2.5,{x:580,y:430});

 }
}
let selected=location.hash.slice(1)||'report_handoff';if(!config.some(c=>c.id===selected))selected='report_handoff';select.value=selected;
const slider=document.querySelector('#time'),clock=document.querySelector('#clock'),notes=document.querySelector('#notes');let start=0,playing=false,enableSound=false,audio=null;
function render(t){scene(selected,t);slider.value=t;clock.value=t.toFixed(2);window.__layout=stage.layout;window.__events=stage.events;}
async function sound(){audio?.pause();if(!enableSound)return;const kit=config.find(c=>c.id===selected);const soundPart=kit.parts.find(p=>['audio','music_score'].includes(catalog[p.source_id]?.kind));if(!soundPart)return;const row=catalog[soundPart.source_id];const file=row.payload.find(p=>p.path.endsWith('audition.wav'))||row.payload.find(p=>p.path.endsWith('.wav'));if(!file)return;audio=new Audio(new URL(file.path,root));audio.volume=.18;await audio.play();}
function choose(){selected=select.value;location.hash=selected;playing=false;audio?.pause();notes.textContent=(config.find(c=>c.id===selected).relationship||config.find(c=>c.id===selected).event_chain)+'；样例边界见组合登记。';render(0);}
select.onchange=choose;slider.oninput=()=>{playing=false;audio?.pause();render(+slider.value);};document.querySelector('#play').onclick=()=>{playing=!playing;start=performance.now()-Number(slider.value)*1000;if(playing)sound();else audio?.pause();};document.querySelector('#sound').onclick=()=>{enableSound=!enableSound;document.querySelector('#sound').textContent='试听声音：'+(enableSound?'开':'关');if(playing)sound();else audio?.pause();};
function loop(now){if(playing){let t=(now-start)/1000;if(t>=6){t=6;playing=false;audio?.pause();}render(t);}requestAnimationFrame(loop);}choose();requestAnimationFrame(loop);
window.__seek=(t)=>{playing=false;audio?.pause();render(Math.max(0,Math.min(6,t)));};window.__select=(id)=>{select.value=id;choose();};window.__ready=true;window.__samples=config.map(c=>c.id);
