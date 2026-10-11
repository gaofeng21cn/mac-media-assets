import {mount} from './kit/player';
import {paperFolder,clipFastener} from './kit/props';
import {phase,mix} from './kit/motion';
import score from '../score.json';
mount({assets:[],score,shots:[{id:'folder',render:({stage:s,t})=>{
 s.tracking=false;s.paper({x:640,y:360,w:1170,h:630,color:'#d8d9c6',seed:850,lift:0});s.tracking=true;
 paperFolder(s,{x:640,y:350,rotation:-.015},450,phase(t,.5,2),()=>{
  const q=phase(t,2.1,3.4);
  for(const side of [-1,1])s.group({x:mix(side*390,side*107,q),y:mix(-70,0,q),rotation:side*.045},()=>{
   s.paper({x:0,y:0,w:152,h:204,color:'#f1e7cc',seed:860+side,lift:2,name:'document'});
   s.text(side<0?'记录':'计划',0,-60,26,'#345a56');
   for(let i=0;i<3;i++)s.paper({x:-35+i*36,y:30,w:16,h:30+i*16,color:['#b08462','#809b91','#c0aa69'][i],seed:880+i,lift:.2});
  });
  clipFastener(s,-141,mix(-210,-92,phase(t,3.6,4.1)),-.07);
 });
 s.text('打开 · 收入 · 夹住',640,617,26,'#345a56');
}}]});
