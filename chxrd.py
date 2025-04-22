import tkinter as tk
import json

# ── CONFIGURATION ───────────────────────────────────────────────
JSON_FILE = 'chords_fulltext.json'
FONT = 'Fixedsys 18'
BG_COLOR = 'black'
FG_COLOR = 'white'
ACCENT_COLOR = 'red'
SELECT_BG = '#550000'
PAD_X = 14
PAD_Y_TOP = 10
PAD_Y_BOTTOM = 2
BUTTON_WIDTH = 2  # clear dot width
BUFFER_CHARS = 2  # extra character buffer for width

# ── ENHARMONIC MAP ────────────────────────────────────
ENHARMONIC = {
    'C':0,'B#':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,
    'E':4,'Fb':4,'E#':5,'F':5,'F#':6,'Gb':6,
    'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,
    'B':11,'Cb':11
}
PARSING_ROOTS = sorted(ENHARMONIC.keys(), key=lambda x: -len(x))
DISPLAY_ROOTS = sorted(ENHARMONIC.keys(), key=lambda x: x.upper())

# ── LOAD & FLATTEN CHORDS ─────────────────────────────────
with open(JSON_FILE, 'r') as f:
    raw = json.load(f)

CHORDS = {}
NORMALIZE = {
    '7b': 'b7', '13+4': '13', '13#4': '#13', '11#': '#11',
    '9#': '#9', '13#': '#13', '#13': '#13', 'b13': 'b13'
}

def _flatten(x):
    for item in x:
        if isinstance(item, list):
            yield from _flatten(item)
        else:
            yield str(item)

for suffix, val in raw.items():
    tokens = list(_flatten(val)) if isinstance(val, list) else str(val).split()
    cleaned = []
    for tok in tokens:
        norm = NORMALIZE.get(tok, tok)
        if norm not in cleaned:
            cleaned.append(norm)
    CHORDS[suffix] = ' '.join(cleaned)

SUFFIXES = sorted(CHORDS.keys(), key=str.lower)
OPTIONS = [f"{root}{suf}" for root in DISPLAY_ROOTS for suf in SUFFIXES]

realistic_longest_example = "Formula: 1 3 5 b7 9 #11 13".ljust(40)
TOTAL_CHARS = len(realistic_longest_example) + BUFFER_CHARS
ENTRY_WIDTH = TOTAL_CHARS - BUTTON_WIDTH
LIST_WIDTH = TOTAL_CHARS

INTERVALS = {
    '1':0,'2':2,'b2':1,'2b':1,'3b':3,'3':4,'4':5,
    'b5':6,'5':7,'#5':8,'6':9,'b7':10,'7':11,
    'b9':13,'9':14,'#9':15,'11':17,'#11':18,'b13':20,'13':21
}
NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

def get_midi(root, octave=4):
    return 12*(octave+1) + ENHARMONIC[root]

def parse_chord(full):
    full_up = full.upper()
    root = next(r for r in PARSING_ROOTS if full_up.startswith(r.upper()))
    suffix = full[len(root):]
    formula = CHORDS.get(suffix, '')
    notes, names = [], []
    base = get_midi(root)
    seen = set()
    for tok in formula.split():
        val = INTERVALS.get(tok)
        if val is not None and val not in seen:
            seen.add(val)
            midi = base + val
            notes.append(str(midi))
            names.append(NOTE_NAMES[midi % 12])
    return root, suffix, formula, notes, names

root = tk.Tk()
root.title('CHXRD')
root.configure(bg=BG_COLOR)
root.option_add('*Font', FONT)
root.resizable(False, False)

input_frame = tk.Frame(root, bg=BG_COLOR)
input_frame.pack(padx=PAD_X, pady=(PAD_Y_TOP, PAD_Y_BOTTOM), anchor='w')

entry_var = tk.StringVar()
entry = tk.Entry(
    input_frame, textvariable=entry_var,
    bg=BG_COLOR, fg=FG_COLOR,
    insertbackground=FG_COLOR,
    insertwidth=4, width=ENTRY_WIDTH)
entry.pack(side='left')
entry.focus_set()

btn_clear = tk.Button(
    input_frame, text='\u25cf', width=BUTTON_WIDTH,
    command=lambda: (entry_var.set(''), entry.focus_set(), update_list()),
    bg=BG_COLOR, fg=ACCENT_COLOR,
    relief='flat', bd=0)
btn_clear.pack(side='left', padx=(4,0))

listbox = tk.Listbox(
    root, bg=BG_COLOR, fg=ACCENT_COLOR,
    selectbackground=SELECT_BG,
    width=LIST_WIDTH, height=7,
    exportselection=False)
listbox.pack(padx=PAD_X, pady=(0, PAD_Y_BOTTOM))

labels = []
for text in ['Chord:', 'Formula:', 'MIDI:', 'Names:']:
    lbl = tk.Label(root, text=f'{text} ', fg=FG_COLOR, bg=BG_COLOR, anchor='w')
    lbl.pack(padx=PAD_X, anchor='w', pady=(0,2))
    labels.append(lbl)
chord_label, formula_label, midi_label, names_label = labels

def update_list(event=None):
    txt = entry_var.get().strip().lower()
    listbox.delete(0, tk.END)
    if not txt:
        for lbl in labels:
            lbl.config(text=lbl.cget('text').split(':')[0] + ': ')
        return
    matches = [opt for opt in OPTIONS if opt.lower().startswith(txt)]
    for opt in matches:
        listbox.insert(tk.END, opt)
    if matches and matches[0].lower() == txt:
        listbox.selection_set(0)
        listbox.activate(0)
        listbox.see(0)
        show_selection()

def on_key(event):
    if event.keysym in ('Down', 'Up') and listbox.size():
        idx = listbox.curselection()[0] if listbox.curselection() else -1
        new = {'Down': min(listbox.size()-1, idx+1), 'Up': max(0, idx-1)}[event.keysym]
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(new)
        listbox.activate(new)
        listbox.see(new)
        show_selection()
        listbox.focus_set()
        return 'break'

def show_selection(event=None):
    if not listbox.curselection():
        return
    sel = listbox.get(listbox.curselection()[0])
    root_n, suf, formula, notes, names = parse_chord(sel)
    chord_label.config(text=f'Chord: {sel}')
    formula_label.config(text=f'Formula: {formula}')
    midi_label.config(text=f"MIDI: {' '.join(notes)}")
    names_label.config(text=f"Names: {' '.join(names)}")

entry.bind('<KeyRelease>', update_list)
entry.bind('<Down>', on_key)
entry.bind('<Up>', on_key)
listbox.bind('<<ListboxSelect>>', show_selection)

def freeze():
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    root.geometry(f"{w}x{h}")
root.after(100, freeze)
root.mainloop()

