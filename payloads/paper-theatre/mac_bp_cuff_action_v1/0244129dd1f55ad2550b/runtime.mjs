// 上臂式血压计：展开袖带 → 套上 → 缠紧 → 主机就位 → 读数 → 拆下。
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

export function cuffState(recipe,t){
  const s=recipe.steps;
  return {
    move:phase(t,s.cuff_move.start,s.cuff_move.end),
    wrap:phase(t,s.wrap.start,s.wrap.end),
    monitor:phase(t,s.monitor.start,s.monitor.end),
    read:phase(t,s.read.start,s.read.end),
    remove:phase(t,s.remove.start,s.remove.end),
  };
}

export function renderStudy(ctx,images,recipe,t){
  const st=cuffState(recipe,t),s=recipe.steps;
  // 手臂：整段动作里固定不动，接触点固定在同一条上臂上。
  piece(ctx,images,recipe,'arm',recipe.arm.x,recipe.arm.y,recipe.arm.width,0,[.5,.5]);

  const onArm=st.move*(1-st.remove);
  const openX=lerp(recipe.cuff_open.from.x,recipe.cuff_open.to.x,onArm);
  const openY=lerp(recipe.cuff_open.from.y,recipe.cuff_open.to.y,onArm);
  const openW=lerp(recipe.cuff_open.from.width,recipe.cuff_open.to.width,onArm);
  const openAlpha=1-st.wrap*(1-st.remove);
  piece(ctx,images,recipe,'cuff_open',openX,openY,openW,0,[.5,.5],openAlpha);

  // 缠好的袖带：只在套上之后出现，拆下时退回展开状态。
  const wrappedAlpha=st.wrap*(1-st.remove);
  if(wrappedAlpha>0.001){
    const tight=st.wrap*0.16;
    piece(ctx,images,recipe,'cuff_wrapped',recipe.cuff_wrapped.x,recipe.cuff_wrapped.y,
      recipe.cuff_wrapped.width*(1-tight*0.25),-0.06*tight,[.5,.5],wrappedAlpha);
  }

  // 主机：读数前才移到袖带下方。
  // 拆下时主机随袖带一起退回原位。
  const mon=st.monitor*(1-st.remove);
  const monX=lerp(recipe.monitor.from.x,recipe.monitor.to.x,mon);
  const monY=lerp(recipe.monitor.from.y,recipe.monitor.to.y,mon);
  piece(ctx,images,recipe,'monitor',monX,monY,recipe.monitor.width,0,[.5,.5]);

  // 读数卡：数值只在读数阶段出现，拆下时消失。
  const readAlpha=st.read*(1-st.remove);
  if(readAlpha>0.001){
    const card=recipe.readout;
    ctx.save();ctx.globalAlpha=readAlpha;
    ctx.translate(card.x,card.y);
    const w=card.width,h=card.height;
    ctx.fillStyle='#f6f1e4';ctx.strokeStyle='#3c4a46';ctx.lineWidth=3;
    ctx.beginPath();ctx.rect(-w/2,-h/2,w,h);ctx.fill();ctx.stroke();
    ctx.fillStyle='#26302e';ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.font='700 46px "Helvetica Neue", Helvetica, Arial, sans-serif';
    ctx.fillText(recipe.readout_values.systolic_diastolic,0,-6);
    ctx.font='500 22px "Helvetica Neue", Helvetica, Arial, sans-serif';
    ctx.fillText(recipe.readout_values.unit,0,32);
    ctx.restore();
  }
  return {study:recipe.id,time:t,state:st,
    events:recipe.events.filter(e=>e.time<=t).map(e=>e.name),
    scene:st.read>0.5?'reading':st.monitor>0.5?'monitor_placed':st.wrap>0.5?'wrapped':'cuff_moving'};
}
