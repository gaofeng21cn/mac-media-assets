// Registered two-dimensional layers. Every layer uses the SAME source origin,
// camera and scale; its alpha bounds never become an independent drawing box.
const clamp=x=>Math.max(0,Math.min(1,x));
const ease=x=>{x=clamp(x);return x*x*(3-2*x)};
const mix=(a,b,u)=>a+(b-a)*u;
const MAIN=[46,72,770,574],INSET=[910,78,260,210];

function fit(bounds,box,padding=24){
  const [x0,y0,x1,y1]=bounds,[x,y,w,h]=box;
  const scale=Math.min((w-padding*2)/(x1-x0),(h-padding*2)/(y1-y0));
  return {scale,x:x+w/2-(x0+x1)*scale/2,y:y+h/2-(y0+y1)*scale/2};
}
const transform=(a,b,u)=>({scale:mix(a.scale,b.scale,u),x:mix(a.x,b.x,u),y:mix(a.y,b.y,u)});

export function structureState(recipe,t){
  const count=recipe.layers.length,base=fit(recipe.composite_bounds,MAIN,34);
  const revealStart=recipe.timing.reveal_start,revealStep=recipe.timing.reveal_step;
  const focusStart=recipe.timing.focus_start,focusStep=recipe.timing.focus_step;
  let mode='overview',index=-1,camera=base,opacities=recipe.layers.map(()=>1);
  if(t>=revealStart&&t<focusStart){
    mode='reveal';index=Math.min(count-1,Math.floor((t-revealStart)/revealStep));
    opacities=recipe.layers.map((_,i)=>ease((t-revealStart-i*revealStep)/.28));
  }else if(t>=focusStart&&t<recipe.timing.return_start){
    mode='focus';index=Math.min(count-1,Math.floor((t-focusStart)/focusStep));
    const start=focusStart+index*focusStep,u=ease((t-start)/.24);
    const bounds=recipe.layers[index].focus_bounds;
    const local=fit(bounds,MAIN,70);
    // Keep nearby layers to explain the relationship, while the whole bundle
    // shares one camera. A locator at right makes the close-up's position clear.
    const previous=index===0?base:fit(recipe.layers[index-1].focus_bounds,MAIN,70);
    camera=transform(previous,local,u);
    opacities=recipe.layers.map((_,i)=>mix(index===0||i===index-1?1:.17,i===index?1:.17,u));
  }else if(t>=recipe.timing.return_start){
    mode='complete';
    const u=ease((t-recipe.timing.return_start)/.35);
    camera=transform(fit(recipe.layers.at(-1).focus_bounds,MAIN,70),base,u);
    opacities=recipe.layers.map((_,i)=>mix(i===count-1?1:.17,1,u));
  }
  return {study:recipe.id,time:t,mode,index,camera,opacities,
    visible_layers:recipe.layers.filter((_,i)=>opacities[i]>.001).map(x=>x.id),
    shared_transform:true,events:recipe.events.filter(x=>x.time<=t).map(x=>x.name)};
}

function layers(ctx,images,recipe,camera,opacities,selected=-1){
  ctx.save();ctx.translate(camera.x,camera.y);ctx.scale(camera.scale,camera.scale);
  recipe.layers.forEach((part,i)=>{
    ctx.globalAlpha=opacities[i];
    ctx.shadowColor=i===selected?'#fff4db':'transparent';
    ctx.shadowBlur=i===selected?6/camera.scale:0;
    const view=part.shared_viewbox;
    ctx.drawImage(images[part.id],view[0],view[1],view[2],view[3]);
  });ctx.restore();
}
function text(ctx,value,x,y,size=27,color='#2a413b'){
  ctx.fillStyle=color;ctx.font=`500 ${size}px system-ui,sans-serif`;ctx.textAlign='left';ctx.textBaseline='middle';
  ctx.fillText(value,x,y);
}

export function renderStudy(ctx,images,recipe,t){
  const state=structureState(recipe,t);
  // The card supports labels; the anatomical cutouts themselves retain alpha.
  ctx.fillStyle='#f4eedf';ctx.fillRect(22,18,1236,46);
  text(ctx,recipe.label,46,42,35);
  text(ctx,state.mode==='reveal'?'逐层出现':state.mode==='focus'?'原位高亮 · 局部近景':'结构总览',870,42,27);
  ctx.save();ctx.beginPath();ctx.rect(...MAIN);ctx.clip();
  layers(ctx,images,recipe,state.camera,state.opacities,state.mode==='focus'?state.index:-1);ctx.restore();
  // Context overview has the exact source registration too. Its highlight box
  // indicates the selected SOURCE bounds and never moves an isolated layer.
  const overview=fit(recipe.composite_bounds,INSET,12);
  layers(ctx,images,recipe,overview,recipe.layers.map(()=>1));
  if(state.mode==='focus'){
    const b=recipe.layers[state.index].content_bounds;
    ctx.strokeStyle='#755934';ctx.lineWidth=2;ctx.setLineDash([5,4]);
    ctx.strokeRect(overview.x+b[0]*overview.scale,overview.y+b[1]*overview.scale,
      (b[2]-b[0])*overview.scale,(b[3]-b[1])*overview.scale);ctx.setLineDash([]);
  }
  ctx.fillStyle='#f4eedf';ctx.fillRect(836,304,390,326);
  text(ctx,'位置总览',946,286,27);
  recipe.layers.forEach((part,i)=>{
    const active=state.mode==='focus'?i===state.index:state.opacities[i]>.9;
    const y=338+i*43;
    ctx.fillStyle=active?'#476a5c':'#a7aea2';ctx.beginPath();ctx.arc(859,y,5,0,Math.PI*2);ctx.fill();
    text(ctx,part.label,877,y,30,active?'#263f35':'#7a847d');
  });
  ctx.fillStyle='#f4eedf';ctx.fillRect(22,658,1236,48);
  text(ctx,recipe.presentation_note,46,682,27);
  return state;
}
