import tkinter as tk
from tkinter import ttk
import json
import random
import time
import mido
from mido import Message

# ── FILES & PERSISTENCE ───────────────────────────────────────────────
FAV_FILE = 'favorites.json'

def load_favorites():
    try:
        with open(FAV_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_favorites():
    with open(FAV_FILE, 'w') as f:
        json.dump(favorites, f, indent=2)

favorites = load_favorites()

# ── TOOLTIP HELPER ──────────────────────────────────────────────────────
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text   = text
        self.tipwin = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        if self.tipwin:
            return
        x = event.x_root + 10
        y = event.y_root + 10
        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text,
                         background="black", foreground="white",
                         font=("Fixedsys", 10), padx=4, pady=2)
        label.pack()
        self.tipwin = tw

    def _hide(self, event=None):
        if self.tipwin:
            self.tipwin.destroy()
            self.tipwin = None

# ── LOAD CHORDS FROM FILE ───────────────────────────────────────────────
with open("chords.json", "r") as f:
    CHORDS_RAW = json.load(f)
CHORDS = {k: v[0] if isinstance(v, list) else v
          for k, v in CHORDS_RAW.items() if isinstance(v, list)}

INTERVALS = {
    "1":0, "2":2, "2b":1, "2M":2,
    "3b":3, "3":4,
    "4":5, "5d":6, "5":7, "5A":8,
    "6b":8, "6":9, "7b":10, "7":11,
    "9b":13, "9":14, "9#":15,
    "11b":16, "11":17, "11#":18,
    "13b":20, "13":21
}

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
BASES = ["5","M","m"]
QUALITIES = ["7","9","11","13"]
EXTENSIONS = ["#11","b9","#9"]

# ── STATE ──────────────────────────────────────────────────────────────
selected_root = None
selected_octave = None
selected_base = None
selected_quality = None
selected_extension = None
scientific_mode = False

# ── MIDI OUTPUT ────────────────────────────────────────────────────────
try:
    port_name = mido.get_output_names()[0]
    midi_port = mido.open_output(port_name)
except Exception:
    midi_port = None

# ── CORE FUNCTIONS ─────────────────────────────────────────────────────
def get_midi_number(note, octave):
    return 12 * (octave + 1) + NOTE_NAMES.index(note)

def parse_chord(root, octave, formula):
    root_midi = get_midi_number(root, octave)
    notes, names = [], []
    for sym in formula.split():
        val = INTERVALS.get(sym)
        if val is not None:
            midi_num = root_midi + val
            notes.append(midi_num)
            names.append(NOTE_NAMES[midi_num % 12])
    return notes, names

# ── FAVORITES ACTIONS ──────────────────────────────────────────────────
def add_favorite():
    if not (selected_root and selected_octave is not None):
        return
    key_parts = [selected_base or '', selected_quality or '', selected_extension or '']
    chord_key = ''.join(p for p in key_parts if p)
    fav = {
        'root': selected_root,
        'octave': selected_octave,
        'base': selected_base,
        'quality': selected_quality,
        'extension': selected_extension
    }
    if fav not in favorites:
        favorites.append(fav)
        save_favorites()

def open_favorites_popup():
    win = tk.Toplevel(root)
    win.title("Favorites")
    for fav in favorites:
        text = f"{fav['root']}{fav['octave']} {fav['base'] or ''}{fav['quality'] or ''}{fav['extension'] or ''}".strip()
        btn = tk.Button(win, text=text,
                        command=lambda f=fav: apply_favorite(f),
                        bg="black", fg="red", activebackground="#330000", activeforeground="white")
        btn.pack(fill='x', padx=5, pady=2)

def apply_favorite(fav):
    set_root(fav['root'])
    set_octave(fav['octave'])
    if fav['base']: set_base(fav['base'])
    if fav['quality']: set_quality(fav['quality'])
    if fav['extension']: set_extension(fav['extension'])

