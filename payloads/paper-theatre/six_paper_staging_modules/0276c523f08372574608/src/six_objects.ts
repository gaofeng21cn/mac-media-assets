import type {Stage} from './kit/stage';
import {cutout,tornEllipse,tape,grain,halftone} from './kit/materials';
import {clipFastener,paperFolder,pocket} from './kit/props';
import {ease,img,env,calendar,clock,phone,medicine,cup,specimen} from './paper_objects';
export {ease,img,env,calendar,clock,phone,medicine,cup,specimen,tape,paperFolder};
export const stageIds:Record<string,string>={gout:'gout_stage',graves:'graves_stage',hashimoto:'hashimoto_stage',breast_nodules:'breast_stage',pcos:'pcos_stage',ckd:'kidney_stage'};
export const organIds:Record<string,string>={gout:'foot_joint',graves:'thyroid_neck',hashimoto:'thyroid_neck',breast_nodules:'breast_section',pcos:'pelvic_organs',ckd:'kidneys_alpha'};
export function paperEnvelope(s:Stage,pose:{x:number;y:number},w:number,contents:(mouth:{x:number;y:number})=>void){pocket(s,'envelope',pose,w,contents);}
export function organ(s:Stage,topic:string,x:number,y:number,w:number,r=0){const id=organIds[topic];const im=s.images[id];const visible=s.assets[id].registration?.anchors?.contentTop; // Asset identity owns content scale; directors still own cognitive proportions.
 img(s,id,x,y,w,r,3);}
