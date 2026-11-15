// Time is supplied by the consuming shot. Rendering never accumulates state.
export const clamp=x=>Math.max(0,Math.min(1,x));
export const ease=x=>{const u=clamp(x);return u*u*(3-2*u)};
export const phase=(t,a,b)=>ease((t-a)/(b-a));
const lerp=(a,b,u)=>a+(b-a)*u;
export function walkProgress(recipe,t){
  const {start,end,period,frames}=recipe.loop;
  const step=period/frames.length;
  // The body and pose share a flipbook clock. A held drawing never glides.
  return clamp(Math.floor((Math.max(start,t)-start+1e-9)/step)*step/(end-start));
}
export function frameAt(recipe,t){
  const time=Math.max(0,Math.min(recipe.duration,t));
  if(recipe.loop){
    const cycle=((time-recipe.loop.start)%recipe.loop.period+recipe.loop.period)%recipe.loop.period;
    if(time>=recipe.loop.start&&time<recipe.loop.end)
      return recipe.loop.frames[Math.floor(cycle/recipe.loop.period*recipe.loop.frames.length)];
    return time<recipe.loop.start?recipe.ready_frame:recipe.finish_frame;
  }
  let result=recipe.keys[0].frame;
  for(const key of recipe.keys){if(time<key.time)break;result=key.frame}
  return result;
}
function sprite(ctx,image,frame,x,y,scale,flip=false){
  const [sx,sy,sw,sh]=frame.rect, [ax,ay]=frame.origin;
  ctx.save();ctx.translate(x,y);ctx.scale(flip?-scale:scale,scale);
  ctx.drawImage(image,sx,sy,sw,sh,-ax,-ay,sw,sh);ctx.restore();
}
function piece(ctx,images,recipe,id,x,y,w,angle=0,anchor=[.5,.5],crop){
  const info=recipe.images[id],img=images[id];
  const b=crop||info.bounds||[0,0,img.width,img.height],bw=b[2]-b[0],bh=b[3]-b[1],s=w/bw;
  ctx.save();ctx.translate(x,y);ctx.rotate(angle);
  ctx.drawImage(img,b[0],b[1],bw,bh,-anchor[0]*bw*s,-anchor[1]*bh*s,w,bh*s);ctx.restore();
}
export function cookingState(recipe,t){
  const cuts=recipe.events.filter(e=>e.kind==='cut');
  const made=cuts.filter(e=>t>=e.time).length;
  const current=cuts.find(e=>t>=e.time-.34&&t<e.time+.28);
  const transfer=phase(t,recipe.transfer.start,recipe.transfer.end);
  const stirring=t>=recipe.stir.start&&t<recipe.stir.end;
  const serving=phase(t,recipe.serve.start,recipe.serve.end);
  return {made,total:cuts.length,knife:current?1-Math.abs(t-current.time)/.34:0,
    currentCut:current?.index??made,transfer,stirring,serving,
    result:serving>=1?'served':transfer>=1?'in_pan':'on_board'};
}
export function cookingLayout(r,t){
  const s=cookingState(r,t);
  const a=(t-r.stir.start)/(r.stir.end-r.stir.start)*Math.PI*4;
  const center={x:823+(s.stirring?Math.sin(a)*35:0),y:447+(s.stirring?(1-Math.cos(a))*12:0)};
  const paddle={x:lerp(490,center.x,s.transfer),y:lerp(433,center.y,s.transfer)-Math.sin(Math.PI*s.transfer)*80};
  paddle.x=lerp(paddle.x,1095,s.serving);
  paddle.y=lerp(paddle.y,268,s.serving)-Math.sin(Math.PI*s.serving)*70;
  const slices=Array.from({length:s.made},(_,i)=>{
    const offset=(i-1)*24;
    let x=lerp(460+i*25,center.x+offset,s.transfer);
    let y=lerp(432+i*8,center.y+(i%2)*13,s.transfer)-Math.sin(Math.PI*s.transfer)*80;
    x=lerp(x,1095+offset,s.serving);
    y=lerp(y,268+(i%2)*13,s.serving)-Math.sin(Math.PI*s.serving)*70;
    return {id:`slice_${i+1}`,x,y};
  });
  return {paddle,slices};
}
function renderCooking(ctx,images,r,t){
  const s=cookingState(r,t);
  const layout=cookingLayout(r,t);
  // Each surface and its contact objects share world coordinates.
  piece(ctx,images,r,'board',340,450,510);
  piece(ctx,images,r,'cooker',875,490,435);
  piece(ctx,images,r,'pan',900,425,520);
  piece(ctx,images,r,'plate',1110,270,235);
  const cuts=r.events.filter(e=>e.kind==='cut');
  const vegetable=r.images.food.bounds,whole=[...vegetable];
  const wholeW=vegetable[2]-vegetable[0];whole[2]-=s.made*wholeW*.085;
  // Crop the removed material at the cut face; preserve original pixel scale.
  piece(ctx,images,r,'food',188,400,270*(1-s.made*.085),0,[0,.5],whole);
  if(t>=r.transfer.start-.25&&t<r.serve.end){
    // Complete hand+spatula contact unit; the food is drawn on its wooden face.
    piece(ctx,images,r,'spatula_hand',layout.paddle.x,layout.paddle.y,325,-.05,[.18,.77]);
  }
  for(const [i,slice] of layout.slices.entries())
    piece(ctx,images,r,'food',slice.x,slice.y,60,Math.sin(i)*.15,[.5,.5],r.images.slice.bounds);
  const cut=cuts.find(e=>t>=e.time-.34&&t<e.time+.28);
  if(t<r.transfer.start-.4){
    const u=cut?clamp((t-(cut.time-.34))/.34):0;
    const lift=cut?(t<=cut.time?1-ease(u):phase(t,cut.time,cut.time+.28)):1;
    const edge={x:445-(s.currentCut)*23,y:434-lift*82};
    const angle=.58;
    // Knife and gripping hand are transformed as one contact unit.
    ctx.save();ctx.translate(edge.x,edge.y);ctx.rotate(angle);
    const info=r.images.knife,b=info.bounds,sc=310/(b[2]-b[0]);
    ctx.drawImage(images.knife,b[0],b[1],b[2]-b[0],b[3]-b[1],
      (b[0]-.38*images.knife.width)*sc,(b[1]-.63*images.knife.height)*sc,310,(b[3]-b[1])*sc);
    const grip={x:(.8-.38)*images.knife.width*sc,y:(.2-.63)*images.knife.height*sc};
    piece(ctx,images,r,'hand',grip.x,grip.y,190,-angle,[.25,.75]);ctx.restore();
  }
  return {study:r.id,time:t,...s,events:r.events.filter(e=>e.time<=t).map(e=>e.name)};
}
export function renderStudy(ctx,images,recipe,t){
  if(recipe.type==='cooking')return renderCooking(ctx,images,recipe,t);
  const index=frameAt(recipe,t),frame=recipe.frames[index];
  const scale=recipe.display_height/frame.reference_height;
  let x=recipe.x,y=recipe.ground;
  if(recipe.type==='walk')x=lerp(recipe.x,recipe.end_x,walkProgress(recipe,t));
  if(recipe.type==='sit'){
    // Fixed chair, unchanged scale; pose height drops naturally as hips and knees bend.
    piece(ctx,images,recipe,'chair',recipe.chair.x,recipe.chair.y,recipe.chair.width,0,[.5,.5]);
  }
  sprite(ctx,images[frame.image],frame,x,y,scale,frame.flip);
  return {study:recipe.id,time:t,frame:index,phase:recipe.phase_names[index],
    world_origin:[x,y],scale,events:recipe.events.filter(e=>e.time<=t).map(e=>e.name)};
}