# ── PLAYBACK ───────────────────────────────────────────────────────────
def play_chord():
    bpm = 120
    try:
        bpm = int(bpm_entry.get())
    except ValueError:
        pass
    chord_key = ''.join(p for p in [selected_base or '', selected_quality or '', selected_extension or ''] if p)
    if not (selected_root and selected_octave is not None):
        return
    if not (scientific_mode or chord_key in CHORDS):
        return
    formula = (CHORDS.get(chord_key)
               if not scientific_mode else build_scientific(chord_key))
    midi_notes, _ = parse_chord(selected_root, selected_octave, formula)
    if midi_port:
        dur = 60.0 / bpm
        for n in midi_notes:
            midi_port.send(Message('note_on', note=n, velocity=64))
        time.sleep(dur)
        for n in midi_notes:
            midi_port.send(Message('note_off', note=n, velocity=64))

def build_scientific(chord_key):
    parts = []
    if selected_base == 'M': parts += ['1','3','5']
    elif selected_base == 'm': parts += ['1','3b','5']
    elif selected_base == '5': parts += ['1','5']
    if selected_quality: parts.append(selected_quality)
    if selected_extension: parts.append(selected_extension)
    return ' '.join(parts)

# ── UI ACTIONS ─────────────────────────────────────────────────────────
def set_root(note):
    global selected_root
    selected_root = note
    refresh_display()

def set_octave(oct):
    global selected_octave
    selected_octave = oct
    refresh_display()

def set_base(b):
    global selected_base, selected_quality, selected_extension
    selected_base = b
    selected_quality = None
    selected_extension = None
    refresh_display()

def set_quality(q):
    global selected_quality
    selected_quality = q
    selected_extension = None
    refresh_display()

def set_extension(e):
    global selected_extension
    selected_extension = e
    refresh_display()

def toggle_mode():
    global scientific_mode
    scientific_mode = not scientific_mode
    indicator.config(bg="#ff0000" if scientific_mode else "#550000")
    refresh_display()

def reset_all():
    global selected_root, selected_octave, selected_base, selected_quality, selected_extension
    selected_root = None
    selected_octave = None
    selected_base = None
    selected_quality = None
    selected_extension = None
    refresh_display()

# ── DISPLAY REFRESH ────────────────────────────────────────────────────
def refresh_display():
    # enable/disable grids
    for child in root_grid.winfo_children():
        if isinstance(child, tk.Button): child.config(state="normal")
    for child in oct_grid.winfo_children():
        child.config(state="normal" if selected_root else "disabled")
    for widget in base_frame.winfo_children():
        widget.config(state="normal" if selected_octave is not None else "disabled")
    for widget in quality_frame.winfo_children():
        widget.config(state="normal" if selected_base else "disabled")
    for widget in extension_frame.winfo_children():
        widget.config(state="normal" if selected_quality else "disabled")
    # highlight selections
    for widget in base_frame.winfo_children():
        widget.config(relief="sunken" if widget.cget('text')==selected_base else 'raised')
    for widget in quality_frame.winfo_children():
        widget.config(relief="sunken" if widget.cget('text')==selected_quality else 'raised')
    for widget in extension_frame.winfo_children():
        widget.config(relief="sunken" if widget.cget('text')==selected_extension else 'raised')
    # path label
    parts = [selected_base, selected_quality, selected_extension]
    chord_key = ''.join(p for p in parts if p)
    selected_path_label.config(
        text=f"Root: {selected_root or '-'}  Octave: {selected_octave if selected_octave is not None else '-'}\n"
             f"Chord Type: {chord_key or '-'}  Mode: {'Scientific' if scientific_mode else 'Basic'}")
    # result
    if selected_root and selected_octave is not None and (scientific_mode or chord_key in CHORDS):
        formula = (CHORDS.get(chord_key)
                   if not scientific_mode else build_scientific(chord_key))
        midi_notes, note_names = parse_chord(selected_root, selected_octave, formula)
        sci_names = [f"{NOTE_NAMES[n%12]}{n//12-1}" for n in midi_notes]
        result_label.config(
            text=f"Formula: {formula}\n"
                 f"MIDI Notes: {' '.join(map(str,midi_notes))}\n"
                 f"Note Names: {' '.join(note_names)}\n"
                 f"Scientific: {' '.join(sci_names)}")
    else:
        result_label.config(text="")

# ── BUILD UI ────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("CHXRD Chord Explorer")
root.configure(bg="black")
root.option_add("*Font","Fixedsys 14")

indicator = tk.Label(root, text="", width=2, height=1, bg="#550000")
indicator.grid(row=0, column=0, padx=5, pady=5)
mode_button = tk.Button(root, text="CHXRD Mode", command=toggle_mode,
                        bg="black", fg="red", activebackground="#330000", activeforeground="white")
