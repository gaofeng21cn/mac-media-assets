import type {Stage} from './kit/stage';
import {clamp,hash} from './kit/motion';
import {cutout,tornEllipse,tape,grain} from './kit/materials';
import {clipFastener} from './kit/props';
export const ease=(t:number,a:number,b:number)=>{let u=clamp((t-a)/(b-a));return u*u*(3-2*u)};
export function env(s:Stage,id:string){const old=s.tracking;s.tracking=false;s.g.drawImage(s.images[id],0,0,1280,720);s.tracking=old}
export function img(s:Stage,id:string,x:number,y:number,w:number,r=0,lift=2){s.image(id,{x,y,w,rotation:r,lift})}
export function fly(s:Stage,id:string,x0:number,y0:number,x:number,y:number,w:number,t:number,a:number,b:number,r=0){const u=ease(t,a,b);img(s,id,x0+(x-x0)*u,y0+(y-y0)*u-Math.sin(u*Math.PI)*40,w,r+(1-u)*.05,2+Math.sin(u*Math.PI)*9)}
export function shadowShape(s:Stage,p:{x:number,y:number},w:number,h:number,color:string,seed=21){cutout(s,p,tornEllipse(w/2,h/2,seed,1.8),color,seed,3)}
export function notebook(s:Stage,x:number,y:number,w:number,title:string,t=10,rotation=-.04){s.group({x,y,rotation},()=>{
 s.paper({x:0,y:0,w,h:w*.82,color:'#eee9db',seed:82,lift:3,name:'记录本'});s.paper({x:0,y:0,w:w*.91,h:w*.76,color:'#faf4e7',seed:83,lift:1,name:'实际记录页'});
 const g=s.g;g.strokeStyle='#8a806e';g.lineWidth=2;
 for(let j=0;j<5;j++){g.beginPath();g.ellipse(-w*.40,-w*.30+j*w*.15,10,5,-.4,0,Math.PI*2);g.stroke()}
 s.text(title,0,-w*.27,23,'#43524b');g.lineWidth=.8;g.strokeStyle='#b5b4a6';
 for(let j=0;j<5;j++){let yy=-w*.13+j*w*.085;g.beginPath();g.moveTo(-w*.29,yy);g.lineTo(w*.34,yy);g.stroke()}
 const u=ease(t,.8,3.2);g.strokeStyle='#787565';g.lineWidth=1.5;
 for(let j=0;j<4;j++){g.beginPath();for(let k=0;k<Math.floor(14*u);k++){let xx=-w*.26+k*w*.033,yy=-w*.10+j*w*.088+(hash(j*20+k)-.5)*6;if(k)g.lineTo(xx,yy);else g.moveTo(xx,yy)}g.stroke()}
 clipFastener(s,w*.32,-w*.38-.2,0);
})}
export function report(s:Stage,x:number,y:number,w:number,title:string,rotation=-.035){s.group({x,y,rotation},()=>{
 s.paper({x:0,y:0,w,h:w*1.10,color:'#f9f4e8',seed:65,lift:4,name:'化验与检查报告'});tape(s,{x:-w*.23,y:-w*.51,rotation:-.13},60,73);s.text(title,0,-w*.36,23,'#42584e');
 const g=s.g;g.strokeStyle='#b9b7a9';g.lineWidth=.8;
 for(let i=0;i<6;i++){g.beginPath();g.moveTo(-w*.38,-w*.18+i*w*.098);g.lineTo(w*.36,-w*.18+i*w*.098);g.stroke();g.fillStyle='#66756b';g.fillRect(-w*.34,-w*.195+i*w*.098,w*(.10+hash(i)*.10),2);g.fillRect(w*.15,-w*.195+i*w*.098,w*.09,2)}
})}
export function clock(s:Stage,x:number,y:number,w=115,hour=8,minute=0){s.group({x,y},()=>{
 shadowShape(s,{x:0,y:0},w,w,'#f0eadb',13);let g=s.g;g.strokeStyle='#57594e';g.lineWidth=2;
 for(let i=0;i<12;i++){let a=i*Math.PI/6;g.beginPath();g.moveTo(Math.sin(a)*w*.39,-Math.cos(a)*w*.39);g.lineTo(Math.sin(a)*w*.44,-Math.cos(a)*w*.44);g.stroke()}
 for(const[a,l,th]of [[(hour+minute/60)*Math.PI/6,w*.24,4],[minute*Math.PI/30,w*.37,2]]){g.lineWidth=th;g.beginPath();g.moveTo(0,0);g.lineTo(Math.sin(a)*l,-Math.cos(a)*l);g.stroke()}
 g.beginPath();g.arc(0,0,3,0,Math.PI*2);g.fillStyle='#57594e';g.fill();
})}
export function calendar(s:Stage,x:number,y:number,w:number,month:string,rotation=0){s.group({x,y,rotation},()=>{
 s.paper({x:0,y:0,w,h:w*.8,color:'#f6efe0',seed:13,lift:4,name:'日历'});const g=s.g;
 g.fillStyle='#456a7a';g.fillRect(-w*.46,-w*.38,w*.92,w*.12);s.text(month,0,-w*.32,20,'#fbf5e8');
 for(let row=0;row<4;row++)for(let col=0;col<7;col++){let xx=-w*.35+col*w*.115,yy=-w*.12+row*w*.115;g.fillStyle=row===2&&col===3?'#b8624e':'#bcb6a4';g.fillRect(xx,yy,w*.035,w*.035)}
 for(const xx of [-w*.27,w*.27]){g.strokeStyle='#6f6d61';g.lineWidth=3;g.beginPath();g.ellipse(xx,-w*.38,6,12,0,0,Math.PI*2);g.stroke()}
})}
export function carton(s:Stage,x:number,y:number,w:number,turn:number,front='无糖',back='营养标示'){s.group({x,y,rotation:-.035},()=>{
 const g=s.g;const face=Math.cos(turn*Math.PI);g.save();g.scale(Math.max(.055,Math.abs(face)),1);
 s.paper({x:0,y:0,w,h:w*1.25,color:face>0?'#e5d1a4':'#ece6d5',seed:42,lift:5,name:'食物包装'});
 cutout(s,{x:0,y:-w*.57},[{x:-w*.47,y:0},{x:-w*.32,y:-w*.15},{x:w*.35,y:-w*.15},{x:w*.47,y:0}],'#ddd2b8',63,2);
 s.text(face>0?front:back,0,-w*.24,27,'#435d50');
 g.strokeStyle='#b4a88c';g.lineWidth=1;
 if(face>0){for(let i=0;i<10;i++)g.fillRect(-w*.3+i*w*.063,w*.20,1.5,w*.16);shadowShape(s,{x:0,y:0},w*.30,w*.30,'#eff0d8',23)}
 else{for(let i=0;i<5;i++){g.beginPath();g.moveTo(-w*.34,-w*.02+i*w*.11);g.lineTo(w*.34,-w*.02+i*w*.11);g.stroke()}s.text('碳水 · 能量',0,w*.06,19,'#536154');s.text('每份 / 每100克',0,w*.39,17,'#536154')}
 g.restore();
})}
export function medicine(s:Stage,x:number,y:number,w=100,rotation=.035){s.group({x,y,rotation},()=>{
 s.paper({x:0,y:0,w,h:w*1.35,color:'#d9dcd4',seed:43,lift:3,name:'闭合药物包装'});for(let i=0;i<3;i++)for(let j=0;j<2;j++)shadowShape(s,{x:-w*.25+j*w*.50,y:-w*.40+i*w*.4},w*.27,w*.19,'#f6f1e5',i+j+22);
})}
export function phone(s:Stage,x:number,y:number,w=160,shown='120',rotation=-.04){s.group({x,y,rotation},()=>{
 cutout(s,{x:0,y:0},[{x:-w*.43,y:-w*.8},{x:w*.43,y:-w*.8},{x:w*.5,y:-w*.70},{x:w*.5,y:w*.70},{x:w*.43,y:w*.8},{x:-w*.43,y:w*.8},{x:-w*.5,y:w*.70},{x:-w*.5,y:-w*.70}],'#425b61',51,5);
 s.paper({x:0,y:0,w:w*.88,h:w*1.32,color:'#f2efe3',seed:53,lift:0,name:'求助电话屏幕'});s.text(shown,0,-w*.10,Math.min(34,w*.78/Math.max(1,shown.length)),'#2f524c');shadowShape(s,{x:0,y:w*.42},w*.30,w*.18,'#789887',61);
})}
export function band(s:Stage,x:number,y:number,w:number,p:number,title='一天'){s.group({x,y},()=>{
 const g=s.g;const opened=.10+.90*clamp(p);g.save();g.scale(opened,1);s.paper({x:0,y:0,w,h:165,color:'#f5efdf',seed:97,lift:4,name:'折叠时间纸带'});
 for(let i=0;i<4;i++){g.strokeStyle='#a9b29f';g.lineWidth=1;g.beginPath();g.moveTo(-w*.3+i*w*.2,-70);g.lineTo(-w*.3+i*w*.2,70);g.stroke()}
 s.text(title,-w*.30,-36,24,'#536a5c');g.restore();
})}
export function curve(s:Stage,x:number,y:number,w:number,t:number,variant=0){s.group({x,y},()=>{
 let g=s.g;g.save();g.strokeStyle=variant?'#ac6956':'#537e87';g.lineWidth=5;g.lineCap='round';g.beginPath();let end=Math.floor(64*ease(t,.4,2.6));
 for(let i=0;i<=end;i++){let xx=-w/2+i*w/64, yy=variant?Math.sin(i*.21)*24+Math.sin(i*.43)*14:Math.sin(i*.16)*42; if(i)g.lineTo(xx,yy);else g.moveTo(xx,yy)}g.stroke();g.restore();
 s.bounds({x:-w/2,y:-65,w,h:130,name:'变化曲线'});
})}

