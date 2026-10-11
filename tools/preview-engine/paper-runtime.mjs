// Reusable deterministic paper interactions. All timings are supplied by the shot.
export const clamp = x => Math.max(0, Math.min(1, x));
export const ease = x => { const t = clamp(x); return t*t*(3-2*t); };
export const phase = (t,start,end) => ease((t-start)/(end-start));
export const lerp=(a,b,t)=>a+(b-a)*t;
export function arc(a,b,u,lift=0){return {x:lerp(a.x,b.x,u),y:lerp(a.y,b.y,u)-Math.sin(Math.PI*u)*lift};}
export function poseAt(t, keys) {
 const next=keys.findIndex(k=>k.time>t);
 if(next===0)return {...keys[0]}; if(next<0)return {...keys.at(-1)};
 const a=keys[next-1],b=keys[next],u=ease((t-a.time)/(b.time-a.time));
 return {...a,x:lerp(a.x,b.x,u),y:lerp(a.y,b.y,u),angle:lerp(a.angle||0,b.angle||0,u),lift:Math.sin(Math.PI*u)*(b.lift||0)};
}
export class PaperStage {
 constructor(canvas,assets){this.ctx=canvas.getContext('2d');this.assets=assets;this.layout=[];this.events=[];}
 begin(t){const c=this.ctx;this.t=t;this.layout=[];this.events=[];c.setTransform(1,0,0,1,0,0);c.clearRect(0,0,1280,720);c.fillStyle='#f4eedf';c.fillRect(0,0,1280,720);}
 piece(id,{x=640,y=360,w=400,h,angle=0,opacity=1,hinge=1,shadow=7,flip=false,crop,z=0}={}) {
  const a=this.assets[id];if(!a)return;
  const b=crop||a.bounds||[0,0,a.image.width,a.image.height]; const bw=b[2]-b[0],bh=b[3]-b[1];h=h||w*bh/bw;
  const c=this.ctx;c.save();c.globalAlpha=opacity;c.translate(x,y);c.rotate(angle);c.scale((flip?-1:1)*hinge,1);
  c.shadowColor='rgba(53,36,19,.22)';c.shadowBlur=shadow;c.shadowOffsetY=shadow*.55;
  c.drawImage(a.image,b[0],b[1],bw,bh,-w/2,-h/2,w,h);c.restore();
  this.layout.push({id,x,y,width:w*Math.abs(hinge),height:h,angle,z,crop:b});
 }
 contact(name,t,at){if(Math.abs(this.t-t)<.15)this.events.push({name,time:t,...at});}
}
