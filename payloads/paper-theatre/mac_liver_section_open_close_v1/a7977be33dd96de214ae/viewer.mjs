import {renderStudy} from './runtime.mjs';
const recipe=await (await fetch('./sequence.json')).json();
const images={};
await Promise.all(Object.entries(recipe.images).map(async([id,info])=>{
  const image=new Image(); image.src=info.path; await image.decode(); images[id]=image;
}));
const canvas=document.querySelector('#stage'),ctx=canvas.getContext('2d');
const slider=document.querySelector('#time'),clock=document.querySelector('#clock');
const background=document.querySelector('#background');
document.querySelector('#title').textContent=recipe.title;
document.querySelector('#description').textContent=recipe.description;
document.querySelector('#scope').textContent=recipe.scope;
slider.max=recipe.duration;
let playing=false,start=0;
function seek(time){
  const t=Math.max(0,Math.min(recipe.duration,time));
  ctx.setTransform(1,0,0,1,0,0);ctx.fillStyle=background.value;ctx.fillRect(0,0,1280,720);
  window.__state=renderStudy(ctx,images,recipe,t);
  slider.value=t;clock.value=t.toFixed(2);
  return window.__state;
}
window.__seek=t=>{playing=false;return seek(t)};
window.__setBackground=color=>{background.value=color;return seek(+slider.value)};
window.__recipe=recipe;window.__ready=true;
slider.oninput=()=>window.__seek(+slider.value);
background.onchange=()=>seek(+slider.value);
document.querySelector('#play').onclick=()=>{
  playing=!playing;if(+slider.value>=recipe.duration)slider.value=0;
  start=performance.now()-Number(slider.value)*1000;
};
function tick(now){if(playing){const t=(now-start)/1000;seek(t);if(t>=recipe.duration)playing=false}requestAnimationFrame(tick)}
seek(0);requestAnimationFrame(tick);
