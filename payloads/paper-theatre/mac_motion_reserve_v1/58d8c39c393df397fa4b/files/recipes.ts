export type MotionCtx={t:number;duration:number;ease?:(x:number)=>number};
export const clamp=(x:number)=>Math.max(0,Math.min(1,x));
export const smooth=(x:number)=>x*x*(3-2*x);
export const contactShadow=(ctx:MotionCtx,appear=.18,hold=.12)=>{const p=clamp(ctx.t/ctx.duration);const a=p<appear?p/appear:p<appear+hold?1:1-(p-appear-hold)/(1-appear-hold);return{alpha:.22*clamp(a),scale:1+.015*(1-clamp(a))};};
export const hingeReveal=(ctx:MotionCtx,overshoot=.02)=>{const p=smooth(clamp(ctx.t/ctx.duration));return Math.min(1,p*(1+overshoot));};
export const insertPart=(ctx:MotionCtx)=>smooth(clamp(ctx.t/ctx.duration));
export const pageTurn=(ctx:MotionCtx)=>{const p=clamp(ctx.t/ctx.duration);return {angle:(p<.5?p*2:2-p*2)*Math.PI*.5,occlusion:Math.abs(p-.5)*2};};
export const poseCrossfade=(ctx:MotionCtx)=>smooth(clamp(ctx.t/ctx.duration));
export const stageOcclusion=(ctx:MotionCtx)=>smooth(clamp(ctx.t/ctx.duration));
