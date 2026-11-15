import type {Stage} from './kit/stage';
import type {Shot,ShotContext} from './kit/types';
import {cutout,tornEllipse,tape,halftone} from './kit/materials';
import {paperEnvelope} from './six_objects';
import directions from './scene_directions.json';
import {ease,img,env,organ,organIds,stageIds,page,fileReceive,archiveFolder,lamp,nightSpace,hospitalSpace,table,bottle,medicineBag,microscope,lens,chair,tissueSample,tobaccoPacket,calendar,clock,phone,medicine,cup,specimen} from './six_objects';
type Recipe={kind:string;topic:string;axis:string;x:number;y:number;labels:string[];events:Record<string,number>;intent:string;camera:string};
type Draw=(c:ShotContext,r:Recipe,name:string)=>void;
function specimenMove(s:Stage,t:number,x:number,y:number,type='blood'){const u=ease(t,.8,2.6);if(type==='blood')img(s,'blood',x+70*(1-u),y-45*(1-u),71,-.03,1+5*(1-u));else specimen(s,x+60*(1-u),y-32*(1-u),79)}
function crystals(s:Stage,t:number,remaining=1){
 // Eight stylized MSU needles belong to the local joint gap, never to bone or free space.
 const u=ease(t,2.3,3.8),amount=Math.round(8*remaining);
 s.group({x:0,y:32,opacity:u},()=>{for(let i=0;i<amount;i++){const x=-13+i*3.7,y=(i%3-1)*7;cutout(s,{x,y,rotation:(i%4-.8)*.35},[{x:-8,y:-1.1},{x:7,y:-.6},{x:9,y:.5},{x:-7,y:1.2}],'#d9e1db',710+i,.6)}});
}
function structure(s:Stage,topic:string,t:number,x:number,y:number,w:number,flap=false,crystal=0){
 s.group({x,y},()=>{organ(s,topic,0,0,w,-.02);
 if(topic==='gout'&&crystal>0)crystals(s,t,crystal);

 });
}
const anatomy:Draw=({stage:s,t},r,name)=>{
 env(s,'lab');const x=r.axis==='right'?796:466;const w=r.topic==='pcos'?490:r.topic==='ckd'?288:386;
 structure(s,r.topic,t,x,286,w,false,r.topic==='gout'?1:0);
 if(r.topic==='gout')lens(s,906,282,130,t,()=>{organ(s,'gout',0,-53,695);s.group({x:0,y:-37,scale:2.1},()=>crystals(s,t,1))});
 else if(r.topic==='graves'||r.topic==='hashimoto')lens(s,r.axis==='right'?350:930,275,116,t,()=>organ(s,r.topic,0,-66,597));
 else microscope(s,r.axis==='right'?295:1090,352,115);

 if(name==='pcos_calendar'||name==='ovulation_story'){calendar(s,r.axis==='right'?362:941,276,191,'月经记录',.05);}
 if(r.topic==='ckd'){specimenMove(s,t,856,385);specimenMove(s,t-1.1,974,385,'urine')}
};
const night:Draw=({stage:s,t},r,name)=>{
 nightSpace(s,t,r.topic);clock(s,317,188,105,2,10);
 if(r.topic==='gout'){
  structure(s,'gout',t,610,298,415,false,0);

 }else{img(s,'body',562,290,260,-.01);medicine(s,862,405,78);}
};
const flare:Draw=({stage:s,t,beat},r,name)=>{
 env(s,'home');let remaining=name==='crystal_time'?1-ease(t,3,7)*.66:1;
 structure(s,'gout',t,511,291,405,false,remaining);
 if(name==='joint_flare'||name==='early_flare'){const u=name==='joint_flare'?1-ease(t,1.1,3.7):ease(t,2.0,3)* (1-ease(t,5.3,7));s.group({x:512,y:324,opacity:u*.65},()=>cutout(s,{x:0,y:0},tornEllipse(40,27,740),'#bf756390',742,1))}
 calendar(s,977,252,175,name==='crystal_time'?'数月以后':'复查记录',.07);page(s,951,412,132,'尿酸与用药',-.05,t-3);
 if(name==='gout_close'){img(s,'shoes',268,423,159,-.04);cup(s,1031,412,82,true)}
};
const compare:Draw=({stage:s,t},r,name)=>{
 hospitalSpace(s,r.topic);const x=r.axis==='right'?837:450;const ox=r.axis==='right'?347:958;
 organ(s,r.topic,ox,258,r.topic==='ckd'?202:r.topic==='pcos'?284:244,-.025);
 const u=ease(t,.6,1.6),v=ease(t,2.3,3.7);
 page(s,x-95*(1-u),287-16*Math.sin(u*Math.PI),220,r.labels[0],-.07+.025*u,t,name.includes('breast')||name==='pcos_ultrasound'?'image':'record');
 page(s,x+155+80*(1-v),310-40*(1-v),196,r.labels[1],.05,t-2.0,name.includes('breast')?'image':'record');
 if(r.topic==='ckd'){specimenMove(s,t,ox-84,421);specimenMove(s,t-1.6,ox+60,421,'urine')}
 else if(name==='joint_clues'){specimenMove(s,t-2,986,406,'urine')}
 else if(r.topic==='graves'||r.topic==='hashimoto')specimenMove(s,t,1110,381);
};
const report:Draw=({stage:s,t},r,name)=>{
 env(s,stageIds[r.topic]);organ(s,r.topic,327,267,r.topic==='ckd'?239:r.topic==='pcos'?308:284,-.02);
 const u=ease(t,.6,1.6);page(s,725-65*(1-u),279-24*(1-u),269,r.labels[0],-.035,t,r.topic==='breast_nodules'?'image':'record');
 if(name==='birads_zero'){page(s,976,349-88*(1-ease(t,2,3.7)),178,r.labels[1],.065,t-2,'image')}
 else if(name==='birads_three'){calendar(s,996,326,180,'约六个月',.06)}
 else if(name==='birads_four'||name==='birads_five'||name==='biopsy_question'){paperEnvelope(s,{x:989,y:367},188,()=>{});page(s,1001,272,137,'取样评估',.05,t-2)}
 else if(name==='biopsy_pathology'){microscope(s,1013,335,159);const u=ease(t,1.1,2.8);tissueSample(s,898+45*(1-u),425-30*(1-u),74)}
 else if(name==='biopsy_guided'){microscope(s,991,330,139);page(s,1000,412,142,'用药核对',.05,t)}
 else if(r.topic==='ckd'){specimenMove(s,t,1018,387);}
 else if(name==='breast_sono')bottle(s,1009,354,93,t,'耦合剂','检查',false);
 else calendar(s,998,372,141,'记录日期',.035);
};
const timeline:Draw=({stage:s,t},r,name)=>{
 env(s,'home');organ(s,r.topic,331,282,r.topic==='ckd'?223:r.topic==='pcos'?308:294);
 const u=ease(t,.6,2.4);calendar(s,674,226,234,name==='cycle_gap'?'月经记录':'既往记录',-.045);calendar(s,978,293,182,name==='kidney_duration'?'至少三个月':'本次复查',.045);
 s.group({x:575,y:390,rotation:-u*.62,opacity:1-u*.70},()=>page(s,73,0,191,'此前记录',-.035,5));
 page(s,721,397,195,r.labels[0],-.025,t-2.2);medicine(s,1047,425,78,.04);
};
const plan:Draw=({stage:s,t},r,name)=>{
 hospitalSpace(s,r.topic);organ(s,r.topic,306,246,r.topic==='ckd'?213:r.topic==='pcos'?286:245,-.02);
 archiveFolder(s,694,318,415,t,r.labels[0],r.labels[1]);
 if(name==='thyroxine_morning'||name==='thyroxine_timing'){clock(s,1055,230,102,7,0);cup(s,1015,401,88,true);medicine(s,1126,373,67)}
 else if(name==='thyroxine_spacing'){bottle(s,996,329,78,t,'钙、铁','间隔',false);clock(s,1110,315,84,12,0)}
 else if(name==='thyroid_radio'||name==='thyroid_surgery')calendar(s,1071,312,145,'治疗后随访',.04);
 else{medicine(s,1036,360,96,.055);specimenMove(s,t-2.3,1123,371)}
};
const call:Draw=({stage:s,t},r,name)=>{
 nightSpace(s,t);organ(s,r.topic,393,287,r.topic==='ckd'?242:r.topic==='pcos'?350:316,-.04);
 const u=ease(t,.8,2.2);page(s,737,345-44*(1-u),207,r.labels[0],-.055,t);
 phone(s,954-32*ease(t,2.2,3.2),313,142,name==='kidney_urgent'||name==='kidney_acute'||name==='joint_urgent'?'及时就医':'联系医生',.04);
 if(name==='antithyroid_call'){medicine(s,760,458,73);page(s,1097,424,139,'血常规',.04,t-3)}
 if(name==='fever_throat'||name==='joint_urgent'){s.group({x:499,y:194,rotation:.12},()=>{s.paper({x:0,y:0,w:20,h:105,color:'#ece8d9',seed:997,lift:3,name:'体温计'});s.paper({x:0,y:16,w:7,h:47,color:'#bf796a',seed:998,lift:.2,name:'温度刻度'})})}
};
const bag:Draw=({stage:s,t},r,name)=>{
 env(s,'clinic'); // The route to the clinic is a change of space, not an image behind a page title.
 const u=ease(t,.5,3.6);s.group({x:700-57*u,y:335},()=>fileReceive(s,0,0,375,t,r.labels[0],r.labels[1]));
 organ(s,r.topic,290,293,r.topic==='ckd'?222:r.topic==='pcos'?289:271,-.035);
 calendar(s,1025,285,163,'下一次预约',.035);
};
const tabletop:Draw=({stage:s,t},r,name)=>{table(s,t,name==='kidney_salt'?'salt':name==='kidney_protein'?'protein':name==='gout_water'||name==='kidney_potassium'?'water':'meal');
 if(name==='plant_returns'||name==='meat_portion'){const u=ease(t,2.3,4.7);img(s,'protein',712+193*u,356,75,.06);img(s,'vegetables',532,260,144,.02)}
 if(name==='gout_table'||name==='kidney_table'){const u=1-ease(t,.6,2.3);s.group({x:612+204*u,y:247-22*u},()=>img(s,'vegetables',0,0,144,-.07))}
 if(name==='kidney_potassium'){page(s,1045,304,144,'化验与饮食',.04,t-2);bottle(s,852,318,80,t,'低钠盐','含钾')}
 if(name==='table_stays')medicine(s,1094,441,61);
};
const drinks:Draw=({stage:s,t},r,name)=>{env(s,'kitchen');img(s,'plate',429,377,220,-.02);img(s,'fruit',261,336,83,-.07);
 const u=ease(t,.8,3.4);if(name==='alcohol_stow'){bottle(s,603+480*u,294+49*u,120,t,'酒','酒精',false);cup(s,862,348,118,false)}
 else if(name==='water_replace'){bottle(s,586+428*u,306,113,t,'甜饮','糖',false);cup(s,874-169*u,345,117,true)}
 else if(name==='gout_water'){cup(s,659,331,141,true);page(s,940,299,172,'个人饮水安排',.06,t-2)}
 else{bottle(s,636,299,136,t,'饮品','糖与份量',true);bottle(s,955,318,93,t-1.4,'酒','酒精',false);cup(s,817,373,89,true)}
};
const bottles:Draw=({stage:s,t},r,name)=>{env(s,'kitchen');organ(s,r.topic,356,265,r.topic==='pcos'?294:r.topic==='ckd'?226:280);
 const u=ease(t,3.1,4.8);bottle(s,701+195*u,314,129,t,name==='iodine_check'||name==='iodine_balance'?'碘补充':'补充剂','成分与用量',true);
 img(s,'plate',1020,362,187,.035);img(s,'vegetables',1012,357,85,-.02);page(s,666,454,119,'先核对',-.03,t-3);
};
const living:Draw=({stage:s,t},r,name)=>{
 env(s,r.topic==='graves'||r.topic==='pcos'?stageIds[r.topic]:'home');const moving=name==='gout_activity'||name==='pcos_movement'||name==='kidney_move';
 img(s,moving?'walking':'body',r.axis==='right'?851:431,281,moving?272:268,-.01);

 if(moving){img(s,'shoes',r.axis==='right'?568:764,451,149,-.04);calendar(s,r.axis==='right'?359:995,284,186,'循序渐进',.04)}
 else if(name==='fast_day'){clock(s,789,237,146,8,Math.min(35,t*5));page(s,997,357,161,'变化记录',.04,t-2)}
 else if(name.includes('skin')||name==='pcos_mirror'){
  s.group({x:r.axis==='right'?411:810,y:286},()=>{cutout(s,{x:0,y:0},tornEllipse(101,141,319),'#ab9672',320,3);cutout(s,{x:0,y:0},tornEllipse(91,130,321),'#b5c8c399',322,1)});page(s,1020,408,137,'症状记录',.04,t);
 }else{page(s,r.axis==='right'?448:870,300,227,name.includes('kidney')?'家庭记录':'生活与症状',.04,t);clock(s,r.axis==='right'?638:1011,451,91,8,0);cup(s,r.axis==='right'?303:678,433,82,true)}
 if(name==='kidney_family'||name==='fatigue_support'||name==='pcos_support')img(s,'male_patient',1100,284,188,.01);
};
const pregnancy:Draw=({stage:s,t},r,name)=>{env(s,'home');calendar(s,470,285,259,'个人计划',-.04);page(s,825,288,236,r.topic==='pcos'?'生育评估':'甲功与用药',.06,t);medicine(s,1037,411,75,.04);clock(s,291,427,92,8,0);
 if(name==='pregnancy_radio'){paperEnvelope(s,{x:989,y:226},172,()=>{});page(s,982,212,115,'既往资料',.05,t)}
};
const eyes:Draw=({stage:s,t},r,name)=>{env(s,'home');img(s,'eye',499,280,400,-.015);page(s,949,298,217,'眼科评估',.055,t);if(name==='eye_smoke'){const u=ease(t,1.1,3.1);tobaccoPacket(s,687,428,66,t)}};
const archive:Draw=({stage:s,t},r,name)=>{env(s,'home');const u=ease(t,1.2,3.6);page(s,514-85*u,312+56*u,243,r.labels[0],-.08,t);fileReceive(s,736,365,348,t,r.labels[1],'');organ(s,r.topic,1016,243,r.topic==='pcos'?228:191);};
const dialysis:Draw=({stage:s,t},r,name)=>{hospitalSpace(s,'ckd');organ(s,'ckd',370,274,248);archiveFolder(s,731,317,399,t,'当前管理','复查计划');calendar(s,1068,325,167,'后续安排',.04)};
const renderers:Record<string,Draw>={night,anatomy,flare,compare,report,timeline,plan,call,bag,table:tabletop,drink:drinks,bottle:bottles,life:living,pregnancy,eye:eyes,archive,dialysis};
export function makeShot(id:string,name:string,topic:string):Shot{
 const r=(directions as unknown as Record<string,Recipe>)[name];if(!r||!renderers[r.kind])throw Error('本集尚未实现镜头 '+name);
 return {id,camera:({t})=>{
  if(r.camera==='close')return {x:r.axis==='right'?681:603,y:306,zoom:1+ease(t,.6,3.5)*.055};
  if(r.camera==='follow')return {x:640+ease(t,1,4)*12,y:309,zoom:1};
  if(r.camera==='pullback')return {x:640,y:306,zoom:1.055-ease(t,.7,5.1)*.055};
  return {x:640,y:306,zoom:1};
 },render:c=>renderers[r.kind](c,r,name)};
}
