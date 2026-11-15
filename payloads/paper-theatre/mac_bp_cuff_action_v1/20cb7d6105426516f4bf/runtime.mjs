// Fitted upper-arm cuff; complete source bytes, all points in the same coordinate group.
export const clamp=x=>Math.max(0,Math.min(1,x));
export const phase=(t,a,b)=>{let u=clamp((t-a)/(b-a));return u*u*(3-2*u)};
export function cuffState(r,t){const s=r.steps;return Object.fromEntries(
 [['move','cuff_move'],['wrap','wrap'],['monitor','monitor'],['read','read'],['remove','remove']].map(([key,k])=>[key,phase(t,s[k].start,s[k].end)]));}
const lerp=(a,b,u)=>a+(b-a)*u;
function piece(ctx,images,r,id,x,y,width,angle=0,alpha=1){
 const b=r.images[id].bounds,scale=width/(b[2]-b[0]),h=(b[3]-b[1])*scale;
 ctx.save();ctx.globalAlpha=alpha;ctx.translate(x,y);ctx.rotate(angle);
 ctx.drawImage(images[id],b[0],b[1],b[2]-b[0],b[3]-b[1],-width/2,-h/2,width,h);ctx.restore();
}
export function cuffLayout(r,t){
 const st=cuffState(r,t),contact=clamp((st.move-.7)/.3)*(1-st.remove);
 const width=166*(1+.06*(1-st.wrap)),angle=-.95;
 const b=r.images.cuff_wrapped.bounds,k=width/(b[2]-b[0]);
 const port=r.cuff_port,dx=(port[0]-(b[0]+b[2])/2)*k,dy=(port[1]-(b[1]+b[3])/2)*k;
 return {state:st,contact,cuff:{x:300,y:390,width,angle},
   port:[300+dx*Math.cos(angle)-dy*Math.sin(angle),390+dx*Math.sin(angle)+dy*Math.cos(angle)],
   monitor:[lerp(1190,1100,st.monitor),550]};
}
export function renderStudy(ctx,images,r,t){
 const l=cuffLayout(r,t),st=l.state,settled=st.move*(1-st.remove);
 ctx.fillStyle='#bba581';ctx.fillRect(180,532,1010,24);
 ctx.fillStyle='#d9c7a6';ctx.fillRect(391,503,352,24);
 ctx.save();ctx.translate(100,-10);ctx.scale(.85,.85);
 piece(ctx,images,r,'arm',520,390,880);
 piece(ctx,images,r,'cuff_open',lerp(1010,300,settled),lerp(190,390,settled),lerp(245,166,settled),-.95*settled,1-l.contact);
 piece(ctx,images,r,'cuff_wrapped',l.cuff.x,l.cuff.y,l.cuff.width,l.cuff.angle,l.contact);
 piece(ctx,images,r,'monitor',...l.monitor,190);
 if(l.contact>0){ctx.save();ctx.globalAlpha=l.contact;ctx.strokeStyle='#647e8e';ctx.lineWidth=6;ctx.lineCap='round';
 ctx.beginPath();ctx.moveTo(...l.port);ctx.bezierCurveTo(l.port[0]+100,l.port[1]+120,920,605,l.monitor[0]-72,566);ctx.stroke();ctx.restore()}
 ctx.restore();
 ctx.fillStyle='#f4eedf';ctx.fillRect(120,618,1040,70);
 ctx.fillStyle='#3c5750';ctx.font='500 25px sans-serif';ctx.textAlign='center';
 ctx.fillText(t<2?'袖带贴合裸露上臂':t<5.2?'前臂承托，保持安静与静止':'测量结束后取下袖带',640,650);
 if(st.read>0&&st.remove<1){ctx.globalAlpha=st.read*(1-st.remove);ctx.fillText('记录本次结果',985,220);ctx.globalAlpha=1}
 return {study:r.id,time:t,...l,events:r.events.filter(e=>e.time<=t).map(e=>e.name)};
}

