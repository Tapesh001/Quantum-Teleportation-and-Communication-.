"""Optional Tkinter interface using the shared teleportation engine."""
import csv
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.engine import ERROR_MODELS, flip_patterns, input_state, prediction, simulate, six_state

def launch():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from history_view import History
    from bloch_view import BlochPair, pure_vector
    root = tk.Tk()
    root.title('Quantum Teleportation | Project Software')
    root.geometry(f'{min(1100,root.winfo_screenwidth()-40)}x{min(790,root.winfo_screenheight()-90)}')
    root.minsize(760,520)
    root.configure(bg='#091725')
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('TFrame',background='#091725')
    style.configure('TLabel',background='#091725',foreground='#e9f4fa',font=('Segoe UI',11))
    style.configure('TCheckbutton',background='#091725',foreground='#e9f4fa')
    style.configure('TButton',font=('Segoe UI',10),padding=7)
    style.configure('TNotebook.Tab',font=('Segoe UI',11,'bold'),padding=(14,7))
    tabs = ttk.Notebook(root)
    tabs.pack(fill='both',expand=True)
    history = History(tabs)
    history.record('Session','Simulator opened')
    lab = ttk.Frame(tabs)
    tabs.add(lab,text='Simulation lab')
    tabs.add(history,text='History')
    # Keep the entire sphere panel in the visible lab. Only the controls,
    # chart and numerical output scroll, regardless of Windows display scaling.
    spheres = BlochPair(lab)
    spheres.pack(fill='x',padx=8,pady=(6,0))
    sweep_row = ttk.Frame(lab)
    sweep_row.pack(fill='x',padx=10,pady=4)
    lower = ttk.Frame(lab)
    lower.pack(fill='both',expand=True)
    viewport = tk.Canvas(lower, bg='#091725', highlightthickness=0)
    scroll = ttk.Scrollbar(lower,orient='vertical',command=viewport.yview)
    scroll.pack(side='right',fill='y')
    viewport.configure(yscrollcommand=scroll.set)
    viewport.pack(fill='both',expand=True)
    frame = ttk.Frame(viewport,padding=14)
    window = viewport.create_window(0,0,window=frame,anchor='nw')
    frame.bind('<Configure>',lambda event: viewport.configure(scrollregion=viewport.bbox('all')))
    ttk.Label(frame,text='Quantum Teleportation and Communication',font=('Segoe UI',23,'bold')).pack(anchor='w')
    ttk.Label(frame,text='Exact numerical simulation of three qubits. No quantum hardware or internet required.').pack(anchor='w',pady=(5,15))
    controls = ttk.Frame(frame)
    controls.pack(fill='x')
    theta,phi,p,e = [tk.StringVar(value=x) for x in ('90','90','0','0')]
    feed = tk.BooleanVar(value=True)
    for col,(title,var) in enumerate([('Theta (0-180 degrees)',theta),('Phi (degrees)',phi),('Resource mixing p (0-1)',p),('Bit error e (0-1)',e)]):
        cell = ttk.Frame(controls)
        cell.grid(row=0,column=col,padx=(0,18),sticky='w')
        ttk.Label(cell,text=title).pack(anchor='w')
        ttk.Entry(cell,textvariable=var,width=19).pack(anchor='w',pady=6)
    ttk.Checkbutton(frame,text="Apply Bob's corrections (classical feedforward)",variable=feed).pack(anchor='w',pady=5)
    presets = ttk.Frame(frame)
    presets.pack(fill='x',pady=7)
    comparison = ttk.Frame(frame)
    comparison.pack(fill='x',pady=3)
    ttk.Label(comparison,text='Bit errors in the lab').pack(side='left',padx=(0,8))
    model_choice = ttk.Combobox(comparison,values=ERROR_MODELS,state='readonly',width=13)
    model_choice.current(0)
    model_choice.pack(side='left')
    table = ttk.Treeview(frame,columns=('model','none','both','input','mean'),show='headings',height=2,
                         selectmode='none')
    for key,title in zip(table['columns'],('Error pattern','Neither bit flips','Both bits flip','Input fidelity','Six-state mean')):
        table.heading(key,text=title)
        table.column(key,width=110,minwidth=80,anchor='center')
    for model in ERROR_MODELS:
        table.insert('','end',iid=model)
    table.pack(fill='x',pady=3)
    sweep_status = tk.StringVar(value='Changing noise setting   ·   p runs from 0 to 1')
    lab.bind('<Configure>',lambda event: spheres.configure(height=min(540,round(event.height*.56))))
    viewport.bind('<Configure>',lambda event: viewport.itemconfigure(window,width=event.width))
    result = tk.Text(frame,height=12,bg='#102538',fg='#e9f4fa',font=('Consolas',11),relief='flat',padx=14,pady=12,wrap='word')
    chart = tk.Canvas(frame,height=173,bg='#091725',highlightthickness=0)
    cache = {}
    timer = None
    sweep_index = None
    writing_step = False

    def parameters():
        t,f,pv,ev = map(float,(theta.get(),phi.get(),p.get(),e.get()))
        if not all(math.isfinite(x) for x in (t,f,pv,ev)) or not 0 <= t <= 180 or not 0 <= pv <= 1 or not 0 <= ev <= 1:
            raise ValueError('Theta must be 0-180; p and e must be 0-1. All values must be finite.')
        return t,f,pv,ev

    def run(action='Calculate',area='Lab'):
        try:
            t,f,pv,ev = parameters()
            state = input_state(t,f)
            selected = model_choice.get()
            results = {}
            for model in ERROR_MODELS:
                output = simulate(state,pv,ev,feed.get(),model)
                values,mean = six_state(pv,ev,feed.get(),model)
                results[model] = (output,values,mean)
                weights = {(a,b):weight for a,b,weight in flip_patterns(ev,model)}
                table.item(model,values=(model,f"{weights.get((0,0),0):.1%}",f"{weights.get((1,1),0):.1%}",
                                         f"{output['fidelity']:.6f}",f"{mean:.6f}"))
            r,vals,avg = results[selected]
            cache.update(p=pv,e=ev,feed=feed.get(),values=vals,model=selected)
            spheres.show(pure_vector(state),r['bloch'],f"All outcomes averaged   ·   Fidelity {r['fidelity']:.3f}")
            text = f'Input amplitudes: a = {state[0]:.4f}, b = {state[1]:.4f}\n'
            text += f'Current input fidelity: {r["fidelity"]:.6f}       Six-state average: {avg:.6f}\n'
            text += 'Six-state benchmark: 2/3 = 0.666667 (fair unknown-state measure-and-prepare comparison)\n'
            text += f'Analytic average: {prediction(pv,ev,selected) if feed.get() else .5:.6f}\n\n'
            text += 'Six-state fidelities:  ' + '   '.join(f'{k}: {v:.4f}' for k,v in vals.items())+'\n'
            text += 'Alice outcomes:       ' + '   '.join(f'{m:02b}: {v:.4f}' for m,v in enumerate(r['outcomes']))+'\n'
            text += 'Bob Bloch vector:     '+str(tuple(round(v,5) for v in r['bloch']))+'\n'
            rho = r['rho']
            text += f'Bob density matrix:   [{rho[0][0]:.4f}   {rho[0][1]:.4f}]\n'
            text += f'                      [{rho[1][0]:.4f}   {rho[1][1]:.4f}]\n'
            result.configure(state='normal');result.delete('1.0','end');result.insert('1.0',text);result.configure(state='disabled')
            draw(ev,pv,avg)
            comparison_text = '\n'.join(
                f"{m}: input fidelity {results[m][0]['fidelity']:.6f}, six-state mean {results[m][2]:.6f}"
                for m in ERROR_MODELS)
            history.record(area,action,f'θ = {t:g}°, φ = {f:g}°, p = {pv:g}, e = {ev:g}\n'
                           f'Error model: {selected}   ·   Bob corrects: {feed.get()}\n'
                           f'{comparison_text}\n\n{text}')
            return True
        except ValueError as exc:
            messagebox.showerror('Check your inputs',str(exc))
            return False

    def draw(ev,pv,avg):
        chart.delete('all')
        w = max(chart.winfo_width(),120)
        x0,y0,x1,y1 = 65,26,w-30,132
        def xy(px,fy):return x0+px*(x1-x0),y1-(fy-.3)/.7*(y1-y0)
        chart.create_text(x0,10,text='Six-state average fidelity versus resource mixing p',anchor='w',fill='#e9f4fa',font=('Segoe UI',11,'bold'))
        chart.create_line(x0,y0,x0,y1,x1,y1,fill='#91afc1')
        for fy in [.4,.5,2/3,.8,1]:
            yy=xy(0,fy)[1]
            chart.create_line(x0,yy,x1,yy,fill='#ffc86b' if fy==2/3 else '#20394b',dash=(4,4))
            chart.create_text(x0-8,yy,text=f'{fy:.3f}',anchor='e',fill='#91afc1')
        for model,color,dash in [('Independent','#43e6cd',()),('Linked','#c7abff',(5,4))]:
            # The mean is linear in resource mixing for both channels.
            left = prediction(0,ev,model) if cache['feed'] else .5
            chart.create_line(*xy(0,left),*xy(1,.5),fill=color,width=2,dash=dash)
        x,y=xy(pv,avg);chart.create_oval(x-5,y-5,x+5,y+5,fill='#ffc86b',outline='',tags='current_point')
        for px in [0,.2,.4,.6,.8,1]:
            chart.create_text(xy(px,.3)[0],y1+15,text=f'{px:.1f}',fill='#91afc1')
        chart.create_text((x0+x1)/2,y1+34,text=f"Resource mixing p    ·    Solid: independent    ·    Dashed: linked    ·    Point: {cache['model']} (e = {ev:.2f})",fill='#e9f4fa')

    def preset(pv,ev,ff=True,action='Preset'):
        p.set(str(pv));e.set(str(ev));feed.set(ff);run(action)

    def export():
        stop_sweep()
        try:parameters()
        except ValueError as exc:
            messagebox.showerror('Check your inputs',str(exc));return
        run('Calculate for CSV export')
        name=filedialog.asksaveasfilename(defaultextension='.csv',initialfile='teleportation_results.csv',filetypes=[('CSV','*.csv')])
        if not name:return
        try:
            with open(name,'w',newline='',encoding='utf-8') as f:
                writer=csv.writer(f)
                writer.writerow(['p','e','feedforward','input_state','fidelity','six_state_mean','analytic_mean','selected_model',
                                 'independent_fidelity','linked_fidelity','independent_mean','linked_mean'])
                selected = cache['model']
                for i in range(101):
                    pv=i/100
                    outputs = {model:six_state(pv,cache['e'],cache['feed'],model) for model in ERROR_MODELS}
                    vals,avg = outputs[selected]
                    expected = prediction(pv,cache['e'],selected) if cache['feed'] else .5
                    for label,value in vals.items():
                        writer.writerow([pv,cache['e'],cache['feed'],label,value,avg,expected,selected,
                                         *(outputs[m][0][label] for m in ERROR_MODELS),*(outputs[m][1] for m in ERROR_MODELS)])
            history.record('Export','Saved CSV',f"{name}\n606 state results, 101 resource-noise settings.\n"
                           f"e = {cache['e']:g}, model = {selected}, corrections = {cache['feed']}")
            messagebox.showinfo('Export complete','Saved 606 state results over 101 resource-noise settings.')
        except OSError as exc:messagebox.showerror('Export failed',str(exc))

    def stop_sweep():
        nonlocal timer
        if timer is not None:
            root.after_cancel(timer)
            timer = None
            history.record('Sweep','Sweep paused',f'p = {sweep_index/100:.2f}')
        if sweep_index is not None and sweep_index < 100:
            sweep_button.configure(text='Resume sweep')
            sweep_status.set(f'Changing noise setting   ·   Paused at p = {sweep_index/100:.2f}')

    def clear_sweep(*args):
        nonlocal sweep_index
        if writing_step:
            return
        stop_sweep()
        sweep_index = None
        sweep_button.configure(text='Start noise sweep')
        sweep_status.set('Changing noise setting   ·   p runs from 0 to 1')

    def sweep_frame(index):
        nonlocal timer, sweep_index, writing_step
        timer = None
        sweep_index = index
        writing_step = True
        try:
            p.set(f'{index/100:.2f}')
        finally:
            writing_step = False
        if not run(f'Noise setting p = {index/100:.2f}','Sweep'):
            clear_sweep()
            return
        mean = sum(cache['values'].values())/6
        sweep_status.set(f'Changing noise setting   ·   p = {p.get()}   ·   Mean fidelity {mean:.3f}')
        if index == 100:
            history.record('Sweep','Sweep completed','Reached p = 1.00.')
            sweep_button.configure(text='Replay sweep')
        else:
            sweep_button.configure(text='Pause sweep')
            timer = root.after(95,sweep_frame,index+1)

    def toggle_sweep():
        if timer is not None:
            stop_sweep()
            return
        try:
            parameters()
        except ValueError as exc:
            messagebox.showerror('Check your inputs',str(exc))
            return
        viewport.yview_moveto(chart.winfo_y()/max(1,frame.winfo_height()))
        restart = sweep_index in (None,100)
        history.record('Sweep','Sweep started' if restart else 'Sweep resumed')
        sweep_frame(0 if restart else sweep_index+1)

    sweep_button = ttk.Button(sweep_row,text='Start noise sweep',command=toggle_sweep)
    sweep_button.pack(side='left',padx=(0,12))
    ttk.Label(sweep_row,textvariable=sweep_status).pack(side='left')
    for var in (theta,phi,p,e,feed):
        var.trace_add('write',clear_sweep)
    lab.bind('<Unmap>',lambda event: stop_sweep())

    def calculate():
        stop_sweep()
        run()

    def comparison_example():
        theta.set('180')
        phi.set('0')
        model_choice.current(0)
        preset(0,.1,action='Try 10% example')

    def select_model(event):
        clear_sweep()
        run(f'Selected {model_choice.get()} errors')

    model_choice.bind('<<ComboboxSelected>>',select_model)
    ttk.Button(comparison,text='Try 10% example',command=comparison_example).pack(side='left',padx=10)
    ttk.Label(comparison,text='Linked = both bits flip together.').pack(side='left')

    for label,command in [('Calculate',calculate),('Ideal',lambda:preset(0,0,action='Ideal')),('Skip correction',lambda:preset(0,0,False,'Skip correction')),('Moderate noise',lambda:preset(.2,.1,action='Moderate noise')),('High noise',lambda:preset(.6,.1,action='High noise')),('Save CSV',export)]:
        ttk.Button(presets,text=label,command=command).pack(side='left',padx=(0,5))
    chart.pack(fill='x')
    result.pack(fill='x',pady=10)
    ttk.Label(frame,text='Ideal gates and measurements. Each bit has the same flip probability e in both models.',font=('Segoe UI',10)).pack(anchor='w',pady=(8,0))
    run('Initial lab settings')
    def close():
        stop_sweep()
        history.record('Session','Simulator closed')
        root.destroy()
        history.db.close()
    root.protocol('WM_DELETE_WINDOW',close)
    chart.bind('<Configure>',lambda event: draw(cache['e'],cache['p'],sum(cache['values'].values())/6) if cache else None)
    root.mainloop()

if __name__ == '__main__':
    if '--test' in sys.argv:
        suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parents[1]/'tests'))
        sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
    else:
        launch()
