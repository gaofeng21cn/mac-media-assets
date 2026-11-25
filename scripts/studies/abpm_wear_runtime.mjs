// Complete contact units: the patient, chair, arm support and fitting hands
// are drawn together. Never scale the cuff or chair independently of the body.
export const clamp=x=>Math.max(0,Math.min(1,x));
export function abpmWearState(r,time){
 const t=Math.max(0,Math.min(r.duration,time));
 const stage=r.stages.find(s=>t>=s.start&&t<s.end)||r.stages.at(-1);
 const frame=r.frames[stage.frame];
 const elapsed=stage.key==='record'?24*clamp((t-stage.start)/(stage.end-stage.start)):stage.key==='return'?24:0;
 const hour=(8+elapsed)%24;
 return {time:t,stage:stage.key,frame:stage.frame,rect:frame.rect,elapsed,hour,
  night:stage.key==='record'&&(hour>=22||hour<7),
  cuff_on_bare_upper_arm:stage.cuff_worn,
  recorder_secured:stage.recorder_secured,
  contact_unit:'patient_chair_table_cuff_tube_recorder',
  events:r.events.filter(e=>e.time<=t).map(e=>e.name)};
}
export function renderStudy(ctx,images,r,t){
 const s=abpmWearState(r,t),stage=r.stages.find(x=>x.key===s.stage),f=r.frames[s.frame];
 const [x,y,w,h]=f.rect,scale=r.display.scale;
 const dx=r.display.ground[0]-f.ground[0]*scale,dy=r.display.ground[1]-f.ground[1]*scale;
 const panelRight=f.hand_entry_right==null?570:dx+f.hand_entry_right*scale;
 // The fitter's forearms enter a visible illustration frame; their cropped
 // ends must not float as detached limbs in open stage space.
 ctx.fillStyle='#eee4d1';ctx.strokeStyle='#b9ad94';ctx.lineWidth=2;
 ctx.fillRect(55,76,panelRight-55,555);ctx.strokeRect(55,76,panelRight-55,555);
 ctx.save();ctx.beginPath();ctx.rect(55,77,panelRight-55,553);ctx.clip();
 ctx.drawImage(images.sheet,x,y,w,h,dx,dy,w*scale,h*scale);
 ctx.restore();
 // Side panel is a separate explanation; it never covers the body's contacts.
 ctx.fillStyle=s.night?'#334d59':'#e9ddb9';ctx.beginPath();ctx.roundRect(700,85,485,485,20);ctx.fill();
 const ink=s.night?'#f4eedf':'#30483f';ctx.fillStyle=ink;ctx.textAlign='center';
 ctx.font='600 30px sans-serif';ctx.fillText(stage.title,942,145);
 ctx.font='500 23px sans-serif';for(let i=0;i<stage.lines.length;i++)ctx.fillText(stage.lines[i],942,200+i*39);
 if(s.stage==='record'){
  const cx=940,cy=365,rr=70;ctx.strokeStyle=ink;ctx.lineWidth=4;ctx.beginPath();ctx.arc(cx,cy,rr,0,Math.PI*2);ctx.stroke();
  for(let i=0;i<12;i++){const a=i*Math.PI/6;ctx.beginPath();ctx.moveTo(cx+Math.sin(a)*60,cy-Math.cos(a)*60);ctx.lineTo(cx+Math.sin(a)*66,cy-Math.cos(a)*66);ctx.stroke()}
  const a=s.hour/12*Math.PI*2;ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(cx+Math.sin(a)*45,cy-Math.cos(a)*45);ctx.stroke();
  ctx.font='600 23px sans-serif';ctx.fillText(s.night?'夜间记录':'日间记录',942,477);
  // A progress bar represents elapsed time, not fabricated BP readings or frequency.
  ctx.fillStyle=ink;ctx.fillRect(765,515,355*clamp(s.elapsed/24),6);
 }
 ctx.fillStyle='#f4eedf';ctx.fillRect(70,637,1140,65);ctx.fillStyle='#30483f';ctx.font='600 24px sans-serif';ctx.fillText(stage.caption,640,676);
 return {...s,ground:r.display.ground,shared_scale:scale};
}
