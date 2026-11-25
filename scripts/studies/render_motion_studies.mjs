// Render the real browser canvas to MP4; no image/model rendering substitute.
import {createHash} from 'node:crypto';
import {readFile,mkdir,writeFile,readdir} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {parseArgs} from 'node:util';
const {values}=parseArgs({options:{playwright:{type:'string'},root:{type:'string'},url:{type:'string'},only:{type:'string'}}});
if(!values.playwright||!values.root||!values.url)throw new Error('Provide --playwright <module> --root <studies> --url <HTTP root>');
const {chromium}=await import(pathToFileURL(resolve(values.playwright)));
const digest=data=>createHash('sha256').update(data).digest('hex');
const browser=await chromium.launch({headless:true});
try{
  const folders=values.only?[values.only]:(await readdir(values.root,{withFileTypes:true})).filter(x=>x.isDirectory()).map(x=>x.name);
  for(const id of folders){
    const folder=resolve(values.root,id),sequence=JSON.parse(await readFile(join(folder,'sequence.json'),'utf8'));
    const samples=join(folder,'samples');await mkdir(join(samples,'keyframes'),{recursive:true});
    const page=await browser.newPage({viewport:{width:1320,height:1000},deviceScaleFactor:1});
    const errors=[];page.on('pageerror',e=>errors.push(String(e)));
    await page.goto(values.url.replace(/\/$/,'')+'/'+id+'/index.html');await page.waitForFunction(()=>window.__ready);
    const canvas=page.locator('canvas');
    const count=Math.ceil(sequence.duration*sequence.fps);
    const ffmpeg=spawn('ffmpeg',['-hide_banner','-loglevel','error','-y','-threads','1','-f','image2pipe','-framerate',String(sequence.fps),
      '-vcodec','png','-i','pipe:0','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',join(samples,'sample.mp4')],{stdio:['pipe','ignore','pipe']});
    let diagnostic='',pipeError;ffmpeg.stderr.on('data',d=>diagnostic+=d);ffmpeg.stdin.on('error',e=>pipeError=e);const done=once(ffmpeg,'close');
    for(let i=0;i<count;i++){
      await page.evaluate(t=>window.__seek(t),i/sequence.fps);
      const frame=Buffer.from(await canvas.evaluate(el=>el.toDataURL('image/png').split(',')[1]),'base64');
      if(pipeError)throw new Error(diagnostic||String(pipeError));
      if(!ffmpeg.stdin.write(frame))await once(ffmpeg.stdin,'drain');
    }
    ffmpeg.stdin.end();const [code]=await done;if(code)throw new Error(diagnostic);
    const states=[],keyframes=[];
    for(let i=0;i<sequence.review_times.length;i++){
      const time=sequence.review_times[i];states.push(await page.evaluate(t=>window.__seek(t),time));
      const relative=`samples/keyframes/${String(i).padStart(2,'0')}.png`;
      await canvas.screenshot({path:join(folder,relative)});keyframes.push(relative);
    }
    // Inspect the exact same source under three backgrounds and at phone width.
    await page.evaluate(()=>window.__seek(2));
    for(const [name,color] of [['light','#f4eedf'],['dark','#263b3a'],['color','#b3d0c5']]){
      await page.evaluate(c=>window.__setBackground(c),color);
      await canvas.screenshot({path:join(samples,`background-${name}.png`)});
    }
    await page.setViewportSize({width:432,height:850});
    await canvas.screenshot({path:join(samples,'phone.png')});
    await page.setViewportSize({width:1320,height:1000});
    // A random seek must return exactly the same canvas bytes.
    await page.evaluate(()=>window.__seek(2));const before=await canvas.screenshot();
    await page.evaluate(d=>{window.__seek(d);window.__seek(0);window.__seek(2)},sequence.duration);
    const after=await canvas.screenshot();if(digest(before)!==digest(after))throw new Error('Non-deterministic seek');
    const inputs={};
    for(const path of ['index.html','runtime.mjs','viewer.mjs','sequence.json',...new Set(Object.values(sequence.images).map(x=>x.path))])
      inputs[path]=digest(await readFile(join(folder,path)));
    await writeFile(join(samples,'technical.json'),JSON.stringify({schema:'mac_motion_render/v1',status:errors.length?'diagnostic':'passed',
      frames:count,fps:sequence.fps,duration:sequence.duration,random_seek_equal:true,browser_errors:errors,inputs,keyframes,states},null,2)+'\n');
    await page.close();process.stdout.write(JSON.stringify({study:id,status:'rendered',frames:count,errors})+'\n');
  }
}finally{await browser.close()}
