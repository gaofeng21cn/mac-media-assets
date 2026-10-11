#!/usr/bin/env python3
"""Original episode score; choreography drives musical breathing, not the reverse."""
import argparse,hashlib,json,math,subprocess
from pathlib import Path
import mido

def perform(project,soundfont):
 score=json.loads((project/'score.json').read_text());cfg=json.loads((project/'project.json').read_text());duration=score['duration']
 series=cfg['series_id'];tonic={'gout_paper_theatre':50,'graves_paper_theatre':53,'hashimoto_paper_theatre':55,'breast_nodules_paper_theatre':48,'pcos_paper_theatre':57,'ckd_paper_theatre':51}.get(series,50)
 bpm={'gout_paper_theatre':68,'graves_paper_theatre':66,'hashimoto_paper_theatre':70,'breast_nodules_paper_theatre':64,'pcos_paper_theatre':74,'ckd_paper_theatre':67}.get(series,72)
 beat=60/bpm;bar=3*beat;tempo=mido.bpm2tempo(bpm);tracks={k:[] for k in ('bed','pulse','motif')};root=project/'audio/music';root.mkdir(parents=True,exist_ok=True)
 def note(stem,t,pitch,length,velocity):
  if 0<=t<duration-.8:tracks[stem].append({'time':round(t,4),'pitch':pitch,'duration':round(min(length,duration-.8-t),4),'velocity':velocity})
 def is_quiet(t):return any(s['start']<=t<s['end'] and (s.get('music_role')=='thin' or s['id'] in ('coordinate','urgent','danger','call','swallow','medication')) for s in score['shots'])
 # Open voicings, slow harmonic rhythm, no high-frequency ostinato under terminology.
 voicings=[[0,7,12,16,19],[5,12,16,19,24],[9,16,19,24,28],[7,14,18,21,26],[0,7,12,16,21],[5,12,16,19,24]]
 for i in range(math.ceil((duration-3)/bar)):
  at=.35+i*bar;chord=[tonic+v for v in voicings[i%len(voicings)]];quiet=is_quiet(at)
  for j,p in enumerate(chord[1:4]):note('bed',at+j*.04,p,bar*1.05,21 if quiet else 27)
  if not quiet:
   for j,offset in enumerate((0,beat+.025,beat*2-.016)):
    if i%4==3 and j==2:continue
    note('pulse',at+offset,chord[(0,2,4)[j]],beat*.72,(37,30,33)[j])
 # Sparse small phrases follow meaning changes; avoid restarting at every cut.
 for i,s in enumerate(score['shots']):
  if i%2 or is_quiet(s['start']+.5):continue
  at=s['start']+.6
  for j,v in enumerate((24,28,31,26)):note('motif',at+j*.54,tonic+v,.7 if j<3 else 1.1,(33,29,30,25)[j])
 for j,v in enumerate((7,12,16,19)):note('bed',max(0,duration-2.8)+j*.06,tonic+v,2.3,24)
 programs={'bed':48,'pulse':24,'motif':12}; programs.update({'gout_paper_theatre':{'pulse':24,'motif':12},'graves_paper_theatre':{'pulse':11,'motif':73},'hashimoto_paper_theatre':{'pulse':24,'motif':10},'breast_nodules_paper_theatre':{'pulse':24,'motif':11},'pcos_paper_theatre':{'pulse':24,'motif':12},'ckd_paper_theatre':{'pulse':24,'motif':71}}.get(series,{}));receipts=[]
 for name,notes in tracks.items():
  midi=mido.MidiFile(ticks_per_beat=960);tr=mido.MidiTrack();midi.tracks.append(tr);tr.append(mido.MetaMessage('set_tempo',tempo=tempo));tr.append(mido.MetaMessage('time_signature',numerator=3,denominator=4));tr.append(mido.Message('program_change',program=programs[name]));tr.append(mido.Message('control_change',control=10,value={'bed':64,'pulse':54,'motif':74}[name]))
  timed=[]
  for n in notes:
   timed.append((round(mido.second2tick(n['time'],960,tempo)),mido.Message('note_on',note=n['pitch'],velocity=n['velocity'])))
   timed.append((round(mido.second2tick(n['time']+n['duration'],960,tempo)),mido.Message('note_off',note=n['pitch'],velocity=0)))
  prior=0
  for tick,msg in sorted(timed,key=lambda x:(x[0],x[1].type=='note_on')):tr.append(msg.copy(time=tick-prior));prior=tick
  tr.append(mido.MetaMessage('end_of_track',time=max(0,round(mido.second2tick(duration+1,960,tempo))-prior)))
  mid=root/f'{name}.mid';raw=root/f'{name}-sampler.wav';wav=root/f'{name}.wav';midi.save(mid)
  subprocess.run(['fluidsynth','-ni','-r','48000','-g','.60','-C','0','-R','1','-o','synth.reverb.room-size=0.25','-o','synth.reverb.damp=0.4','-o','synth.reverb.level=0.18','-F',str(raw),str(soundfont),str(mid)],check=True,capture_output=True)
  subprocess.run(['ffmpeg','-y','-v','error','-i',str(raw),'-af',f'highpass=f=75,lowpass=f={3500 if name=="bed" else 6000},apad=whole_dur={duration},atrim=end={duration}', '-c:a','pcm_s24le',str(wav)],check=True)
  receipts.append({'id':name,'program':programs[name],'notes':notes,'midi':str(mid.relative_to(project)),'wave':str(wav.relative_to(project))})
 (root/'performance.json').write_text(json.dumps({'title':'把生活接起来','source':'original MIDI, locally performed with FluidSynth','series':series,'tonic':tonic,'tempo':bpm,'duration':duration,'soundfont':str(soundfont),'soundfont_sha256':hashlib.sha256(soundfont.read_bytes()).hexdigest(),'license_ref':'assets/audio/instruments/FluidR3/LICENSE.txt','tracks':receipts,'listening_review':'pending'},ensure_ascii=False,indent=2)+'\n')
 (project/'preproduction/music-plan.json').write_text(json.dumps({'brief':'温暖克制的纸面生活；解释段留出中频空间，用药和急症减薄脉冲，结尾完整收束。','tracks':[{'id':n,'path':f'audio/music/{n}.wav','gain':g,'loop':False} for n,g in [('bed',.40),('pulse',.50),('motif',.30)]],'bus_lufs':-32,'ducking':{'threshold':.025,'ratio':8,'attack_ms':25,'release_ms':300},'full_listening':'pending'},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--soundfont',type=Path,required=True);a=p.parse_args();perform(a.project.resolve(),a.soundfont.resolve())
