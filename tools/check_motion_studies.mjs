// Check the actual registered recipes, not creative acceptance.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {pathToFileURL} from 'node:url';
const root=resolve(process.argv[2]||'.');
const rows=(await readFile(resolve(root,'catalog/assets.jsonl'),'utf8')).trim().split('\n').map(JSON.parse);
const ids=['mac_walk_cycle_v1','mac_sit_stand_cycle_v1','mac_care_assistance_v1','mac_cooking_action_v1'];
for(const id of ids){
  const matches=rows.filter(r=>r.source_id===id);
  assert.equal(matches.length,1,`${id}: one admitted recipe`);
  const record=JSON.parse(await readFile(resolve(root,matches[0].portable_record),'utf8'));
  const folder=dirname(resolve(root,matches[0].payload.find(f=>f.path.endsWith('/sequence.json')).path));
  const r=JSON.parse(await readFile(resolve(folder,'sequence.json'),'utf8'));
  const {frameAt,walkProgress,cookingState,cookingLayout}=await import(pathToFileURL(resolve(folder,'runtime.mjs')));
  assert.equal(record.review.current_shot,'pending');
  if(r.type==='walk'){
    const {start,end,period,frames}=r.loop,step=period/frames.length;
    for(let i=0;i<16;i++)assert.equal(frameAt(r,start+i*step+.001),frames[i%frames.length]);
    assert.equal(frameAt(r,end),r.finish_frame);
    assert.equal(frameAt(r,r.duration+10),r.finish_frame);
    assert.equal(walkProgress(r,start+.02),walkProgress(r,start+step-.02),'held feet cannot slide');
    assert.equal(walkProgress(r,end),1);
    assert.ok(r.frames.slice(0,8).every(f=>f.origin&&f.rect&&f.reference_height>0));
  }else if(r.type==='cooking'){
    for(const [i,event] of r.events.filter(e=>e.kind==='cut').entries()){
      assert.equal(cookingState(r,event.time-.0001).made,i,'no slice before blade contact');
      assert.equal(cookingState(r,event.time).made,i+1);
    }
    for(let t=2.5;t<=r.duration;t+=.05)
      assert.deepEqual(cookingLayout(r,t).slices.map(x=>x.id),['slice_1','slice_2','slice_3'],'no lost/duplicated food');
    for(const t of [r.transfer.end,r.stir.start,r.stir.end,r.serve.start,r.serve.end]){
      const before=cookingLayout(r,t-.00001),after=cookingLayout(r,t+.00001);
      for(let i=0;i<3;i++)assert.ok(Math.hypot(before.slices[i].x-after.slices[i].x,before.slices[i].y-after.slices[i].y)<.02,'continuous food trajectory');
      assert.ok(Math.hypot(before.paddle.x-after.paddle.x,before.paddle.y-after.paddle.y)<.02,'continuous paddle trajectory');
    }
    assert.equal(cookingState(r,r.duration).result,'served');
  }else{
    for(const key of r.keys)assert.equal(frameAt(r,key.time),key.frame);
    assert.equal(frameAt(r,r.duration+1),r.keys.at(-1).frame,'finish never wraps to sitting/support');
    assert.equal(frameAt(r,-1),r.keys[0].frame);
  }
  process.stdout.write(`${id}: passed\n`);
}
