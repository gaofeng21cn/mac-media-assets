// Two-dimensional section windows follow each registered source structure.
// Original rasters stay unchanged and every layer retains the same origin.
const clamp=x=>Math.max(0,Math.min(1,x));
const smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
const MAIN=[42,86,790,548];
const edgeCaches=new WeakMap();

export function sectionState(r,t){
  const a=r.timing;
  const opening=smooth((t-a.open_start)/(a.open_end-a.open_start));
  const closing=smooth((t-a.close_start)/(a.close_end-a.close_start));
  const openness=opening*(1-closing);
  const phase=t<a.open_start?'closed':t<a.open_end?'opening':t<a.close_start?'open':t<a.close_end?'closing':'restored';
  return {study:r.id,time:t,phase,openness,shared_origin:true,
    section_kind:r.section.kind,events:r.events.filter(x=>x.time<=t).map(x=>x.name)};
}

function camera(r,box=MAIN){
  const b=r.composite_bounds,[x,y,w,h]=box;
  const s=Math.min((w-46)/(b[2]-b[0]),(h-34)/(b[3]-b[1]));
  return {scale:s,x:x+w/2-(b[0]+b[2])*s/2,y:y+h/2-(b[1]+b[3])*s/2};
}

function windowPath(section,openness){
  const combined=new Path2D();
  if(openness<=0)return combined;
  if(section.kind==='cross_section_sector'){
    const e=section.sector,end=-Math.PI/2+Math.PI*2*openness;
    combined.moveTo(e.cx,e.cy);combined.lineTo(e.cx,e.cy-e.ry);
    combined.ellipse(e.cx,e.cy,e.rx,e.ry,0,-Math.PI/2,end);combined.closePath();
  }else for(const window of section.windows){
    const [cx,cy]=window.pivot;
    const matrix=new DOMMatrix().translate(cx,cy).rotate(window.angle||0).scale(openness,1).translate(-cx,-cy);
    combined.addPath(new Path2D(window.path),matrix);
  }
  return combined;
}

function draw(ctx,images,ids,alpha=1){
  ctx.save();ctx.globalAlpha=alpha;for(const id of ids)ctx.drawImage(images[id],0,0,1024,1024);ctx.restore();
}

function edge(ctx,images,section,cut,scale){
  let cache=edgeCaches.get(images);
  if(!cache){cache={marks:new OffscreenCanvas(1024,1024),masks:new Map()};edgeCaches.set(images,cache)}
  const mark=cache.marks.getContext('2d');mark.reset();
  if(section.kind==='local_relation_reveal')mark.setLineDash([8/scale,6/scale]);
  mark.strokeStyle='#f4e7cc';mark.lineWidth=8/scale;mark.stroke(cut);
  mark.strokeStyle='#86684a';mark.lineWidth=2/scale;mark.stroke(cut);
  if(section.cover.length){
    const key=section.cover.join('|');
    if(!cache.masks.has(key)){
      const mask=new OffscreenCanvas(1024,1024);draw(mask.getContext('2d'),images,section.cover);cache.masks.set(key,mask);
    }
    // Clip the decorative cut edge by the ACTUAL cover alpha. A source-bound
    // window can narrow outside a sloped outline; it must never leave a
    // floating incision frame in transparent space.
    mark.globalCompositeOperation='destination-in';mark.drawImage(cache.masks.get(key),0,0);
  }
  ctx.drawImage(cache.marks,0,0);
}

function body(ctx,images,r,state,view){
  ctx.save();ctx.translate(view.x,view.y);ctx.scale(view.scale,view.scale);
  const s=r.section,u=state.openness,cut=windowPath(s,u);
  draw(ctx,images,s.context_before||[]);
  if(s.cover.length){
    if(u>0){
      // The cut face uses the same source pixels at reduced paper opacity;
      // it adds no invented tissue or external image to the section.
      ctx.save();ctx.clip(cut);draw(ctx,images,s.cover,s.underlay_alpha);ctx.restore();
      const outside=new Path2D();outside.rect(0,0,1024,1024);outside.addPath(cut);
      ctx.save();ctx.clip(outside,'evenodd');draw(ctx,images,s.cover);ctx.restore();
    }else draw(ctx,images,s.cover);
  }
  if(u>0){
    ctx.save();ctx.clip(cut);draw(ctx,images,s.interior);ctx.restore();
    if(u<.999||s.kind!=='cross_section_sector'){
      edge(ctx,images,s,cut,view.scale);
    }
  }
  draw(ctx,images,s.context_after||[]);
  for(const item of s.context_regions||[]){
    ctx.save();
    if(item.outside_path){
      const outside=new Path2D();outside.rect(0,0,1024,1024);outside.addPath(new Path2D(item.outside_path));ctx.clip(outside,'evenodd');
    }else ctx.clip(new Path2D(item.path));
    draw(ctx,images,[item.id]);ctx.restore();
  }
  ctx.restore();
}

function label(ctx,value,x,y,size=30,color='#2b4138'){
  ctx.font=`500 ${size}px system-ui,sans-serif`;ctx.fillStyle=color;ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(value,x,y);
}

export function renderStudy(ctx,images,r,t){
  const state=sectionState(r,t),view=camera(r);
  ctx.fillStyle='#f4eedf';ctx.fillRect(22,18,1236,54);
  label(ctx,r.label,42,45,36);label(ctx,r.section.display_kind,868,45,28);
  ctx.save();ctx.beginPath();ctx.rect(...MAIN);ctx.clip();body(ctx,images,r,state,view);ctx.restore();
  ctx.fillStyle='#f4eedf';ctx.fillRect(852,94,376,534);
  const phaseLabel={closed:'起始状态',opening:'边界连续打开',open:state.section_kind==='two_dimensional_section'?'内部关系可见':'对应关系可见',closing:'边界连续关闭',restored:'恢复起始状态'}[state.phase];
  label(ctx,phaseLabel,878,128,30);
  ctx.fillStyle='#d8cfba';ctx.fillRect(878,163,316,12);ctx.fillStyle='#547364';ctx.fillRect(878,163,316*state.openness,12);
  label(ctx,'打开时显示',878,216,27);
  r.section.revealed_labels.forEach((text,index)=>label(ctx,text,878,260+index*42,28));
  label(ctx,'同位二维示意',878,578,27);
  ctx.fillStyle='#f4eedf';ctx.fillRect(22,650,1236,58);label(ctx,r.presentation_note,42,680,27);
  return {...state,camera:view,interior_allowed:state.openness>0};
}
