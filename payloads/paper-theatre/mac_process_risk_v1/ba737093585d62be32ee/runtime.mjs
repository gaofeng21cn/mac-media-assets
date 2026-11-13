// Original, dependency-free Canvas components. Explicit time makes seeks repeatable.
export const duration = 10;
const ink='#294a48',red='#b96359',blue='#609eaf',gold='#d4a352',paper='#f5efdf';
const clamp=v=>Math.max(0,Math.min(1,v));
const ease=v=>{v=clamp(v);return v*v*(3-2*v)};
export const phase=(t,a,b)=>ease((t-a)/(b-a));
export function riskCounts({population=100,before=10,after=5}={}){
  if(![population,before,after].every(Number.isInteger)||population<1||population>400||before<0||after<0||before>population||after>population)throw Error('事件人数须为同一分母内的整数');
  return {population,before,after,absoluteDifference:before-after};
}
export function screeningCounts({population=100,disease=10,truePositive=8,falsePositive=9}={}){
  if(![population,disease,truePositive,falsePositive].every(Number.isInteger)||population<1||population>400||disease<0||disease>population||truePositive<0||truePositive>disease||falsePositive<0||falsePositive>population-disease)throw Error('四格人数必须与人群总数一致');
  return {population,disease,truePositive,falsePositive,falseNegative:disease-truePositive,trueNegative:population-disease-falsePositive};
}
function label(c,s,x,y,size=24,color=ink){c.fillStyle=color;c.font=`${size}px system-ui, sans-serif`;c.fillText(s,x,y)}
function line(c,points,color=ink,w=4){c.beginPath();c.moveTo(...points[0]);for(const p of points.slice(1))c.lineTo(...p);c.strokeStyle=color;c.lineWidth=w;c.lineJoin='round';c.lineCap='round';c.stroke()}
function ellipse(c,x,y,rx,ry,fill,stroke=ink){c.beginPath();c.ellipse(x,y,rx,ry,0,0,Math.PI*2);c.fillStyle=fill;c.fill();if(stroke){c.strokeStyle=stroke;c.lineWidth=3;c.stroke()}}
function box(c,x,y,w,h,fill,r=16){c.beginPath();c.roundRect(x,y,w,h,r);c.fillStyle=fill;c.fill();c.strokeStyle=ink;c.lineWidth=2;c.stroke()}
function arrow(c,x1,y1,x2,y2,color=ink,w=4){line(c,[[x1,y1],[x2,y2]],color,w);const a=Math.atan2(y2-y1,x2-x1);line(c,[[x2-12*Math.cos(a-.5),y2-12*Math.sin(a-.5)],[x2,y2],[x2-12*Math.cos(a+.5),y2-12*Math.sin(a+.5)]],color,w)}
function dot(c,x,y,color=red,r=9){ellipse(c,x,y,r,r,color,null)}
function note(c,s){label(c,s,64,630,25)}

