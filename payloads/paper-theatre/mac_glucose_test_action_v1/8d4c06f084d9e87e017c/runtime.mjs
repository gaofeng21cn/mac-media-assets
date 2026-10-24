// 血糖仪操作：插试纸 → 采血 → 试纸沾血 → 读数 → 按压止血。
// 时间由镜头提供；渲染不累积状态。
export const clamp=x=>Math.max(0,Math.min(1,x));
export const ease=x=>{const u=clamp(x);return u*u*(3-2*u)};
export const phase=(t,a,b)=>ease((t-a)/(b-a));
const lerp=(a,b,u)=>a+(b-a)*u;

function piece(ctx,images,recipe,id,x,y,w,angle=0,anchor=[.5,.5],alpha=1){
  const info=recipe.images[id],img=images[id];
  const b=info.bounds||[0,0,img.width,img.height],bw=b[2]-b[0],bh=b[3]-b[1],s=w/bw;
  ctx.save();ctx.globalAlpha=alpha;ctx.translate(x,y);ctx.rotate(angle);
  ctx.drawImage(img,b[0],b[1],bw,bh,-anchor[0]*bw*s,-anchor[1]*bh*s,w,bh*s);ctx.restore();
}

// 试纸沿固定路径移动：待用 → 插入主机 → 指端 → 回到主机。
function alongPath(positions,path,time){
  let index=0;
  while(index<path.length-1&&time>=path[index+1][0])index++;
  const [t0,key0]=path[index],[t1,key1]=path[Math.min(index+1,path.length-1)];
  const u=t1>t0?phase(time,t0,t1):0;
  const a=positions[key0],b=positions[key1];
  return {x:lerp(a.x,b.x,u),y:lerp(a.y,b.y,u),width:lerp(a.width,b.width,u),angle:lerp(a.angle||0,b.angle||0,u)};
}

export function glucoseState(recipe,t){
  const s=recipe.steps;
  return {insert:phase(t,s.insert.start,s.insert.end),prick:phase(t,s.prick.start,s.prick.end),
    read:phase(t,s.read.start,s.read.end),dress:phase(t,s.dress.start,s.dress.end)};
}

export function renderStudy(ctx,images,recipe,t){
  const st=glucoseState(recipe,t),s=recipe.steps;
  // 手：整段动作里固定不动，采血点固定在同一根手指的指尖。
  piece(ctx,images,recipe,'arm',recipe.arm.x,recipe.arm.y,recipe.arm.width,0,[.5,.5]);

  // 血糖仪与试纸。
  piece(ctx,images,recipe,'meter',recipe.meter.x,recipe.meter.y,recipe.meter.width,0,[.5,.5]);
  const strip=alongPath(recipe.positions,recipe.strip_path,t);
  piece(ctx,images,recipe,'strip',strip.x,strip.y,strip.width,strip.angle,[.5,.5]);

  // 指端血滴：采血后出现，按压止血后消失。
  const blood=st.prick*(1-st.dress);
  if(blood>0.001){
    const p=recipe.positions.finger;
    ctx.save();ctx.globalAlpha=blood;
    ctx.fillStyle='#b03a2e';
    ctx.beginPath();ctx.arc(p.x+recipe.finger_offset.x,p.y+recipe.finger_offset.y,9,0,Math.PI*2);ctx.fill();
    ctx.restore();
  }

  // 敷料：按压止血时贴到指端。
  const dpos=alongPath(recipe.dressing_positions,recipe.dressing_path,t);
  piece(ctx,images,recipe,'dressing',dpos.x,dpos.y,dpos.width,dpos.angle,[.5,.5],st.dress);

  // 读数卡：只在读数阶段出现。
  const readAlpha=st.read*(1-st.dress);
  if(readAlpha>0.001){
    const card=recipe.readout;
    ctx.save();ctx.globalAlpha=readAlpha;
    ctx.translate(card.x,card.y);
    const w=card.width,h=card.height;
    ctx.fillStyle='#f6f1e4';ctx.strokeStyle='#3c4a46';ctx.lineWidth=3;
    ctx.beginPath();ctx.rect(-w/2,-h/2,w,h);ctx.fill();ctx.stroke();
    ctx.fillStyle='#26302e';ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.font='700 44px "Helvetica Neue", Helvetica, Arial, sans-serif';
    ctx.fillText(recipe.readout_values.value,0,-6);
    ctx.font='500 22px "Helvetica Neue", Helvetica, Arial, sans-serif';
    ctx.fillText(recipe.readout_values.unit,0,32);
    ctx.restore();
  }
  return {study:recipe.id,time:t,state:st,
    events:recipe.events.filter(e=>e.time<=t).map(e=>e.name),
    scene:st.dress>0.5?'dressing':st.read>0.5?'reading':st.prick>0.5?'pricked':st.insert>0.5?'strip_in':'standby'};
}
