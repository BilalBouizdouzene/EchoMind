"""Dependency-light browser dashboard for the local FastAPI fallback."""

from __future__ import annotations

from fastapi.responses import HTMLResponse


def dashboard_page() -> HTMLResponse:
    return HTMLResponse(_PAGE)


_PAGE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>EchoMind · Speech Intelligence</title>
  <style>
    :root{--bg:#06111f;--panel:#0b1b2b;--line:#1e4057;--text:#e2edf7;--muted:#8da7bb;--cyan:#67e8f9;--blue:#60a5fa;--violet:#a78bfa;--amber:#fbbf24;--red:#fb7185}
    *{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at 10% 0%,#12324a 0,#06111f 38%,#040b14 100%);color:var(--text);font:14px/1.5 Inter,Segoe UI,Arial,sans-serif;min-height:100vh}
    .shell{max-width:1420px;margin:0 auto;padding:28px}.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}.brand{display:flex;gap:12px;align-items:center}.logo{height:42px;width:42px;border:1px solid #2c7188;border-radius:13px;display:grid;place-items:center;color:var(--cyan);font-weight:800;background:#0b2738;box-shadow:0 0 30px #164e6355}.brand h1{font-size:22px;letter-spacing:-.03em;margin:0}.brand p{margin:2px 0 0;color:var(--muted);font-size:12px}.pill{border:1px solid #216277;color:var(--cyan);background:#0a2434;padding:7px 11px;border-radius:999px;font-size:12px}
    .grid{display:grid;grid-template-columns:350px 1fr;gap:18px}.panel{background:linear-gradient(145deg,#0b1b2bdd,#091725dd);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:0 14px 45px #0004}.panel h2{font-size:13px;text-transform:uppercase;letter-spacing:.13em;color:#b9d9e7;margin:0 0 14px}.field{margin:12px 0}.field label{display:block;color:var(--muted);font-size:12px;margin-bottom:6px}.field input,.field select,.field textarea{width:100%;background:#071421;border:1px solid #23465d;color:var(--text);border-radius:10px;padding:10px 11px;outline:none}.field textarea{resize:vertical;min-height:74px}.checks label{display:flex;gap:8px;align-items:center;margin:9px 0;color:#c9d9e5}.checks input{accent-color:var(--cyan)}button{border:0;border-radius:11px;padding:12px 16px;background:linear-gradient(100deg,#0891b2,#2563eb);color:white;font-weight:700;cursor:pointer;width:100%;margin-top:10px;box-shadow:0 10px 25px #0891b244}button:disabled{opacity:.55;cursor:wait}.hint{font-size:11px;color:var(--muted);margin-top:10px}.drop{border:1px dashed #2c647b;border-radius:12px;padding:12px;background:#071421;color:var(--muted);width:100%}.record-controls{display:grid;grid-template-columns:1fr 1fr auto;gap:8px;align-items:center}.record-controls button{margin:0;padding:10px 9px;font-size:12px}.record-controls #stopRecord{background:#7f1d35;box-shadow:none}.record-clock{font:12px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--cyan);min-width:44px;text-align:right}.record-state{min-height:18px;color:var(--muted);font-size:11px;margin-top:6px}
    .hero{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;margin-bottom:18px}.hero h2{font-size:28px;letter-spacing:-.04em;margin:0}.hero p{color:var(--muted);margin:6px 0 0;max-width:720px}.hero .status{color:#86efac;font-size:12px;border:1px solid #166534;background:#052e1a;padding:8px 10px;border-radius:999px;white-space:normal;max-width:420px;overflow-wrap:anywhere;text-align:center}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.metric-card{border:1px solid var(--line);border-radius:13px;padding:12px;background:#0a1928}.metric-card span{display:block;color:var(--muted);font-size:10px;letter-spacing:.12em}.metric-card strong{display:block;margin-top:5px;font-size:18px}.metric-card.cyan strong{color:var(--cyan)}.metric-card.blue strong{color:var(--blue)}.metric-card.violet strong{color:var(--violet)}.metric-card.amber strong{color:var(--amber)}
    .twocol{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}.text-box{border:1px solid var(--line);border-radius:13px;padding:14px;background:#081622;min-height:125px}.text-box h3{margin:0 0 9px;font-size:10px;letter-spacing:.12em;color:var(--muted);text-transform:uppercase}.text-box p{margin:0;font-size:16px;line-height:1.55}.text-box.final{border-color:#1c687c;background:#092333}.text-box.final p{color:#d9fbff}.subpanel{margin-top:14px}.timeline-wrap{padding:12px 0 2px}.timeline-axis{display:flex;justify-content:space-between;color:var(--muted);font-size:11px}.timeline{position:relative;height:22px;margin:8px 0;border-radius:999px;background:#132536;overflow:hidden;border:1px solid #24455b}.timeline-bar{position:absolute;top:3px;height:14px;border-radius:99px;min-width:7px}.legend{display:flex;gap:16px;color:var(--muted);font-size:11px}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}.dot.cyan{background:var(--cyan)}.dot.amber{background:var(--amber)}.dot.red{background:var(--red)}.json{white-space:pre-wrap;max-height:270px;overflow:auto;background:#050d16;border:1px solid #1a3448;border-radius:12px;padding:13px;color:#bdebf5;font:12px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace}.tabs{display:flex;gap:8px;margin-top:18px}.tab{background:#091a29;border:1px solid var(--line);padding:8px 12px;border-radius:9px;color:var(--muted);cursor:pointer}.tab.active{color:var(--cyan);border-color:#27768b}.hidden{display:none}.empty-state{padding:20px;color:var(--muted);border:1px dashed var(--line);border-radius:12px}.footer{color:#668197;text-align:center;font-size:11px;padding:20px}
    @media(max-width:900px){.grid{grid-template-columns:1fr}.metric-grid{grid-template-columns:repeat(2,1fr)}.twocol{grid-template-columns:1fr}.hero{display:block}.hero .status{display:inline-block;margin-top:12px}}
    :root{--bg:#080b18;--panel:#111629;--line:#303450;--text:#f3f4ff;--muted:#a1a6c2;--cyan:#75f0ef;--blue:#8aa7ff;--violet:#c19aff;--amber:#ffd37b;--red:#ff829b}
    body{background:radial-gradient(ellipse at 82% 4%,#342258 0,transparent 30%),radial-gradient(ellipse at 0 24%,#123c55 0,transparent 34%),#080b18;letter-spacing:.005em}
    .shell{max-width:1480px;padding:30px 32px}
    .topbar{position:relative;isolation:isolate;min-height:136px;margin-bottom:24px;padding:20px 24px;border:1px solid #3a4164;border-radius:24px;background:linear-gradient(112deg,#11182bea 0%,#15152be8 58%,#211b39e8 100%);box-shadow:0 22px 60px #02040e77;overflow:hidden}
    .topbar:before{content:"";position:absolute;inset:0;z-index:-1;background:repeating-linear-gradient(112deg,transparent 0 62px,#b9c7ff08 63px 64px);mask-image:linear-gradient(90deg,#000,transparent 78%)}
    .brand{gap:15px;z-index:1}.logo{width:50px;height:50px;border-radius:16px;border-color:#5ee3ec88;color:#dfffff;font-size:20px;background:linear-gradient(145deg,#1c6276,#25234c);box-shadow:0 0 32px #56e7e84a}
    .brand h1{font-size:25px;letter-spacing:-.045em}.brand p{margin-top:5px;color:#b5bdd6;font-size:12px;letter-spacing:.015em}
    .pill{z-index:2;border-color:#52e4d755;color:#a5fff5;background:#0f292eaa;box-shadow:inset 0 0 18px #55e4d710;letter-spacing:.09em}
    .mascot{position:absolute;right:118px;bottom:-24px;width:154px;height:156px;object-fit:contain;object-position:center bottom;filter:drop-shadow(0 0 22px #7661ff45);pointer-events:none}
    .grid{grid-template-columns:355px minmax(0,1fr);gap:20px}
    .panel{border-color:#343953;border-radius:20px;background:linear-gradient(145deg,#151a2eeF,#101426ed);box-shadow:0 18px 48px #03040c66}
    .panel h2{color:#d5d9ef;letter-spacing:.15em}
    .field label{color:#b3b8d0}.field input,.field select,.field textarea,.drop{border-color:#383d5a;border-radius:12px;background:#0b1020;color:#f3f4ff;transition:border-color .18s,box-shadow .18s}
    .field input:focus,.field select:focus,.field textarea:focus{border-color:#78e9eb;box-shadow:0 0 0 3px #78e9eb1b}
    .checks label{color:#d1d4e6}.checks input{accent-color:#8b8dff}
    button{border-radius:12px;background:linear-gradient(105deg,#21b8c3,#7367e8 68%,#a363ce);box-shadow:0 10px 26px #5456c844;transition:transform .18s,filter .18s,box-shadow .18s}
    button:not(:disabled):hover{transform:translateY(-1px);filter:brightness(1.1);box-shadow:0 13px 30px #6659e255}
    button:focus-visible,.tab:focus-visible{outline:2px solid #92fbf3;outline-offset:3px}
    .record-controls #stopRecord{background:linear-gradient(110deg,#8e3154,#632743);box-shadow:none}
    .hint,.record-state{color:#a0a6c2}.record-clock{color:#91fff3}
    .hero{align-items:center;padding:4px 2px 16px}.hero h2{font-size:clamp(25px,3vw,34px);letter-spacing:-.055em}.hero p{color:#b1b6cf;max-width:650px}
    .hero .status{border-color:#58e5d944;background:#102a2b;color:#a3fff1;box-shadow:0 0 22px #55e4d40c}
    .metric-grid{gap:12px}.metric-card,.text-box{border-color:#343953;border-radius:15px;background:#0c1121}.metric-card{padding:14px}.metric-card span{color:#a6acc7}.metric-card strong{font-size:20px}.metric-card.cyan strong{color:#85fff2}.metric-card.blue strong{color:#9bb5ff}.metric-card.violet strong{color:#d0a7ff}.metric-card.amber strong{color:#ffd886}
    .text-box{padding:16px}.text-box h3{color:#a8aec8}.text-box.final{border-color:#6558a0;background:linear-gradient(145deg,#17182e,#121a2a)}.text-box.final p{color:#e9e5ff}
    .timeline{border-color:#383d5a;background:#161b30}.timeline-bar{box-shadow:0 0 14px currentColor}
    .json{border-color:#343953;border-radius:14px;background:#090d19;color:#c9f7f5}
    .tab{border-color:#343953;border-radius:11px;background:#111629;color:#b5bad1}.tab.active{color:#a3fff4;border-color:#60ded7;background:#13252c}
    .empty-state{border-color:#424663;color:#aeb4cc;background:#0c1121}.footer{color:#8e94af}
    @media(max-width:900px){.shell{padding:18px}.grid{grid-template-columns:1fr}.topbar{min-height:116px;padding:18px}.mascot{right:85px;width:130px;height:138px}.pill{font-size:10px}.metric-grid{grid-template-columns:repeat(2,1fr)}}
    @media(max-width:560px){.shell{padding:12px}.topbar{min-height:104px;padding:15px}.brand{gap:10px}.brand h1{font-size:20px}.brand p{max-width:200px;font-size:10px}.logo{width:42px;height:42px}.mascot{display:none}.pill{padding:6px 8px;font-size:9px}.metric-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.record-controls{grid-template-columns:1fr 1fr}.record-clock{grid-column:1/-1;text-align:left}}
    @media(prefers-reduced-motion:reduce){*,*:before,*:after{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar"><div class="brand"><div class="logo" aria-hidden="true">E</div><div><h1>EchoMind</h1><p>Local multilingual speech analysis · selective re-decoding is experimental</p></div></div><img class="mascot" src="/static/echomind-anime-engineer.png" alt="" aria-hidden="true"/><div class="pill">LOCAL · NO TELEMETRY</div></header>
    <div class="grid">
      <aside class="panel">
        <h2>Analysis control</h2>
        <div class="field"><label>Execution mode</label><select id="mode"><option value="demo">Demo / model-free</option><option value="asr">Local ASR</option></select></div>
        <div class="field"><label>Demo scenario</label><select id="scenario"><option value="selective_correction">Selective correction</option><option value="self_correction">Self-correction + clarification</option><option value="multilingual">French · English · Arabic</option></select></div>
        <div class="field"><label>Record from microphone</label><div class="record-controls"><button id="record" type="button">Start recording</button><button id="stopRecord" type="button" disabled>Stop</button><span class="record-clock" id="recordClock">00:00</span></div><div class="record-state" id="recordState" aria-live="polite">Up to 5 minutes · microphone access is requested by your browser on localhost or HTTPS.</div></div>
        <div class="field"><label>Or choose an audio file</label><input class="drop" id="audio" type="file" accept=".wav,.flac,.ogg,.mp3,audio/*" /><audio id="player" controls style="width:100%;margin-top:10px;display:none"></audio></div>
        <div class="field"><label>ASR model</label><select id="model"><option>tiny</option><option>base</option><option>small</option></select></div>
        <div class="field"><label>Language hint</label><select id="language"><option value="auto">Automatic</option><option value="en">English</option><option value="fr">French</option><option value="ar">Arabic</option></select></div>
        <div class="field"><label>Verified context / vocabulary</label><textarea id="context" placeholder="Optional words or context used only to compare grounded candidates"></textarea></div>
        <div class="checks"><label><input id="uncertainty" type="checkbox" checked /> Uncertainty analysis</label><label><input id="correction" type="checkbox" checked /> Selective correction</label><label><input id="nlp" type="checkbox" checked /> Contextual NLP</label></div>
        <button id="run">Run local analysis</button><button id="download" disabled>Download JSON report</button><div class="hint">Recording and file analysis use Local ASR and require installed faster-whisper weights. Demo mode uses simulated hypotheses and is not a speech benchmark.</div>
      </aside>
      <section>
        <div class="hero"><div><h2>Reasoning console</h2><p>See what the system heard, which regions it trusted, why it spent extra compute, and whether it needs clarification.</p></div><div class="status" id="status">Ready</div></div>
        <div class="panel" id="metrics"><div class="empty-state">Run an analysis to populate measured pipeline metrics.</div></div>
        <div class="twocol"><div class="text-box"><h3>Baseline ASR</h3><p id="original">Waiting for an analysis.</p></div><div class="text-box final"><h3>Final grounded result</h3><p id="final">Waiting for an analysis.</p></div></div>
        <div class="panel subpanel"><h2>Uncertainty timeline</h2><div id="timeline"><div class="empty-state">Segment-level evidence will appear here.</div></div></div>
        <div class="tabs"><div class="tab active" data-tab="semantic">Semantic intelligence</div><div class="tab" data-tab="provenance">Correction provenance</div><div class="tab" data-tab="raw">Full JSON</div></div>
        <div class="panel subpanel" id="semantic"><div class="json">Run an analysis to see intent, entities, language transitions, and self-correction.</div></div>
        <div class="panel subpanel hidden" id="provenance"><div class="json">No correction provenance yet.</div></div>
        <div class="panel subpanel hidden" id="raw"><div class="json">No structured result yet.</div></div>
      </section>
    </div>
    <div class="footer">EchoMind · CPU-first research prototype · recordings remain on this machine</div>
  </main>
  <script>
    const $ = id => document.getElementById(id); let fileData = null; let lastReport = null;
    let mediaRecorder = null; let recordingStream = null; let recordingChunks = []; let recordingTimer = null; let recordingStartedAt = 0; let previewUrl = null;
    const MAX_RECORDING_MS = 5 * 60 * 1000;
    function readAsDataUrl(blob) { return new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload=()=>resolve(reader.result); reader.onerror=()=>reject(new Error('Could not read the audio recording')); reader.readAsDataURL(blob); }); }
    async function selectAudio(blob, name) { if (previewUrl) URL.revokeObjectURL(previewUrl); previewUrl=URL.createObjectURL(blob); $('player').src=previewUrl; $('player').style.display='block'; fileData={name, data:await readAsDataUrl(blob)}; }
    $('audio').addEventListener('change', async event => { const file = event.target.files[0]; if (!file) { fileData = null; $('player').style.display='none'; return; } try { await selectAudio(file, file.name); $('mode').value='asr'; $('recordState').textContent='Audio file ready for Local ASR.'; } catch(error) { $('recordState').textContent=error.message; } });
    function stopRecordingTracks() { if (recordingStream) { recordingStream.getTracks().forEach(track => track.stop()); recordingStream=null; } }
    function toMonoWav(audioBuffer, targetRate=16000) {
      const frameCount=Math.ceil(audioBuffer.duration*targetRate); const bytesPerSample=2; const buffer=new ArrayBuffer(44+frameCount*bytesPerSample); const view=new DataView(buffer); const channels=Array.from({length:audioBuffer.numberOfChannels},(_,i)=>audioBuffer.getChannelData(i));
      const writeText=(offset,value)=>{ for(let i=0;i<value.length;i++) view.setUint8(offset+i,value.charCodeAt(i)); };
      writeText(0,'RIFF'); view.setUint32(4,36+frameCount*bytesPerSample,true); writeText(8,'WAVE'); writeText(12,'fmt '); view.setUint32(16,16,true); view.setUint16(20,1,true); view.setUint16(22,1,true); view.setUint32(24,targetRate,true); view.setUint32(28,targetRate*bytesPerSample,true); view.setUint16(32,bytesPerSample,true); view.setUint16(34,16,true); writeText(36,'data'); view.setUint32(40,frameCount*bytesPerSample,true);
      const ratio=audioBuffer.sampleRate/targetRate;
      for(let i=0;i<frameCount;i++){ const position=i*ratio; const left=Math.floor(position); const fraction=position-left; let sample=0; for(const channel of channels){ const a=channel[Math.min(left,channel.length-1)]||0; const b=channel[Math.min(left+1,channel.length-1)]||0; sample+=(a+(b-a)*fraction)/channels.length; } const clipped=Math.max(-1,Math.min(1,sample)); view.setInt16(44+i*bytesPerSample,clipped<0?clipped*0x8000:clipped*0x7fff,true); }
      return new Blob([buffer],{type:'audio/wav'});
    }
    function updateRecordClock() { const seconds=Math.floor((Date.now()-recordingStartedAt)/1000); $('recordClock').textContent=String(Math.floor(seconds/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0'); if(Date.now()-recordingStartedAt>=MAX_RECORDING_MS) stopMicrophoneRecording(); }
    function stopMicrophoneRecording() { if(mediaRecorder && mediaRecorder.state!=='inactive') mediaRecorder.stop(); }
    $('record').addEventListener('click', async () => {
      if(!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder){ $('recordState').textContent='Microphone recording is not supported in this browser. Try an up-to-date browser.'; return; }
      $('record').disabled=true; $('audio').disabled=true; $('mode').value='asr'; $('recordState').textContent='Requesting microphone access…';
      try {
        recordingStream=await navigator.mediaDevices.getUserMedia({audio:true}); recordingChunks=[];
        const mimeType=['audio/webm;codecs=opus','audio/ogg;codecs=opus','audio/webm','audio/ogg'].find(type=>MediaRecorder.isTypeSupported(type));
        mediaRecorder=new MediaRecorder(recordingStream,mimeType?{mimeType}:undefined);
        mediaRecorder.ondataavailable=event=>{ if(event.data.size) recordingChunks.push(event.data); };
        mediaRecorder.onerror=()=>{ stopRecordingTracks(); clearInterval(recordingTimer); $('record').disabled=false; $('audio').disabled=false; $('stopRecord').disabled=true; $('recordState').textContent='Recording failed. Check browser microphone permissions and try again.'; };
        mediaRecorder.onstop=async()=>{
          stopRecordingTracks(); clearInterval(recordingTimer); $('stopRecord').disabled=true; $('recordState').textContent='Converting recording to local WAV…';
          try {
            const recorded=new Blob(recordingChunks,{type:mediaRecorder.mimeType||recordingChunks[0]?.type||'audio/webm'}); const AudioContextClass=window.AudioContext||window.webkitAudioContext; const audioContext=new AudioContextClass();
            try { const decoded=await audioContext.decodeAudioData(await recorded.arrayBuffer()); const wav=toMonoWav(decoded); if(wav.size>16*1024*1024) throw new Error('Recording exceeds the 16 MB upload limit. Record a shorter clip.'); const name='echomind-recording-'+new Date().toISOString().replace(/[:.]/g,'-')+'.wav'; await selectAudio(wav,name); $('audio').value=''; $('mode').value='asr'; $('recordState').textContent='Recording ready ('+Math.round(decoded.duration)+' s, WAV 16 kHz mono). Click “Run local analysis” to use the real ASR pipeline.'; $('status').textContent='Recording ready for Local ASR'; }
            finally { await audioContext.close(); }
          } catch(error) { $('recordState').textContent='Could not prepare recording: '+error.message; }
          finally { $('record').disabled=false; $('audio').disabled=false; mediaRecorder=null; recordingChunks=[]; }
        };
        mediaRecorder.start(); recordingStartedAt=Date.now(); $('recordClock').textContent='00:00'; $('recordState').textContent='Recording… Maximum duration: 5 minutes.'; $('mode').value='asr'; $('audio').value=''; fileData=null; $('player').style.display='none'; $('stopRecord').disabled=false; $('record').disabled=true; recordingTimer=setInterval(updateRecordClock,250);
      } catch(error) { stopRecordingTracks(); $('record').disabled=false; $('audio').disabled=false; $('recordState').textContent='Microphone unavailable: '+error.message; }
    });
    $('stopRecord').addEventListener('click', stopMicrophoneRecording);
    window.addEventListener('beforeunload', () => { stopRecordingTracks(); if(previewUrl) URL.revokeObjectURL(previewUrl); });
    document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => { document.querySelectorAll('.tab').forEach(t => t.classList.remove('active')); document.querySelectorAll('.subpanel').forEach(p => p.classList.add('hidden')); tab.classList.add('active'); $(tab.dataset.tab).classList.remove('hidden'); }));
    function setJson(id, value) { $(id).querySelector('.json').textContent = JSON.stringify(value, null, 2); }
    $('run').addEventListener('click', async () => {
      const demo = $('mode').value === 'demo'; if (mediaRecorder) { $('status').textContent = mediaRecorder.state==='recording' ? 'Stop the recording before analysis' : 'Preparing the recording…'; return; } if (!demo && !fileData) { $('status').textContent = 'Audio required'; return; }
      $('run').disabled = true; $('download').disabled = true; lastReport = null; $('status').textContent = 'Processing locally…'; $('metrics').innerHTML='<div class="empty-state">Analysis is running locally…</div>'; $('original').textContent='Waiting for transcription…'; $('final').textContent='Waiting for transcription…'; $('timeline').innerHTML='<div class="empty-state">Waiting for ASR segments…</div>'; setJson('semantic', {}); setJson('provenance', []); setJson('raw', {});
      const body = {demo_mode:demo, scenario:$('scenario').value, audio_base64:fileData ? fileData.data : null, audio_filename:fileData ? fileData.name : null, model_name:$('model').value, language_hint:$('language').value === 'auto' ? null : $('language').value, context:$('context').value, enable_uncertainty:$('uncertainty').checked, enable_selective_correction:$('correction').checked, enable_contextual_nlp:$('nlp').checked};
      try {
        const response = await fetch('/dashboard/analyze', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)}); const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'analysis failed');
        lastReport = data; $('download').disabled = false; $('metrics').innerHTML = data.metrics_html; $('original').textContent = data.original_transcript || '(empty)'; $('final').textContent = data.final_transcript || '(empty)'; $('timeline').innerHTML = data.timeline_html; setJson('semantic', data.semantic_interpretation); setJson('provenance', data.corrections); setJson('raw', data);
        $('status').textContent = !data.original_transcript ? 'No speech detected — check the recording' : data.decision === 'CLARIFY' ? 'Clarification required' : 'Analysis complete';
      } catch(error) {
        $('status').textContent = 'Analysis failed'; const errorBox=document.createElement('div'); errorBox.className='empty-state'; errorBox.textContent=error.message; $('metrics').replaceChildren(errorBox); $('original').textContent='ASR did not complete.'; $('final').textContent='No final transcript available.'; $('timeline').innerHTML='<div class="empty-state">No ASR segments were produced.</div>'; setJson('raw', {error:error.message});
      } finally { $('run').disabled = false; }
    });
    $('download').addEventListener('click', () => { if (!lastReport) return; const blob = new Blob([JSON.stringify(lastReport, null, 2)], {type:'application/json'}); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = 'echomind-analysis.json'; link.click(); URL.revokeObjectURL(url); });
  </script>
</body>
</html>"""
