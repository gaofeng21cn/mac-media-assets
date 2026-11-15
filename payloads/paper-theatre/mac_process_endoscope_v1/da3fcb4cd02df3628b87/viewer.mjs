import {render,duration} from './runtime.mjs';
const spec=await(await fetch('./component.json')).json();
document.title=spec.title;const canvas=document.querySelector('canvas'),slider=document.querySelector('input');
const ctx=canvas.getContext('2d');let start=null,playing=false;
window.__seek=t=>{slider.value=Math.min(duration,Math.max(0,t));render(ctx,Number(slider.value),spec)};
document.querySelector('button').onclick=()=>{playing=!playing;start=null};slider.oninput=()=>{playing=false;window.__seek(slider.value)};
function frame(now){if(playing){if(start===null)start=now-Number(slider.value)*1000;const t=(now-start)/1000;if(t>=duration){playing=false;window.__seek(duration)}else window.__seek(t)}requestAnimationFrame(frame)}
window.__seek(0);window.__ready=true;requestAnimationFrame(frame);
