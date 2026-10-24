export const clamp=x=>Math.max(0,Math.min(1,x));
export function abpmState(r,t){
 const elapsed=24*clamp(t/r.duration),hour=(8+elapsed)%24;
 const reading=Math.floor(elapsed/r.interval_hours);
 return {elapsed,hour,night:hour<7||hour>=22,readings:reading,complete:elapsed>=24};
}
export function renderStudy(ctx,images,r,t){
 const s=abpmState(r,t),p=r.images.patient,b=p.bounds,scale=3/r.source_pixels_per_cm;
 ctx.drawImage(images.patient,b[0],b[1],b[2]-b[0],b[3]-b[1],315-(b[2]-b[0])*scale/2,640-(b[3]-b[1])*scale,(b[2]-b[0])*scale,(b[3]-b[1])*scale);
 ctx.fillStyle=s.night?'#334d59':'#eee0b2';ctx.beginPath();ctx.roundRect(670,95,490,460,25);ctx.fill();
 const ink=s.night?'#f5f0de':'#344a46';ctx.strokeStyle=ink;ctx.fillStyle=ink;
 ctx.lineWidth=5;ctx.beginPath();ctx.arc(910,215,76,0,Math.PI*2);ctx.stroke();
 for(let i=0;i<12;i++){const a=i*Math.PI/6;ctx.beginPath();ctx.moveTo(910+Math.sin(a)*66,215-Math.cos(a)*66);ctx.lineTo(910+Math.sin(a)*72,215-Math.cos(a)*72);ctx.stroke()}
 const a=s.hour/12*2*Math.PI;ctx.beginPath();ctx.moveTo(910,215);ctx.lineTo(910+Math.sin(a)*48,215-Math.cos(a)*48);ctx.stroke();
 ctx.textAlign='center';ctx.font='600 27px sans-serif';ctx.fillText(s.night?'夜间记录':'日间记录',910,335);
 ctx.font='500 21px sans-serif';ctx.fillText('周期性测量 · 保留日夜记录',910,375);
 // These marks are scheduled samples, never a fabricated blood-pressure curve.
 const count=Math.min(24,Math.floor(s.elapsed));
 for(let i=0;i<count;i++){ctx.fillStyle=ink;ctx.beginPath();ctx.arc(715+(i%12)*35,425+Math.floor(i/12)*40,6,0,Math.PI*2);ctx.fill()}
 ctx.fillStyle='#f4eedf';ctx.fillRect(120,635,1040,65);
 ctx.fillStyle='#334a45';ctx.font='600 24px sans-serif';ctx.fillText(s.complete?'记录满 24 小时后按约定交回设备':'充气测量时放松，手臂保持安静',640,660);
 return {study:r.id,time:t,...s,events:r.events.filter(e=>e.time<=t).map(e=>e.name)};
}

