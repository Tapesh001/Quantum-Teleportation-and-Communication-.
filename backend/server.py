"""Local browser interface for the teleportation model (standard library only)."""
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import csv
import io
import json
import math
import os
import random
import sqlite3
import webbrowser

from .engine import ERROR_MODELS, input_state, flip_patterns, simulate, six_state

ASSETS = Path(__file__).resolve().parents[1] / 'frontend'
DB = Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'QuantumTeleportation' / 'history.sqlite3'


def record(area, title, detail):
    with sqlite3.connect(DB) as db:
        db.execute('INSERT INTO events(stamp,area,title,detail) VALUES(?,?,?,?)',
                   (datetime.now().astimezone().isoformat(sep=' ', timespec='seconds'), area, title, detail))


def parameters(data):
    angles = [float(data[k]) for k in ('theta','phi','p','e')]
    t,f,p,e = angles
    if not all(map(math.isfinite,angles)) or not 0<=t<=180 or not 0<=p<=1 or not 0<=e<=1:
        raise ValueError('Use θ from 0 to 180 and probabilities from 0 to 1.')
    if data['model'] not in ERROR_MODELS or type(data['feed']) is not bool:
        raise ValueError('Choose a listed error model and correction setting.')
    return t,f,p,e,data['model'],data['feed']


def calculate(data):
    t,f,p,e,model,feed = parameters(data)
    psi = input_state(t,f)
    output = simulate(psi,p,e,feed,model)
    a,b=psi
    inputs=[2*(a.conjugate()*b).real,2*(a.conjugate()*b).imag,abs(a)**2-abs(b)**2]
    rows={}
    for name in ERROR_MODELS:
        vals,mean=six_state(p,e,feed,name)
        rows[name]=dict(values=vals,mean=mean,start=six_state(0,e,feed,name)[1],patterns={f'{i}{j}':v for i,j,v in flip_patterns(e,name)},
                        fidelity=simulate(psi,p,e,feed,name)['fidelity'])
    matrix=[[f'{z.real:.4f}{z.imag:+.4f}i' for z in row] for row in output['rho']]
    return dict(input=inputs,output=output['bloch'],fidelity=output['fidelity'],outcomes=output['outcomes'],
                matrix=matrix,models=rows,settings=dict(theta=t,phi=f,p=p,e=e,model=model,feed=feed))


class Handler(BaseHTTPRequestHandler):
    def reply(self, body, mime='application/json', code=200):
        if not isinstance(body,bytes):
            body=json.dumps(body,ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(body)

    def local(self):
        return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

    def do_GET(self):
        if not self.local():
            return self.send_error(403)
        url=urlsplit(self.path)
        if url.path=='/api/history':
            try:
                page=max(0,int(parse_qs(url.query).get('page',['0'])[0]))
                with sqlite3.connect(DB) as db:
                    count=db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
                    rows=db.execute('SELECT stamp,area,title,detail FROM events ORDER BY id DESC LIMIT 30 OFFSET ?', (min(page,count//30)*30,)).fetchall()
                return self.reply(dict(count=count,rows=rows))
            except (ValueError,sqlite3.Error):
                return self.reply({'error':'Could not read history.'},code=400)
        routes={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),
                '/styles.css':('styles.css','text/css; charset=utf-8'),'/views.js':('views.js','text/javascript; charset=utf-8')}
        if url.path not in routes:
            return self.send_error(404)
        name,mime=routes[url.path]
        self.reply((ASSETS/name).read_bytes(),mime)

    def do_POST(self):
        if not self.local() or self.headers.get('Origin') not in (None,'http://'+self.headers['Host']):
            return self.send_error(403)
        try:
            size=int(self.headers.get('Content-Length',0))
            if not 0<size<=2048 or self.headers.get_content_type()!='application/json':
                return self.send_error(400)
            data=json.loads(self.rfile.read(size))
            if self.path=='/api/message':
                _,_,_,e,model,feed=parameters(data)
                sent=data['sent']
                if sent not in ('00','01','10','11'):
                    raise ValueError('Select a two-bit measurement outcome.')
                patterns=flip_patterns(e,model)
                first,second,_=random.choices(patterns,weights=[p[2] for p in patterns],k=1)[0]
                value=int(sent,2) ^ ((first<<1)|second)
                receipt=dict(sent=sent,received=format(value,'02b'),correction=('Identity','X','Z','X then Z')[value] if feed else 'disabled')
                record('Lab','Classical message',json.dumps(dict(**receipt,e=e,model=model)))
                return self.reply(receipt)
            if self.path=='/api/run':
                result=calculate(data)
                area='Sweep' if data.get('sweep') else 'Lab'
                record(area,f"{result['settings']['model']} · p = {data['p']} · e = {data['e']}",json.dumps(result,indent=2,ensure_ascii=False))
                return self.reply(result)
            if self.path=='/api/csv':
                _,_,_,e,model,feed=parameters(data)
                stream=io.StringIO()
                writer=csv.writer(stream)
                writer.writerow(['p','e','feedforward','input_state','selected_model','independent_fidelity','linked_fidelity','independent_mean','linked_mean'])
                for step in range(101):
                    results=[six_state(step/100,e,feed,m) for m in ERROR_MODELS]
                    for state in results[0][0]:
                        writer.writerow([step/100,e,feed,state,model,*(r[0][state] for r in results),*(r[1] for r in results)])
                record('Export','CSV generated',f'606 rows · e = {e:g} · corrections = {feed}')
                return self.reply(stream.getvalue().encode(),'text/csv; charset=utf-8')
            self.send_error(404)
        except (ValueError,TypeError,KeyError,OverflowError) as exc:
            self.reply({'error':str(exc)},code=400)
        except sqlite3.Error:
            self.reply({'error':'The local history database could not be accessed.'},code=500)

    def log_message(self,*args):
        pass


def start(browser=True):
    DB.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(DB) as db:
        db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY,stamp TEXT,area TEXT,title TEXT,detail TEXT)')
    with ThreadingHTTPServer(('127.0.0.1',0),Handler) as server:
        url=f'http://127.0.0.1:{server.server_port}/'
        print(f'Teleportation Lab is running at {url}\nKeep this window open. Press Ctrl+C to exit.',flush=True)
        record('Session','Browser lab opened','Local workspace')
        if browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

