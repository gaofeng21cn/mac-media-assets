// Complete character/furniture units share one body ruler and one scene transform.
export function frameAt(r,t){
 let frame=0;
 for(const key of r.keys){if(t<key.time)break;frame=key.frame}
 return frame;
}
export function placement(r,t){
 const index=frameAt(r,Math.max(0,Math.min(r.duration,t))),f=r.frames[index];
 const scale=r.scene_pixels_per_cm/r.body_calibration.source_pixels_per_cm;
 return {index,scale,x:r.x,y:r.ground,world_anchor:[r.x,r.ground],
  body_head_y:r.ground+(f.content_bounds[1]-f.origin[1])*scale};
}
export function renderStudy(ctx,images,r,t){
 const p=placement(r,t),f=r.frames[p.index],b=f.rect;
 ctx.save();ctx.translate(p.x,p.y);ctx.scale(p.scale,p.scale);
 ctx.drawImage(images.sheet,b[0],b[1],b[2],b[3],-f.origin[0],-f.origin[1],b[2],b[3]);ctx.restore();
 return {study:r.id,time:t,frame:p.index,phase:r.phase_names[p.index],scale:p.scale,
  furniture_anchor:p.world_anchor,paper_state:r.paper_states[p.index],
  events:r.events.filter(e=>e.time<=t).map(e=>e.name)};
}
