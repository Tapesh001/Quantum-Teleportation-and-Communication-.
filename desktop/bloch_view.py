"""Single-qubit Bloch spheres with a rotating camera for Bob's output."""
import math
import tkinter as tk
import time


def pure_vector(amplitudes):
    a, b = amplitudes
    coherence = complex(a).conjugate() * b
    return 2 * coherence.real, 2 * coherence.imag, abs(a)**2 - abs(b)**2


class BlochPair(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, height=260, bg="#0d2131", highlightthickness=0)
        self.states = None
        self.angle = 0.0
        self.rotating = True
        self.timer = None
        self.last_tick = None
        self.bind("<Configure>", self.draw)
        self.bind("<Map>", self.start_rotation)
        self.bind("<Unmap>", self.stop_rotation)
        self.bind("<Destroy>", self.stop_rotation)
        self.bind("<Button-1>", self.toggle_view)

    def start_rotation(self, event=None):
        if self.rotating and self.timer is None and self.winfo_ismapped():
            self.last_tick = time.monotonic()
            self.timer = self.after(50, self.rotate)

    def stop_rotation(self, event=None):
        if self.timer is not None:
            self.after_cancel(self.timer)
            self.timer = None

    def rotate(self):
        self.timer = None
        now = time.monotonic()
        self.angle = (self.angle + (now - self.last_tick)*math.tau/22) % math.tau
        self.draw()
        self.start_rotation()

    def toggle_view(self, event):
        if event.x < self.winfo_width()/2:
            return
        self.rotating = not self.rotating
        self.stop_rotation()
        self.angle = 0.0
        self.draw()
        self.start_rotation()

    def show(self, original, output, caption):
        states = (original, output, caption)
        if states != self.states:
            self.states = states
            self.draw()

    def draw(self, event=None):
        w, h = self.winfo_width(), self.winfo_height()
        if self.states is None or min(w, h) < 40:
            return
        self.delete("all")
        original, output, caption = self.states
        self.create_line(w/2, 12, w/2, h-12, fill="#29495b")
        self.sphere(w*.25, h, original, "Alice’s original input · reference",
                    "Saved direction of the prepared state", "#55e2c7")
        action = "Rotating · click to align" if self.rotating else "Aligned · click to rotate"
        self.sphere(w*.75, h, output, f"Bob’s state  |  {action}", caption, "#ffd18a", bob=True)

    def sphere(self, cx, h, state, title, caption, color, bob=False):
        # Reserve space for the title and coordinates before fitting the globe.
        cy = (h + 24)/2
        r = max(10,min((h-114)/2, self.winfo_width()/4-35))
        large = r >= 95
        azimuth = math.atan2(.6,.8) + (self.angle if bob else 0)
        sin_a, cos_a = math.sin(azimuth), math.cos(azimuth)
        elevation_cos = math.sqrt(1-.35**2)
        def project(x, y, z):
            return (cx+r*(-sin_a*x+cos_a*y),
                    cy+r*(.35*(cos_a*x+sin_a*y)-elevation_cos*z))

        def text(x, y, value, size=10, tint="#c2d3dd", weight="normal"):
            self.create_text(x, y, text=value, fill=tint, font=("Segoe UI",size,weight))

        text(cx, 18, title, 13, color, "bold")
        text(cx, 41, caption)
        self.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#102b3d", outline="#9bb8c8", width=2,tags='globe')
        for plane in ("xy","xz","yz"):
            points = []
            for n in range(73):
                angle = n * math.tau / 72
                a,b = math.cos(angle), math.sin(angle)
                coord = (a,b,0) if plane=="xy" else ((a,0,b) if plane=="xz" else (0,a,b))
                points.extend(project(*coord))
            self.create_line(*points, fill="#5c7e91", width=2 if large else 1)
        for axis, direction in (("x",(1,0,0)), ("y",(0,1,0)), ("z",(0,0,1))):
            end = project(*direction)
            self.create_line(cx,cy,*end,fill="#658394",dash=(3,3))
            if not bob:
                tx,ty = project(*(1.13*v for v in direction))
                if axis == "z":
                    tx,ty = end[0]+16,end[1]
                text(tx, ty, axis.upper(), 12 if large else 9, "#e3f0f6","bold")
        if bob:
            poles = (("+X",(1,0,0)), ("−X",(-1,0,0)), ("+Y",(0,1,0)),
                     ("−Y",(0,-1,0)), ("+Z",(0,0,1)), ("−Z",(0,0,-1)))
            def depth(pole):
                x,y,z = pole[1]
                return elevation_cos*(cos_a*x+sin_a*y) + .35*z
            for name,direction in sorted(poles,key=depth):
                px,py = project(*direction)
                near = depth((name,direction)) >= 0
                tint = "#e3f5fa" if near else "#a6c3d2"
                marker = 5 if large else 3
                self.create_oval(px-marker,py-marker,px+marker,py+marker,outline=tint,
                                 fill=tint if near else "#102b3d",tags="bob_axis_point")
                if direction[2]:
                    text(px+(23 if large else 14),py,name,12 if large else 8,tint,"bold")
                else:
                    offset = 18 if large else 10
                    text(px+(offset if px>=cx else -offset),py+(9 if py>=cy else -9),name,12 if large else 8,tint,"bold")
        if state is None:
            text(cx, h-18, "Awaiting shared pair")
            return
        endx,endy = project(*state)
        length = math.sqrt(sum(v*v for v in state))
        if length > 1e-7:
            self.create_line(cx,cy,endx,endy,fill=color,width=5 if large else 4,arrow="last",arrowshape=(12,15,6))
        dot = 7 if large else 4
        self.create_oval(endx-dot,endy-dot,endx+dot,endy+dot,fill=color,outline=color)
        coords = ", ".join(f"{v if abs(v) >= .0005 else 0:.3f}" for v in state)
        text(cx, h-18, f"(x, y, z) = ({coords})    |r| = {length:.3f}", 10, color)