// Small objects keep their material identity; they are not backgrounds for prose.
export function cup(s:Stage,x:number,y:number,w=94,filled=true){s.group({x,y},()=>{
 const g=s.g;shadowShape(s,{x:0,y:0},w,w*.82,'#efefe2',512);
 g.save();g.strokeStyle='#697d80';g.lineWidth=6;g.beginPath();g.ellipse(w*.46,0,w*.16,w*.24,0,0,Math.PI*2);g.stroke();g.restore();
 shadowShape(s,{x:0,y:-w*.12},w*.69,w*.26,filled?'#aeb9b0':'#dbd7ca',514);
})}
export function specimen(s:Stage,x:number,y:number,w=82){s.group({x,y},()=>{
 s.paper({x:0,y:0,w,h:w*.87,color:'#e6e4d680',seed:534,lift:2,name:'带盖尿液标本容器'});
 s.paper({x:0,y:w*.16,w:w*.82,h:w*.25,color:'#dbbe7490',seed:535,lift:0,name:'容器内标本'});
 s.paper({x:0,y:-w*.45,w:w*1.08,h:w*.16,color:'#6b8790',seed:536,lift:1,name:'标本杯盖'});
})}
export function journal(s:Stage,x:number,y:number,w:number,t:number,title='完整记录'){
 notebook(s,x,y,w,title,t);s.group({x,y,rotation:-.04},()=>{
  const g=s.g,u=ease(t,1.2,3.5);g.save();g.lineCap='round';g.strokeStyle='#557e88';g.lineWidth=2.6;g.beginPath();
  const ys=[.09,-.03,.10,.02,.07,-.04];for(let i=0;i<Math.floor(6*u);i++){let px=-w*.25+i*w*.105,py=ys[i]*w;if(i)g.lineTo(px,py);else g.moveTo(px,py)}g.stroke();g.restore();
 });
}
