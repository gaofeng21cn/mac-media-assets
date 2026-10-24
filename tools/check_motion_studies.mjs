// Check the actual registered recipes, not creative acceptance.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
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
// New contact units retain manually reviewed points bound to the exact sheet.
// This guards identity/coordinates; the review record owns visible contact quality.
for(const row of rows.filter(r=>r.kind==='motion_recipe'&&!['superseded','needs_rebuild'].includes(r.curation?.status))){
  const entry=row.payload.find(p=>p.path.endsWith('/'+row.source_id+'/'+row.revision+'/sequence.json'));
  if(!entry)continue;
  const folder=dirname(resolve(root,entry.path));
  const r=JSON.parse(await readFile(resolve(folder,'sequence.json'),'utf8'));
  if(!['role_contact_unit','bed_contact_unit'].includes(r.type))continue;
  const registration=JSON.parse(await readFile(resolve(folder,'registration.json'),'utf8'));
  const source=await readFile(resolve(folder,r.images.sheet.path));
  const sourceSha=createHash('sha256').update(source).digest('hex');
  assert.equal(sourceSha,r.images.sheet.sha256);
  assert.equal(sourceSha,registration.source_sha256);
  assert.deepEqual(r.frames.map(f=>f.rect),registration.frame_rects);
  assert.deepEqual(r.frames.map(f=>f.origin),registration.anchors);
  assert.equal(r.frames.length,registration.anchors.length);
  const calibration=registration.body_calibration_review;
  assert.ok(calibration.span_basis.startsWith('vertical_y_distance'));
  assert.equal(calibration.design_height_cm,r.body_calibration.design_height_cm);
  assert.deepEqual(calibration.reviewed_points,r.body_calibration.source_body_points);
  const span=Math.abs(calibration.reviewed_points[1][1]-calibration.reviewed_points[0][1]);
  assert.equal(span,calibration.span_pixels);
  assert.equal(r.body_calibration.source_pixels_per_cm,span/calibration.design_height_cm);
  const {placement,frameAt}=await import(pathToFileURL(resolve(folder,'runtime.mjs')));
  const scale=r.scene_pixels_per_cm/r.body_calibration.source_pixels_per_cm;
  for(let frame=0;frame<=Math.ceil(r.duration*r.fps);frame++){
    const time=frame/r.fps,p=placement(r,time);
    assert.equal(p.scale,scale,'seated/lying must not be independently resized');
    assert.deepEqual(p.world_anchor,[r.x,r.ground],'furniture must not jump between poses');
  }
  for(const key of r.keys)assert.equal(frameAt(r,key.time),key.frame);
  assert.equal(frameAt(r,r.duration+1),r.keys.at(-1).frame);
  process.stdout.write(`${row.source_id}: reviewed source registration and shared ruler passed\n`);
}
