import assert from 'node:assert/strict';
import {riskCounts,screeningCounts,phase} from '../tools/medical-processes/runtime.mjs';
assert.deepEqual(riskCounts(),{population:100,before:10,after:5,absoluteDifference:5});
assert.throws(()=>riskCounts({population:100,before:101,after:1}));
for(const disease of [0,1,10,99,100])for(const tp of [0,disease])for(const fp of [0,100-disease]){
  const x=screeningCounts({population:100,disease,truePositive:tp,falsePositive:fp});
  assert.equal(x.truePositive+x.falsePositive+x.falseNegative+x.trueNegative,100);
  assert.equal(x.truePositive+x.falseNegative,disease);
}
assert.throws(()=>screeningCounts({population:100,disease:10,truePositive:11,falsePositive:0}));
assert.throws(()=>screeningCounts({population:100,disease:10,truePositive:8,falsePositive:91}));
assert.equal(phase(-1,0,5),0);assert.equal(phase(6,0,5),1);assert.equal(phase(2.5,0,5),.5);
console.log('Medical process numerical boundaries passed');
