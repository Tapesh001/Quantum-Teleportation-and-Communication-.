const mint='#70e6cd',gold='#ffd28d',muted='#a2b7c5';
export function sphere(canvas,v,angle,bob){
 const w=canvas.clientWidth,h=canvas.clientHeight;if(!w||!h)return;
 const d=Math.min(devicePixelRatio,2);
 if(canvas.width!==Math.round(w*d)||canvas.height!==Math.round(h*d)){canvas.width=Math.round(w*d);canvas.height=Math.round(h*d)}
 const c=canvas.getContext('2d');c.setTransform(d,0,0,d,0,0);c.clearRect(0,0,w,h);
 const r=Math.max(10,Math.min(w/2-25,h/2-20)),cx=w/2,cy=h/2,ca=Math.cos(angle+.64),sa=Math.sin(angle+.64);
 const pt=([x,y,z])=>[cx+r*(-sa*x+ca*y),cy+r*(.35*(ca*x+sa*y)-Math.sqrt(1-.35**2)*z)];
 function line(points,color,width=1){c.beginPath();points.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.strokeStyle=color;c.lineWidth=width;c.stroke()}
 function dot(x,y,rad,color){c.beginPath();c.arc(x,y,rad,0,2*Math.PI);c.fillStyle=color;c.fill()}
 const fill=c.createRadialGradient(cx-r*.3,cy-r*.4,1,cx,cy,r);fill.addColorStop(0,'#204657');fill.addColorStop(1,'#112635');
 dot(cx,cy,r,fill);c.strokeStyle='#82a5b4';c.lineWidth=1.6;c.stroke();
 for(let plane=0;plane<3;plane++){let points=[];for(let k=0;k<=90;k++){let a=Math.cos(k*Math.PI/45),b=Math.sin(k*Math.PI/45);points.push(pt([[a,b,0],[a,0,b],[0,a,b]][plane]))}line(points,'#416375')}
 c.font='600 12px system-ui';c.textAlign='center';c.textBaseline='middle';
 for(let j=0;j<3;j++)for(const sign of [-1,1]){let axis=[0,0,0];axis[j]=sign;let [x,y]=pt(axis);
 if(sign===1)line([[cx,cy],[x,y]],'#617e8b');dot(x,y,3,'#b5d4d8');c.fillStyle='#dbedf0';c.fillText((sign>0?'+':'−')+'XYZ'[j],x+(j===2?14:(x>=cx?12:-12)),y+(j===2?0:(y>=cy?7:-7)))}
 const [ex,ey]=pt(v),col=bob?gold:mint;line([[cx,cy],[ex,ey]],col,4);
 const a=Math.atan2(ey-cy,ex-cx);if(Math.hypot(ex-cx,ey-cy)>12){c.beginPath();c.moveTo(ex,ey);for(const offset of [-.43,.43])c.lineTo(ex-13*Math.cos(a+offset),ey-13*Math.sin(a+offset));c.closePath();c.fillStyle=col;c.fill()}
 dot(ex,ey,4.5,col);
}
const svg=(w,h,body,label)=>'<svg viewBox="0 0 '+w+' '+h+'" role="img" aria-label="'+label+'" xmlns="http://www.w3.org/2000/svg">'+body+'</svg>';
const line=(x,y,a,b,color,width=1,dash='')=>'<line x1="'+x+'" y1="'+y+'" x2="'+a+'" y2="'+b+'" stroke="'+color+'" stroke-width="'+width+'" stroke-dasharray="'+dash+'"/>';
const txt=(x,y,s,color=muted,anchor='middle')=>'<text x="'+x+'" y="'+y+'" fill="'+color+'" text-anchor="'+anchor+'" font-family="system-ui" font-size="13">'+s+'</text>';
export function chart(data){
 const Y=f=>158-(f-.3)*190,X=p=>58+665*p;
 let out='';for(const f of [.4,.5,2/3,.8,1])out+=line(58,Y(f),723,Y(f),f===2/3?'#caa56b':'#304958',1,'4 4')+txt(49,Y(f)+4,f.toFixed(3),muted,'end');
 for(const [name,color] of [['Independent',mint],['Linked','#b9a5ff']]){
 const start=data.models[name].start;
 out+=line(X(0),Y(start),X(1),Y(.5),color,3,name==='Linked'?'7 4':'')}
 for(const p of [0,.2,.4,.6,.8,1])out+=txt(X(p),181,p.toFixed(1));
 out+=txt(392,202,'Resource mixing p')+txt(228,17,'Independent',mint)+txt(530,17,'Linked','#b9a5ff');
 const m=data.models[data.settings.model].mean;
 out+='<circle cx="'+X(data.settings.p)+'" cy="'+Y(m)+'" r="6" fill="'+gold+'"/>';
 return svg(760,209,out,'Six-state mean fidelity against resource mixing');
}
export function circuit(feed,received,step){
 let s='';const ys=[37,84,131];
 for(let i=0;i<3;i++)s+=txt(45,ys[i]+4,['q0 · input','q1 · Alice','q2 · Bob'][i])+line(85,ys[i],730,ys[i],'#426373');
 function gate(x,y,symbol,on=true){return '<rect x="'+(x-15)+'" y="'+(y-15)+'" width="30" height="30" rx="5" fill="'+(on?'#1d4546':'#283340')+'" stroke="'+(on?mint:muted)+'"/>'+txt(x,y+5,symbol,on?mint:muted)}
 function cx(x,y1,y2){return line(x,y1,x,y2,mint,2)+'<circle cx="'+x+'" cy="'+y1+'" r="5" fill="'+mint+'"/><circle cx="'+x+'" cy="'+y2+'" r="10" fill="#123039" stroke="'+mint+'"/>'+line(x-8,y2,x+8,y2,mint)+line(x,y2-8,x,y2+8,mint)}
 function stage(i,body){return '<g class="circuit-stage '+(i===step?'lit':i<step?'done':'waiting')+'">'+body+'</g>'}
 s+=stage(0,gate(108,37,'ψ'))+stage(1,gate(173,84,'H')+cx(244,84,131))+stage(2,cx(336,37,84))+stage(3,gate(401,37,'H'));
 s+=stage(5,line(467,37,467,16,gold,1,'3 3')+line(467,16,672,16,gold,1,'3 3')+line(672,16,672,115,gold,1,'3 3'));
 s+=stage(5,line(503,84,591,84,gold,1,'3 3')+line(591,84,591,115,gold,1,'3 3'))+stage(4,gate(467,37,'M')+gate(503,84,'M'))+stage(6,gate(591,131,'X',feed&&received[1]==='1'))+stage(7,gate(672,131,'Z',feed&&received[0]==='1'));
 return svg(760,161,s,'Teleportation circuit from input preparation to conditional correction');
}
