// Contact geometry is expressed in exact original-image pixels.
export const clamp=x=>Math.max(0,Math.min(1,x));
const lerp=(a,b,u)=>a+(b-a)*u;
const phase=(t,a,b)=>{let u=clamp((t-a)/(b-a));return u*u*(3-2*u)};
function draw(ctx,images,r,id,point,anchor,scale,angle=0){
 const im=images[id],b=r.images[id].bounds;
 ctx.save();ctx.translate(...point);ctx.rotate(angle);ctx.scale(scale,scale);
 ctx.drawImage(im,b[0],b[1],b[2]-b[0],b[3]-b[1],b[0]-anchor[0],b[1]-anchor[1],b[2]-b[0],b[3]-b[1]);ctx.restore();
}
export function glucoseGeometry(r,t){
 const insert=phase(t,.4,1.2),approach=phase(t,2.8,3.6),retreat=phase(t,4.9,5.6);
 const u=approach*(1-retreat);
 const port=[lerp(1090,920,u),310];
 return {port,finger:r.finger,stripEnd:[port[0],port[1]+90],
   insert,stripPort:[port[0],port[1]+(1-insert)*80],
   sample:t>=3.6&&t<4.9,reading:t>=4.3,press:phase(t,5.5,6.2)};
}
export function renderStudy(ctx,images,r,t){
 const g=glucoseGeometry(r,t);
 draw(ctx,images,r,'arm',r.finger,r.finger_source,.5);
 // A generic lancing pen contacts the side of this same fingertip, then withdraws.
 if(t>=1.35&&t<2.8){
  const u=phase(t,1.35,2.15)*(1-phase(t,2.4,2.8));
  const x=lerp(1070,r.finger[0],u),y=lerp(420,r.finger[1],u);
  ctx.save();ctx.translate(x,y);ctx.fillStyle='#647d87';ctx.strokeStyle='#3d535b';ctx.lineWidth=2;
  ctx.beginPath();ctx.roundRect(0,-10,105,20,8);ctx.fill();ctx.stroke();
  ctx.fillStyle='#e3e5db';ctx.fillRect(0,-7,14,14);ctx.fillStyle='#bd7c69';
  ctx.beginPath();ctx.arc(55,-10,t>=2.15&&t<2.4?3:5,0,Math.PI*2);ctx.fill();ctx.restore();
 }
 const blood=t>=2.2?(1-g.press):0;
 if(blood>0){ctx.save();ctx.globalAlpha=blood;ctx.fillStyle='#a94e40';ctx.beginPath();ctx.arc(...r.finger,4,0,2*Math.PI);ctx.fill();ctx.restore()}
 // Contacts stay in the meter port after insertion. Rotate the strip, not its aspect ratio.
 draw(ctx,images,r,'strip',g.stripPort,r.strip_contact,90/r.strip_length,Math.PI);
 draw(ctx,images,r,'meter',g.port,r.meter_port,.24);
 if(g.reading){
  const screen=[g.port[0]+(585-r.meter_port[0])*.24,g.port[1]+(475-r.meter_port[1])*.24];
  ctx.fillStyle='#263b3a';ctx.textAlign='center';ctx.textBaseline='middle';ctx.font='600 20px sans-serif';
  ctx.fillText('读取完成',screen[0],screen[1]);
 }
 if(g.press>0){
  const point=[lerp(1040,r.finger[0],g.press),lerp(510,r.finger[1],g.press)];
  draw(ctx,images,r,'dressing',point,[640,640],.035);
 }
 ctx.fillStyle='#f4eedf';ctx.fillRect(120,618,1040,70);
 ctx.fillStyle='#374d48';ctx.font='500 25px sans-serif';ctx.textAlign='left';
 const label=t<1.3?'双手已洗净擦干，装入匹配试纸':t<2.8?'指端侧面采血':t<4.3?'试纸保持连接，采样端接触血滴':t<5.5?'等待读取': '清洁敷料轻压止血';
 ctx.fillText(label,150,650);
 return {study:r.id,time:t,geometry:g,events:r.events.filter(e=>e.time<=t).map(e=>e.name)};
}

