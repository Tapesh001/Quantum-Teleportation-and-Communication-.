"""Local activity journal and paginated reader."""
from datetime import datetime
import os
from pathlib import Path
import sqlite3
import tkinter as tk
from tkinter import ttk


class History(ttk.Frame):
    PAGE_SIZE = 50

    def __init__(self, parent):
        super().__init__(parent, padding=14)
        path = Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'QuantumTeleportation' / 'history.sqlite3'
        schema = 'CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, stamp TEXT, area TEXT, title TEXT, detail TEXT)'
        self.warning = ''
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(path)
            self.db.execute(schema)
        except (OSError, sqlite3.Error) as exc:
            self.warning = f'History is available for this session only. {exc}'
            self.db = sqlite3.connect(':memory:')
            self.db.execute(schema)
        self.page = 0
        ttk.Label(self,text='Activity history',font=('Segoe UI',20,'bold')).pack(anchor='w')
        self.notice = ttk.Label(self,text=self.warning or 'Select an entry to see its settings and results.')
        self.notice.pack(anchor='w',pady=4)
        bar = ttk.Frame(self)
        bar.pack(fill='x',pady=4)
        self.filter = ttk.Combobox(bar,values=('All activity','Lab','Sweep','Export','Session'),
                                   state='readonly',width=16)
        self.filter.current(0)
        self.filter.pack(side='left')
        self.filter.bind('<<ComboboxSelected>>',lambda event:self.load(0))
        self.older = ttk.Button(bar,text='Older',command=lambda:self.load(self.page+1))
        self.newer = ttk.Button(bar,text='Newer',command=lambda:self.load(self.page-1))
        for button in (self.older,self.newer):
            button.pack(side='right',padx=3)
        self.count = ttk.Label(bar)
        self.count.pack(side='right',padx=8)
        listing = ttk.Frame(self)
        listing.pack(fill='both',expand=True)
        self.rows = ttk.Treeview(listing,columns=('time','area','activity'),show='headings',height=7,selectmode='browse')
        for col,title,width in [('time','Local time',160),('area','Section',105),('activity','Activity',375)]:
            self.rows.heading(col,text=title)
            self.rows.column(col,width=width,stretch=(col=='activity'))
        self._scroll(listing,self.rows)
        self.rows.bind('<<TreeviewSelect>>',lambda event:self.show_detail())
        box = ttk.Frame(self)
        box.pack(fill='both',expand=True,pady=(8,0))
        self.details = tk.Text(box,height=8,wrap='word',bg='#102538',fg='#e9f4fa',
                               font=('Consolas',10),padx=10,pady=8,state='disabled')
        self._scroll(box,self.details)
        self.bind('<Map>',lambda event:self.load(0))

    @staticmethod
    def _scroll(frame,widget):
        scroll = ttk.Scrollbar(frame,orient='vertical',command=widget.yview)
        widget.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y')
        widget.pack(fill='both',expand=True)

    def record(self,area,title,detail=''):
        stamp = datetime.now().astimezone().isoformat(sep=' ',timespec='seconds')
        try:
            with self.db:
                self.db.execute('INSERT INTO events(stamp,area,title,detail) VALUES(?,?,?,?)',(stamp,area,title,detail))
        except sqlite3.Error as exc:
            self.notice.configure(text=f'Could not save the latest history entry. {exc}')

    def load(self,page):
        where,params = ('',()) if self.filter.current()==0 else (' WHERE area=?',(self.filter.get(),))
        total = self.db.execute('SELECT COUNT(*) FROM events'+where,params).fetchone()[0]
        last = max(0,(total-1)//self.PAGE_SIZE)
        self.page = max(0,min(last,page))
        start = self.page*self.PAGE_SIZE
        records = self.db.execute('SELECT id,stamp,area,title FROM events'+where+
                                  ' ORDER BY id DESC LIMIT ? OFFSET ?',params+(self.PAGE_SIZE,start))
        self.rows.delete(*self.rows.get_children())
        for key,stamp,area,title in records:
            self.rows.insert('','end',iid=str(key),values=(stamp[:19],area,title))
        self.count.configure(text=f'{start+1}–{min(start+self.PAGE_SIZE,total)} of {total}' if total else 'No entries')
        self.older.configure(state='normal' if self.page<last else 'disabled')
        self.newer.configure(state='normal' if self.page else 'disabled')
        children=self.rows.get_children()
        if children:
            self.rows.selection_set(children[0])
        self.show_detail()

    def show_detail(self):
        selection=self.rows.selection()
        text=''
        if selection:
            stamp,title,detail=self.db.execute('SELECT stamp,title,detail FROM events WHERE id=?',selection).fetchone()
            text=f'{title}\n{stamp}\n\n{detail}'
        self.details.configure(state='normal')
        self.details.delete('1.0','end')
        self.details.insert('1.0',text)
        self.details.configure(state='disabled')