export function page(s:Stage,x:number,y:number,w:number,title:string,r=0,t=8,kind='record'){
 s.group({x,y,rotation:r},()=>{
  s.paper({x:0,y:0,w,h:w*.91,color:'#f8f1df',seed:71,lift:3,name:title+'资料'});
  s.text(title,0,-w*.30,Math.min(25,w*.105),'#3c5754');
  const g=s.g;g.save();g.strokeStyle='#bbb29c';g.lineWidth=1;
  for(let i=0;i<3;i++){const y=-w*.13+i*w*.17;g.beginPath();g.moveTo(-w*.33,y);g.lineTo(w*.32,y);g.stroke()}
  if(kind==='image'){
   g.fillStyle='#49565d';g.fillRect(-w*.34,-w*.13,w*.67,w*.46);
   // Grey ultrasound texture is an abstract instrument display, never a fabricated patient's lesion.
   g.save();g.beginPath();g.rect(-w*.34,-w*.13,w*.67,w*.46);g.clip();g.translate(0,w*.10);halftone(g,w*.65,w*.42,'#b3b4a1',5,1.1);g.restore();
  }else{
   const u=ease(t,.4,2.1);g.strokeStyle='#61786d';g.lineWidth=2.1;
   for(let row=0;row<3;row++){g.beginPath();g.moveTo(-w*.29,-w*.08+row*w*.17);g.lineTo(-w*.29+w*.31*u,-w*.08+row*w*.17);g.stroke();g.beginPath();g.arc(w*.25,-w*.08+row*w*.17,2.2,0,Math.PI*2);g.fillStyle='#a67953';g.fill()}
  }g.restore();clipFastener(s,w*.29,-w*.45,.07);
 });
}
export function fileReceive(s:Stage,x:number,y:number,w:number,t:number,title:string,other='用药记录'){
 const u=ease(t,.9,3.6);paperEnvelope(s,{x,y},w,p=>{
  s.group({x:p.x,y:p.y-w*.24*(1-u)+w*.09*u,rotation:-.03*(1-u)},()=>page(s,0,0,w*.45,title,0,5));
 });
 if(other)page(s,x+w*.76,y+w*.24,w*.35,other,.065,t-3.2);
}
export function archiveFolder(s:Stage,x:number,y:number,w:number,t:number,title:string,subtitle:string){
 paperFolder(s,{x,y,rotation:-.025},w,ease(t,.25,1.8),()=>{
  page(s,-w*.16,0,w*.38,title,-.04,t,'record');page(s,w*.23,w*.02,w*.35,subtitle,.045,t-1.6,'record');
 },{height:w*.48,color:'#a38e60'});
}
export function lamp(s:Stage,x:number,y:number,t:number,night=true){
 s.group({x,y},()=>{const g=s.g;g.save();g.strokeStyle='#665845';g.lineWidth=7;g.beginPath();g.moveTo(0,65);g.lineTo(0,-30);g.stroke();g.restore();
 cutout(s,{x:0,y:-40},[{x:-24,y:-36},{x:24,y:-36},{x:49,y:17},{x:-49,y:17}],night?'#e8c584':'#bfb49b',402,3);
 cutout(s,{x:0,y:68},tornEllipse(39,9,403),'#74634d',404,2);
 });
}
export function nightSpace(s:Stage,t:number,topic=''){env(s,topic==='gout'?'gout_stage':'home');const g=s.g;g.save();const old=s.tracking;s.tracking=false;g.fillStyle='#253b535d';g.fillRect(0,0,1280,720);g.restore();s.tracking=old;if(topic!=='gout')lamp(s,1010,369,t,true);}
export function hospitalSpace(s:Stage,topic=''){env(s,stageIds[topic]||'lab');}
export function table(s:Stage,t:number,mode:string){env(s,'kitchen');img(s,'plate',548,325,360,-.025);img(s,'rice',495,345,117,-.055);img(s,'protein',576,360,94,.035);const u=ease(t,.6,3.4);
 img(s,'vegetables',813-202*u,228+17*u,157,-.05+.06*u,2+Math.sin(u*Math.PI)*5);img(s,'fruit',981,340,102,.06);cup(s,343,293,88,true);
 if(mode==='protein')bottle(s,951,213,75,t,'蛋白补充','先评估',false);if(mode==='salt')bottle(s,876,289,93,t,'调味','钠');if(mode==='water')cup(s,878,316,107,true);
}
export function bottle(s:Stage,x:number,y:number,w:number,t:number,front:string,back:string,turn=true){s.group({x,y,rotation:-.03},()=>{
 const u=turn?ease(t,.7,2.9):0,f=Math.cos(u*Math.PI),g=s.g;g.save();g.scale(Math.max(.055,Math.abs(f)),1);
 cutout(s,{x:0,y:0},[{x:-w*.25,y:-w*.78},{x:w*.25,y:-w*.78},{x:w*.25,y:-w*.44},{x:w*.47,y:-w*.23},{x:w*.45,y:w*.70},{x:-w*.45,y:w*.70},{x:-w*.47,y:-w*.23},{x:-w*.25,y:-w*.44}],'#8baaa298',310,3);
 s.paper({x:0,y:-w*.78,w:w*.54,h:w*.12,color:'#5c756a',seed:312,lift:.8,name:'瓶盖'});s.paper({x:0,y:0,w:w*.74,h:w*.58,color:'#ebe1c9',seed:314,lift:.4,name:'瓶身标签'});s.text(f>0?front:back,0,0,Math.min(22,w*.62/Math.max(1,(f>0?front:back).length)),'#3b5651');g.restore();
 });}
export function medicineBag(s:Stage,t:number,title:string){hospitalSpace(s);const u=ease(t,.4,2.5);paperEnvelope(s,{x:387,y:352},320,()=>{});
 medicine(s,561+102*u,291-20*Math.sin(Math.PI*u),95,-.04);bottle(s,826,316,90,t-2,'补充剂','成分');page(s,1016,305,147,title,.04,t-3);
}
export function microscope(s:Stage,x:number,y:number,w:number){s.group({x,y},()=>{
 cutout(s,{x:0,y:0},[{x:-w*.37,y:w*.4},{x:w*.43,y:w*.4},{x:w*.43,y:w*.50},{x:-w*.42,y:w*.50}],'#677f80',901,3);
 cutout(s,{x:w*.10,y:-w*.05},[{x:-w*.15,y:w*.40},{x:w*.07,y:w*.40},{x:w*.16,y:-w*.27},{x:-w*.23,y:-w*.44},{x:-w*.35,y:-w*.21},{x:-w*.12,y:-w*.07}],'#829596',902,3);
 s.paper({x:-w*.03,y:w*.19,w:w*.57,h:w*.08,color:'#364d53',seed:903,lift:1,name:'显微镜载物台'});
 })}