mode_button.grid(row=0, column=1, padx=5, pady=5)
reset_button = tk.Button(root, text="Reset", command=reset_all,
                         bg="black", fg="red", activebackground="#330000", activeforeground="white")
reset_button.grid(row=0, column=2, padx=5, pady=5)

# root notes
root_grid = tk.Frame(root, bg="black")
root_grid.grid(row=1, column=0, columnspan=3, pady=5)
for i,n in enumerate(NOTE_NAMES):
    r,c = (0,i) if i<6 else (1,i-6)
    btn = tk.Button(root_grid, text=n, width=4, command=lambda x=n: set_root(x),
                    bg="black", fg="red", activebackground="#550000", activeforeground="white")
    btn.grid(row=r, column=c, padx=2, pady=2)

# octave
oct_grid = tk.Frame(root, bg="black")
oct_grid.grid(row=2, column=0, columnspan=3, pady=5)
for i in range(10):
    btn = tk.Button(oct_grid, text=str(i), width=4, command=lambda x=i: set_octave(x),
                    bg="black", fg="red", activebackground="#550000", activeforeground="white")
    btn.grid(row=i//5, column=i%5, padx=2, pady=2)

# bases
base_frame = tk.Frame(root, bg="black")
base_frame.grid(row=3, column=0, columnspan=3, pady=5)
for b in BASES:
    btn = tk.Button(base_frame, text=b, width=4, command=lambda x=b: set_base(x),
                    bg="black", fg="red", activebackground="#330000", activeforeground="white")
    btn.pack(side='left', padx=2, pady=2)

# qualities
quality_frame = tk.Frame(root, bg="black")
quality_frame.grid(row=4, column=0, columnspan=3, pady=5)
for q in QUALITIES:
    btn = tk.Button(quality_frame, text=q, width=4, command=lambda x=q: set_quality(x),
                    bg="black", fg="red", activebackground="#330000", activeforeground="white")
    btn.pack(side='left', padx=2, pady=2)

# extensions
extension_frame = tk.Frame(root, bg="black")
extension_frame.grid(row=5, column=0, columnspan=3, pady=5)
for e in EXTENSIONS:
    btn = tk.Button(extension_frame, text=e, width=4, command=lambda x=e: set_extension(x),
                    bg="black", fg="red", activebackground="#330000", activeforeground="white")
    btn.pack(side='left', padx=2, pady=2)

# status & stars
selected_path_label = tk.Label(root, text="", fg="white", bg="black", justify='left')
selected_path_label.grid(row=6, column=0, columnspan=3, pady=5)
result_label = tk.Label(root, text="", fg="red", bg="black", justify='left')
result_label.grid(row=7, column=0, columnspan=5, pady=5)
stars_frame = tk.Frame(root, bg="black")
stars_frame.grid(row=8, column=0, columnspan=5, pady=(0,10))
add_star = tk.Button(stars_frame, text="☆", width=2, command=add_favorite,
                    bg="black", fg="yellow")
open_star = tk.Button(stars_frame, text="★", width=2, command=open_favorites_popup,
                     bg="black", fg="yellow")
add_star.pack(side='left', padx=8)
open_star.pack(side='left', padx=8)

# playback controls
control_frame = tk.Frame(root, bg='black')
control_frame.grid(row=9, column=0, columnspan=5, pady=5)
BPM_label = tk.Label(control_frame, text='BPM:', fg='white', bg='black')
BPM_label.pack(side='left')
bpm_entry = tk.Entry(control_frame, width=4)
bpm_entry.insert(0, '120')
bpm_entry.pack(side='left', padx=(0,10))
play_button = tk.Button(control_frame, text='Play Chord', command=play_chord,
                        bg='black', fg='red', activebackground='#330000', activeforeground='white')
play_button.pack(side='left')

# tooltips
Tooltip(mode_button,   "Toggle Basic/Scientific mode")
Tooltip(reset_button,  "Reset all selections")
Tooltip(add_star,      "Add chord to favorites")
Tooltip(open_star,     "Open favorites list")
Tooltip(play_button,   "Play the current chord at given BPM")

refresh_display()
root.mainloop()
