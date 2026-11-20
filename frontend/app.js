import {sphere,chart,circuit} from './views.js';
const $=id=>document.getElementById(id),form=$('settings');
const pages={
 overview:['Overview','Quantum teleportation','Compare Alice’s original qubit with Bob’s reconstructed state.','metrics visual jump protocol'],
 simulator:['State simulator','State simulator','Set the input, apply a channel, and inspect the state Bob receives.','controls metrics visual protocol branch details'],
 noise:['Noise laboratory','Noise laboratory','Compare the effect of independent and linked message errors at the same bit-error rate.','controls metrics noiseplot compare visual details'],
 history:['History','Experiment history','Review earlier runs, sweeps, and exports saved on this computer.','history'],
 theory:['Theory','Protocol and model','The physics and assumptions behind this experiment.','notes']
};
const icons=['<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>','<circle cx="12" cy="12" r="9"/><path d="M5 17l12-12m-5 0h5v5"/>','<path d="M3 20h18M5 15l4-7 5 5 6-9"/>','<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 3"/>','<path d="M3 5q5-2 9 1 4-3 9-1v14q-5-2-9 1-4-3-9-1zM12 6v14"/>'];
document.querySelector('nav').innerHTML=Object.entries(pages).map(([id,[label]],i)=>'<a href="#'+id+'"><svg viewBox="0 0 24 24">'+icons[i]+'</svg>'+label+'</a>').join('');
let page='',data=null,angle=0,rotate=!matchMedia('(prefers-reduced-motion: reduce)').matches,previous=0;
let cursor=null,running=false,sequence=0,historyPage=0,requestId=0;
const f=n=>Number(n).toFixed(3),vector=v=>'('+v.map(n=>f(Math.abs(n)<.0005?0:n)).join(', ')+')';
function error(msg=''){$('error').hidden=!msg;$('error').textContent=msg}
async function api(url,options){const r=await fetch(url,options);if(!r.ok){let v=await r.json().catch(()=>({}));throw Error(v.error||'The local server could not complete the request.')}return r}
const post=d=>({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
function settings(){return Object.fromEntries([...['theta','phi','p','e'].map(k=>[k,Number(form.elements[k].value)]),['model',form.elements.model.value],['feed',form.elements.feed.checked]])}
function table(head,rows){return '<table><thead><tr>'+head.map(v=>'<th>'+v+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(v=>'<td>'+v+'</td>').join('')+'</tr>').join('')+'</tbody></table>'}
let circuitTimer, sampled=null;
function branches(){if(!data)return;$('receipt').textContent='';const model=data.models[data.settings.model],sent=parseInt($('measured').value,2);
 const rows=Object.entries(model.patterns).map(([mask,prob])=>{const n=sent^parseInt(mask,2);return [mask,n.toString(2).padStart(2,'0'),(100*prob).toFixed(1)+'%',data.settings.feed?['Identity','X','Z','X then Z'][n]:'Disabled']});
 $('messages').innerHTML=table(['Bits flipped¹','Bob receives','Probability','Bob applies'],rows)+'<p class="hint">¹ A 1 marks a flipped bit. Probabilities are conditional on the chosen Alice outcome.</p>'}
function show(){
 if(!data)return;
 const active=data.models[data.settings.model],metrics=[['Input fidelity',f(data.fidelity)],['Six-state mean',f(active.mean)],['Resource mixing p',f(data.settings.p)]];
 $('metrics').innerHTML=metrics.map(([label,val])=>'<div class="metric"><span>'+label+'</span><strong>'+val+'</strong></div>').join('');
 $('avec').textContent=vector(data.input);$('bvec').textContent=vector(data.output);
 $('rotate').textContent=rotate?'Align views':'Rotate Bob';
 $('plot').innerHTML=chart(data);paintCursor();renderCircuit();branches();
 $('comparison').innerHTML=table(['Pattern','Neither flips','Both flip','Input fidelity','Six-state mean'],Object.entries(data.models).map(([name,v])=>[name,((v.patterns['00']||0)*100).toFixed(1)+'%',((v.patterns['11']||0)*100).toFixed(1)+'%',v.fidelity.toFixed(6),v.mean.toFixed(6)]));
 $('numbers').innerHTML=table(['Input state','0','1','+','−','+i','−i'],[['Fidelity',...['0','1','+','-','+i','-i'].map(k=>f(active.values[k]))]])+'<p>Bob’s density matrix</p><pre>'+data.matrix.map(row=>row.join('      ')).join('\n')+'</pre><p>Measurement probabilities (00, 01, 10, 11): '+data.outcomes.map(f).join(' · ')+'</p>';
 $('sweepstatus').textContent='p = '+data.settings.p.toFixed(2)+'  ·  '+data.settings.model;
}
function pause(reset=false){running=false;sequence++;if(reset)cursor=null;$('sweep').textContent=cursor===null?'Start sweep':cursor>=100?'Replay sweep':'Resume sweep'}
async function calculate(isSweep=false){if(!form.reportValidity())return false;const id=++requestId;
 try{const result=await(await api('/api/run',post({...settings(),sweep:isSweep}))).json();if(id!==requestId)return false;data=result;sampled=null;error();show();return true}catch(e){error(e.message);return false}}
async function sweep(){
 if(running){pause();return}if(!form.reportValidity())return;
 running=true;const token=++sequence;$('sweep').textContent='Pause sweep';
 for(let step=cursor===null||cursor===100?0:cursor+1;step<=100&&running&&sequence===token;step++){
  cursor=step;form.elements.p.value=(step/100).toFixed(2);
  if(!await calculate(true)){if(sequence===token)pause();return}
  await new Promise(resolve=>setTimeout(resolve,95))
 }if(sequence===token)pause()
}
async function loadHistory(){try{
 const result=await(await api('/api/history?page='+historyPage)).json();$('events').replaceChildren();
 for(const [stamp,area,title,detail] of result.rows){const item=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');
 summary.textContent=stamp.slice(0,19)+'   ·   '+area+'   ·   '+title;pre.textContent=detail;item.append(summary,pre);$('events').append(item)}
 $('count').textContent=result.count+' entries · page '+(historyPage+1);$('newer').disabled=!historyPage;$('older').disabled=(historyPage+1)*30>=result.count;
 }catch(e){error(e.message)}}
function route(){
 pause();const requested=location.hash.slice(1),guide=requested==='software-guide';page=guide?'theory':Object.hasOwn(pages,requested)?requested:'overview';
 const [label,title,sub,list]=pages[page];$('crumb').textContent=label;$('heading').textContent=title;$('subtitle').textContent=sub;
 document.querySelectorAll('nav a').forEach(a=>{a.classList.toggle('active',a.hash==='#'+page);a.setAttribute('aria-current',a.hash==='#'+page?'page':'false')});
 document.querySelectorAll('.content>section').forEach(s=>s.hidden=true);
 for(const id of list.split(' ')){const el=$(id);el.parentNode.append(el);el.hidden=false}
 if(guide)$('first-visit').hidden=true;
 if(page==='history'){historyPage=0;loadHistory()}
 if(guide)openGuide();else window.scrollTo(0,0);renderCircuit()
}
function openGuide(){
 const guide=$('software-guide');guide.open=true;
 guide.querySelector('summary').focus({preventScroll:true});
 guide.scrollIntoView({block:'start'});
}
// The launcher uses a different port each run. A host cookie remembers visits across ports.
const visitorCookie='teleportation_lab_guide_seen=1';
if(!document.cookie.split(';').some(item=>item.trim()===visitorCookie)){
 document.cookie=visitorCookie+'; Max-Age=34560000; Path=/; SameSite=Strict';
 $('first-visit').hidden=false;
}
$('guide-pin').addEventListener('click',()=>{if(location.hash==='#software-guide')openGuide()});
function frame(t){
 if(data&&!document.hidden&&!$('visual').hidden&&t-previous>=40){
  if(rotate)angle+=(previous?Math.min(100,t-previous):0)*Math.PI/11000;previous=t;
  sphere($('alice'),data.input,0,false);sphere($('bob'),data.output,angle,true)
 }requestAnimationFrame(frame)
}
form.onsubmit=e=>{e.preventDefault();pause(true);calculate()};
form.oninput=()=>pause(true);
$('rotate').onclick=()=>{rotate=!rotate;angle=0;show()};
$('measured').onchange=()=>{sampled=null;branches();renderCircuit()};
$('transmit').onclick=async()=>{
 if(!data)return;
 try{
 const snapshot=data,sent=$('measured').value;
 const result=await(await api('/api/message',post({...snapshot.settings,sent}))).json();
 if(snapshot!==data||sent!==$('measured').value)return;
 sampled=result.received;renderCircuit();
 $('receipt').textContent='Sent '+result.sent+'  →  Received '+result.received+'  ·  Correction: '+result.correction;
 $('receipt').animate([{opacity:.2,transform:'translateX(-8px)'},{opacity:1,transform:'translateX(0)'}],{duration:280});
 }catch(e){error(e.message)}
};
for(const [button,noise] of [['moderate',.2],['high',.6]]){
 $(button).onclick=()=>{pause(true);form.elements.p.value=noise;form.elements.e.value=.1;form.elements.feed.checked=true;calculate()}
}
$('ideal').onclick=()=>{pause(true);form.elements.p.value=0;form.elements.e.value=0;form.elements.feed.checked=true;calculate()};
$('example').onclick=()=>{pause(true);form.elements.theta.value=180;form.elements.model.value='Independent';form.elements.phi.value=0;form.elements.p.value=0;form.elements.e.value=.1;form.elements.feed.checked=true;calculate()};
$('sweep').onclick=sweep;
$('csv').onclick=async()=>{pause();if(!form.reportValidity())return;try{const blob=await(await api('/api/csv',post(settings()))).blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='teleportation-results.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000)}catch(e){error(e.message)}};
$('refresh').onclick=()=>{historyPage=0;loadHistory()};$('older').onclick=()=>{historyPage++;loadHistory()};$('newer').onclick=()=>{historyPage--;loadHistory()};
window.addEventListener('hashchange',route);document.addEventListener('visibilitychange',()=>{if(document.hidden&&running)pause()});
function renderCircuit(){
 clearTimeout(circuitTimer);
 if(!data||$('protocol').hidden)return;
 const {theta,phi,p,e,model,feed}=data.settings,sent=$('measured').value;
 const [mask]=Object.entries(data.models[model].patterns).sort((a,b)=>b[1]-a[1])[0];
 const received=sampled??(parseInt(sent,2)^parseInt(mask,2)).toString(2).padStart(2,'0');
 const action=(gate,bit)=>!feed?gate+' skipped · corrections disabled':gate+(bit==='1'?' applied':' skipped')+' · control bit '+bit;
 const stages=[
  'Prepare Alice’s input with θ = '+theta+'° and φ = '+phi+'°.',
  'H and CNOT create the Bell pair; the resource model mixes in '+(100*p).toFixed(1)+'% white noise.',
  'Alice applies CNOT from input q0 to her resource qubit q1.',
  'Alice applies H to q0 before reading the two qubits.',
  'Inspect Alice’s measurement '+sent+' (probability '+(100*data.outcomes[parseInt(sent,2)]).toFixed(1)+'%).',
  'Alice sends '+sent+' through the '+model.toLowerCase()+' error channel (e = '+e+'). Bob receives '+received+'.',
  action('X',received[1]),action('Z',received[0])
 ];
 $('branch-caption').textContent=(sampled===null?'Most probable message for this outcome':'Sampled transmission')+' · '+sent+' → '+received+' · Fidelity above averages all branches.';
 function paint(i){
  $('circuit').innerHTML=circuit(feed,received,i);
  $('gate-caption').textContent=(i+1)+' / 8   '+stages[i];
  if(i<7)circuitTimer=setTimeout(()=>paint(i+1),780);
 }
 paint(matchMedia('(prefers-reduced-motion: reduce)').matches?7:0);
}
$('replay-circuit').onclick=renderCircuit;
route();calculate();requestAnimationFrame(frame);


const noisePlot=$('plot');
let cursorTarget=null, cursorPosition=null, cursorFrame=0;
function paintCursor(){
 if(cursorTarget===null||!data)return;
 const svg=noisePlot.querySelector('svg');if(!svg)return;
 let overlay=svg.querySelector('.cursor-guide');
 if(!overlay){
  overlay=document.createElementNS(svg.namespaceURI,'g');
  overlay.setAttribute('class','cursor-guide');
  overlay.innerHTML='<line y1="25" y2="158" stroke="#d3e7ee" stroke-dasharray="3 4"/><circle r="5" fill="#122331" stroke="#70e6cd" stroke-width="2"/><circle r="3" fill="#b9a5ff"/><g><rect width="155" height="68" rx="6" fill="#091925" stroke="#466173"/><text x="9" y="17" fill="#eaf5f7"></text><text x="9" y="38" fill="#70e6cd"></text><text x="9" y="58" fill="#b9a5ff"></text></g>';
  svg.append(overlay);
 }
 const p=cursorPosition,x=58+665*p;
 const values=['Independent','Linked'].map(name=>(1-p)*data.models[name].start+p*.5);
 const [guide,first,second,box]=overlay.children;
 guide.setAttribute('x1',x);guide.setAttribute('x2',x);
 [first,second].forEach((point,i)=>{point.setAttribute('cx',x);point.setAttribute('cy',158-(values[i]-.3)*190)});
 box.setAttribute('transform','translate('+(x>555?x-166:x+11)+' 64)');
 const labels=box.querySelectorAll('text');
 labels[0].textContent='Preview p = '+p.toFixed(3);
 labels[1].textContent='Independent   '+values[0].toFixed(4);
 labels[2].textContent='Linked             '+values[1].toFixed(4);
}
function glide(){
 cursorFrame=0;
 if(cursorTarget===null)return;
 const gap=cursorTarget-cursorPosition;
 cursorPosition=Math.abs(gap)<.0002||matchMedia('(prefers-reduced-motion: reduce)').matches?cursorTarget:cursorPosition+gap*.42;
 paintCursor();
 if(cursorPosition!==cursorTarget)cursorFrame=requestAnimationFrame(glide);
}
function trackCursor(event){
 const svg=noisePlot.querySelector('svg');if(!svg)return;
 const transform=svg.getScreenCTM();if(!transform)return;
 const point=new DOMPoint(event.clientX,event.clientY).matrixTransform(transform.inverse());
 cursorTarget=Math.max(0,Math.min(1,(point.x-58)/665));
 if(cursorPosition===null)cursorPosition=cursorTarget;
 if(!cursorFrame)cursorFrame=requestAnimationFrame(glide);
}
noisePlot.addEventListener('pointermove',trackCursor);
noisePlot.addEventListener('pointerdown',trackCursor);
function hideCursor(){
 cancelAnimationFrame(cursorFrame);cursorFrame=0;cursorTarget=cursorPosition=null;
 noisePlot.querySelector('.cursor-guide')?.remove();
}
noisePlot.addEventListener('pointerleave',hideCursor);
noisePlot.addEventListener('pointercancel',hideCursor);
window.addEventListener('hashchange',hideCursor);
$('theory-chapter').addEventListener('change',event=>{
 const chapter=document.getElementById(event.target.value);
 if(!chapter)return;
 chapter.open=true;
 chapter.querySelector('summary').focus({preventScroll:true});
 chapter.scrollIntoView({block:'start'});
 event.target.selectedIndex=0;
});