function blood(c,t){
  label(c,'血管纵切面',70,155);box(c,90,220,1100,210,'#d8a59b',60);box(c,90,250,1100,150,'#f7e4db',40);
  const p=phase(t,2,6);c.beginPath();c.moveTo(450,250);c.bezierCurveTo(510,250,510,250+64*p,620,250+64*p);c.bezierCurveTo(730,250+64*p,730,250,790,250);c.fillStyle=gold;c.fill();
  c.beginPath();c.moveTo(450,400);c.bezierCurveTo(510,400,510,400-54*p,620,400-54*p);c.bezierCurveTo(730,400-54*p,730,400,790,400);c.fill();
  for(let i=0;i<11;i++){const x=130+((i*91+t*58)%1000);ellipse(c,x,327+Math.sin(i)*6,15,8,red,null)}
  arrow(c,150,490,410,490,red);label(c,'血流方向',155,535);line(c,[[650,260],[790,175],[1000,175]],gold);label(c,p>.5?'斑块使管腔变窄':'血管壁与管腔',800,160);note(c,'观察管壁、管腔和血流的空间关系');
}
function gas(c,t){
  ellipse(c,565,280,245,135,'#e7c4ae');label(c,'肺泡内空气',455,245,30);box(c,230,470,820,90,'#e7aaaa',35);label(c,'肺毛细血管',70,520,22);line(c,[[320,435],[900,435]],blue,8);
  const p=phase(t,1.5,7);arrow(c,470,325,470,490,red);arrow(c,675,485,675,320,blue);label(c,'氧气 O₂',300,380,26,red);label(c,'二氧化碳 CO₂',730,390,26,blue);
  for(let i=0;i<3;i++){dot(c,470+(i-1)*15,330+p*165,red,7);dot(c,675+(i-1)*15,485-p*165,blue,7)}
  for(let i=0;i<5;i++)ellipse(c,350+i*135,525,24,13,red,null);note(c,'两种气体沿相反方向跨过肺泡—毛细血管屏障');
}
function insulin(c,t){
  box(c,600,150,540,400,'#deead9',35);line(c,[[600,150],[600,550]],ink,8);label(c,'细胞外',120,180,30);label(c,'细胞内',805,180,30);
  const p=phase(t,1,4),g=phase(t,5,8);dot(c,250+315*p,285,gold,15);box(c,575,260,50,50,'#ddd0a7',8);label(c,'胰岛素与受体结合',110,240,25);line(c,[[345,245],[530,275]],gold);
  box(c,570,385,62,75,p>.8?'#a1bba4':'#cbd1c2',8);label(c,'葡萄糖转运',750,430,26);dot(c,210+620*g,420,red,12);arrow(c,270,480,815,480,red);note(c,'胰岛素信号促进葡萄糖进入部分组织细胞');
}
function feedback(c,t){
  const p=phase(t,1,4),q=phase(t,5,8);for(const [x,s] of [[110,'调节中枢'],[480,'激素信号'],[850,'靶器官']]){box(c,x,255,280,115,'#e3d9b9');label(c,s,x+52,325,32)}
  arrow(c,390,312,480,312,p>.5?gold:ink);arrow(c,760,312,850,312,p>.8?gold:ink);line(c,[[990,385],[990,490],[245,490],[245,385]],q>.3?red:'#c6c3b4',5);line(c,[[225,385],[265,385]],red,6);label(c,'反馈抑制上游信号',455,545,30,red);note(c,'展示调节关系；具体激素轴由本集证据与标注确定');
}
function inflammation(c,t){
  box(c,90,180,1100,150,'#ead2c3',35);label(c,'血管内',105,150,27);line(c,[[100,330],[1180,330]],ink,6);label(c,'局部组织',105,390,27);ellipse(c,935,485,95,65,'#d9a69b');label(c,'损伤部位',860,590,26);
  const p=phase(t,1,8);for(let i=0;i<4;i++){const q=clamp((p-i*.14)/.58);const x=230+i*70+q*(670-i*70),y=250+q*215;dot(c,x,y,'#e6dabc',19);dot(c,x-3,y-1,'#8b7c9c',8)}
  arrow(c,520,380,810,455,gold);label(c,'免疫细胞向局部募集',310,535,27);note(c,'免疫细胞跨越血管壁，向受损组织移动');
}
function metastasis(c,t){
  const p=phase(t,1,9);box(c,80,175,260,370,'#e2cfb7');box(c,935,175,260,370,'#d3dec9');label(c,'原发部位',115,155,28);label(c,'远处部位',970,155,28);box(c,320,290,640,100,'#dfb8b2',25);
  for(let i=0;i<7;i++){const a=i*Math.PI*2/7;dot(c,230+32*Math.cos(a),335+32*Math.sin(a),red,15)}
  const x=290+730*p,y=335;dot(c,x,y,red,15);arrow(c,430,430,810,430,red);label(c,'经血液或淋巴传播',420,485,27);
  const seed=phase(t,8,10);for(let i=0;i<5;i++){const a=i*Math.PI*2/5;dot(c,1045+28*seed*Math.cos(a),335+28*seed*Math.sin(a),red,12*seed+1)}note(c,'从局部脱离、进入循环，到远处形成新的病灶');
}
function risk(c,t,spec){
  const x=riskCounts(spec.example);const cols=Math.ceil(Math.sqrt(x.population)),step=320/cols;for(const [left,n,title] of [[100,x.before,'干预前'],[730,x.after,'干预后']]){label(c,title,left,160,32);for(let i=0;i<x.population;i++){const fill=i<n?red:'#d5d8cc';dot(c,left+(i%cols)*step,210+Math.floor(i/cols)*step,fill,Math.min(10,step*.3))}label(c,`${n} / ${x.population}`,left+70,575,32)}
  if(t>3){arrow(c,490,340,640,340);label(c,`相差 ${x.absoluteDifference} 人`,482,410,24)}note(c,'演示数据：比较相同人数、相同随访时段的事件人数');
}
function screening(c,t,spec){
  const x=screeningCounts(spec.example),p=phase(t,2,7),cols=Math.ceil(Math.sqrt(x.population)),step=350/cols;for(let i=0;i<x.population;i++){const disease=i<x.disease;const positive=disease?i<x.truePositive:i<x.disease+x.falsePositive;const px=100+(i%cols)*step,py=210+Math.floor(i/cols)*step,r=Math.min(10,step*.28);dot(c,px,py,disease?red:'#c6d6cd',r);if(positive&&p>.2){c.strokeStyle=gold;c.lineWidth=2;c.strokeRect(px-r-3,py-r-3,2*r+6,2*r+6)}}
  label(c,'实际状态：红点为患病者',80,160,27);label(c,'金框：检测阳性',80,600,25,gold);const names=[['真阳性',x.truePositive,red],['假阳性',x.falsePositive,gold],['假阴性',x.falseNegative,red],['真阴性',x.trueNegative,blue]];
  names.forEach(([title,n,color],i)=>{const xx=640+(i%2)*265,yy=230+Math.floor(i/2)*190;box(c,xx,yy,235,145,'#faf6e9');label(c,title,xx+30,yy+45,28);label(c,String(n),xx+85,yy+110,44,color)});note(c,'演示数据：检测结果与真实疾病状态是两个维度');
}
function endoscope(c,t){
  box(c,75,165,1130,360,'#d8aca2',35);box(c,75,200,1130,250,'#f4d8c8',30);label(c,'肠腔局部放大',90,145,28);ellipse(c,865,440,48,65,red);const p=phase(t,1,4),q=phase(t,5,7),r=phase(t,8,10);const tip=280+470*p-280*r;
  line(c,[[90,285],[tip,285]],'#667c78',45);line(c,[[tip,285],[tip+65,345],[tip+100,395]],ink,7);const jaw=12*(1-q);line(c,[[tip+100,395],[tip+120,408-jaw]],ink,5);line(c,[[tip+100,395],[tip+120,408+jaw]],ink,5);
  if(q>.8)dot(c,tip+118,408,red,7);label(c,'观察病变 → 靶向取样 → 回收标本',240,585,30);note(c,'局部二维示意，保留镜身、器械、病变的相对位置');
}
function skin(c,t){
  box(c,120,260,1040,55,'#dfc19d',8);box(c,120,315,1040,200,'#d7a89a',8);box(c,120,515,1040,65,'#e8d69d',8);label(c,'表皮',60,294,24);label(c,'真皮',60,420,24);label(c,'皮下',60,557,24);const p=phase(t,2,7);
  if(p>0){c.fillStyle=paper;c.beginPath();c.moveTo(610-40*p,250);c.lineTo(610,330+85*p);c.lineTo(610+40*p,250);c.fill()}
  for(let i=0;i<5;i++)dot(c,500+i*60,175+(i===2?120*p:0),blue,9);label(c,'屏障完整',185,190,30);label(c,'屏障受损',810,190,30);note(c,'对照皮肤分层与局部屏障变化');
}
function spine(c,t){
  label(c,'腰椎局部侧面关系',100,150,30);for(let i=0;i<3;i++)box(c,370,200+i*135,265,90,'#dfd5b8',22);for(let i=0;i<2;i++)box(c,390,290+i*135,225,45,'#c3d5d0',12);
  line(c,[[730,175],[730,570]],gold,15);line(c,[[730,330],[880,390]],gold,12);const p=phase(t,2,8);ellipse(c,610+42*p,312,30+40*p,20,blue);label(c,'椎间盘',150,330,27);line(c,[[280,320],[385,312]],blue);label(c,'神经根',910,405,27);note(c,'局部关系示意：观察椎间盘后方突出与邻近神经');
}
function eye(c,t){
  for(const [cx,title,long] of [[345,'正常成像',false],[930,'近视成像',true]]){ellipse(c,cx,340,long?200:175,150,'#e4e8d9');ellipse(c,cx-110,340,22,66,'#b6d0d3');const retina=cx+(long?190:165),focus=cx+(long?155:165);line(c,[[retina,270],[retina,410]],red,8);label(c,title,cx-110,160,32);const p=phase(t,1,6);for(const dy of [-70,70]){line(c,[[cx-245,340+dy],[cx-110,340+dy],[focus,340]],gold,3);if(long&&p>.5)line(c,[[focus,340],[retina,340-dy*.2]],gold,3)}dot(c,focus,340,gold,7);label(c,long?'焦点在视网膜前':'焦点在视网膜上',cx-135,570,26)}note(c,'对比光线焦点与视网膜的位置');
}
const draw={blood,gas,insulin,feedback,inflammation,metastasis,risk,screening,endoscope,skin,spine,eye};
export function render(ctx,time,spec){
  if(!draw[spec.scene])throw Error('未知医学组件');const t=Math.max(0,Math.min(duration,Number(time)||0));ctx.save();ctx.clearRect(0,0,1280,720);ctx.fillStyle=paper;ctx.fillRect(0,0,1280,720);label(ctx,spec.title,64,80,38);draw[spec.scene](ctx,t,spec);ctx.restore();
}