export function lens(s:Stage,x:number,y:number,r:number,t:number,draw:()=>void){
 const u=ease(t,.4,2.6);s.group({x:x+54*(1-u),y:y-25*(1-u)},()=>{const g=s.g;
 s.clip(()=>{g.beginPath();g.arc(0,0,r,0,Math.PI*2)}, {x:-r,y:-r,w:r*2,h:r*2,name:'结构放大窗'},draw);
 g.save();s.shadow(3);g.strokeStyle='#ad9669';g.lineWidth=9;g.beginPath();g.arc(0,0,r+3,0,Math.PI*2);g.stroke();g.shadowColor='transparent';g.strokeStyle='#596d69';g.lineWidth=14;g.beginPath();g.moveTo(r*.70,r*.72);g.lineTo(r*1.29,r*1.32);g.stroke();g.restore();s.bounds({x:-r,y:-r,w:r*2.28,h:r*2.33,name:'放大镜'});
 });
}
export function chair(s:Stage,x:number,y:number){cutout(s,{x,y},[{x:-67,y:-68},{x:70,y:-67},{x:58,y:50},{x:-52,y:57}],'#acaa89',221,3);const g=s.g;g.save();g.strokeStyle='#7f735e';g.lineWidth=8;g.beginPath();g.moveTo(x-45,y+45);g.lineTo(x-55,y+123);g.moveTo(x+47,y+45);g.lineTo(x+53,y+123);g.stroke();g.restore()}

export function tissueSample(s:Stage,x:number,y:number,w=82){s.group({x,y},()=>{
 s.paper({x:0,y:0,w,h:w*.92,color:'#e6e7de85',seed:1220,lift:2,name:'密封组织样本容器'});
 cutout(s,{x:0,y:w*.13},[{x:-w*.11,y:-w*.06},{x:w*.16,y:-w*.08},{x:w*.10,y:w*.10},{x:-w*.16,y:w*.07}],'#c89687',1221,.4);
 s.paper({x:0,y:-w*.46,w:w*1.08,h:w*.16,color:'#7a9191',seed:1222,lift:1,name:'组织样本杯盖'});
});}
export function tobaccoPacket(s:Stage,x:number,y:number,w=71,t=0){const u=ease(t,1.1,3.1);s.group({x:x+335*u,y:y+19*u,rotation:.06+u*.08},()=>{
 s.paper({x:0,y:0,w,h:w*1.34,color:'#efe9d9',seed:1250,lift:3,name:'烟盒'});
 cutout(s,{x:0,y:w*.25},[{x:-w*.48,y:-w*.18},{x:w*.48,y:-w*.18},{x:w*.48,y:w*.39},{x:-w*.48,y:w*.39}],'#976b57',1251,.2);
 s.paper({x:0,y:-w*.63,w:w*.99,h:w*.25,color:'#f5efdf',seed:1252,lift:1,name:'打开的烟盒盖'});
 for(let i=0;i<3;i++){s.paper({x:(i-1)*w*.19,y:-w*.48,w:w*.13,h:w*.49,color:'#f1eee1',seed:1253+i,lift:.3,name:'烟盒内卷烟'});s.paper({x:(i-1)*w*.19,y:-w*.30,w:w*.13,h:w*.10,color:'#bb9863',seed:1260+i,lift:0,name:'卷烟滤嘴'});}
});}
