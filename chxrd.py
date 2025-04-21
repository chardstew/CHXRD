import tkinter as tk
from tkinter import ttk
import json
import random

# ── LOAD CHORDS FROM FILE ───────────────────────────────────────────────
with open("chords.json", "r") as f:
    CHORDS_RAW = json.load(f)

CHORDS = {k: v[0] if isinstance(v, list) else v for k, v in CHORDS_RAW.items() if isinstance(v, list)}

INTERVALS = {
    "1": 0, "2": 2, "2b": 1, "2M": 2,
    "3b": 3, "3": 4,
    "4": 5, "5d": 6, "5": 7, "5A": 8,
    "6b": 8, "6": 9, "7b": 10, "7": 11,
    "9b": 13, "9": 14, "9#": 15,
    "11b": 16, "11": 17, "11#": 18,
    "13b": 20, "13": 21
}

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
BASES = ["5", "M", "m"]
QUALITIES = ["7", "9", "11", "13"]
EXTENSIONS = ["#11", "b9", "#9"]

selected_root = None
selected_octave = None
selected_base = None
selected_quality = None
selected_extension = None
selected_alterations = []
scientific_mode = False
extension_buttons = []
quality_buttons = []

# ── FUNCTIONS ───────────────────────────────────────────────────────────
def get_midi_number(note, octave):
    return 12 * (octave + 1) + NOTE_NAMES.index(note)

def parse_chord(root, octave, formula):
    root_midi = get_midi_number(root, octave)
    notes = []
    note_names = []
    for sym in formula.split():
        val = INTERVALS.get(sym)
        if val is not None:
            midi_num = root_midi + val
            notes.append(midi_num)
            name = NOTE_NAMES[midi_num % 12]
            note_names.append(name)
    return notes, note_names

def set_root(note):
    global selected_root
    selected_root = note
    refresh_display()

def set_octave(oct):
    global selected_octave
    selected_octave = oct
    refresh_display()

def set_base(base):
    global selected_base, selected_quality, selected_extension, selected_alterations
    selected_base = base
    selected_quality = None
    selected_extension = None
    selected_alterations = []
    refresh_display()

def set_quality(q):
    global selected_quality
    selected_quality = q
    refresh_display()

def set_extension(e):
    global selected_extension
    selected_extension = e
    refresh_display()

def toggle_mode():
    global scientific_mode
    scientific_mode = not scientific_mode
    indicator_color = "#ff0000" if scientific_mode else "#550000"
    indicator.config(bg=indicator_color)
    refresh_display()

def reset_all():
    global selected_root, selected_octave, selected_base, selected_quality, selected_extension
    selected_root = None
    selected_octave = None
    selected_base = None
    selected_quality = None
    selected_extension = None
    refresh_display()

def refresh_display():
    for i, child in enumerate(root_grid.winfo_children()):
        if isinstance(child, tk.Button):
            child.config(state="normal")

    for child in oct_grid.winfo_children():
        child.config(state="normal" if selected_root else "disabled")

    for widget in base_frame.winfo_children():
        widget.config(state="normal" if selected_octave else "disabled", relief="raised")
    for widget in quality_frame.winfo_children():
        widget.config(state="normal" if selected_base else "disabled", relief="raised")
    for widget in extension_frame.winfo_children():
        widget.config(state="normal" if selected_quality else "disabled", relief="raised")

    if selected_base:
        for widget in base_frame.winfo_children():
            if widget.cget("text") == selected_base:
                widget.config(relief="sunken")
    if selected_quality:
        for widget in quality_frame.winfo_children():
            if widget.cget("text") == selected_quality:
                widget.config(relief="sunken")
    if selected_extension:
        for widget in extension_frame.winfo_children():
            if widget.cget("text") == selected_extension:
                widget.config(relief="sunken")

    parts = [selected_base, selected_quality, selected_extension]
    chord_key = "".join([p for p in parts if p])

    selected_path_label.config(
        text=f"Root: {selected_root or '-'}  Octave: {selected_octave if selected_octave is not None else '-'}\nChord Type: {chord_key or '-'}  Mode: {'Scientific' if scientific_mode else 'Basic'}")

    chord_exists = chord_key in CHORDS if not scientific_mode else True

    if selected_root is not None and selected_octave is not None and chord_exists:
        if not scientific_mode and chord_key in CHORDS:
            formula = CHORDS[chord_key]
        elif scientific_mode:
            formula = "1"
            if selected_base == "M":
                formula += " 3 5"
            elif selected_base == "m":
                formula += " 3b 5"
            elif selected_base == "5":
                formula += " 5"
            if selected_quality:
                formula += f" {selected_quality}"
            if selected_extension:
                formula += f" {selected_extension}"
        else:
            formula = None

        if formula:
            midi_notes, note_names = parse_chord(selected_root, selected_octave, formula)
            result_label.config(text=f"""Formula: {formula}\nMIDI Notes: {' '.join(map(str, midi_notes))}\nNote Names: {' '.join(note_names)}\nScientific: {' '.join([NOTE_NAMES[n % 12] + str(n // 12 - 1) for n in midi_notes])}""")
    else:
        result_label.config(text="")

# ── UI ──────────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("CHXRD Chord Explorer")
root.configure(bg="black")
root.option_add("*Font", "Fixedsys 14")

indicator = tk.Label(root, text="", width=2, height=1, bg="#550000")
indicator.grid(row=0, column=0, padx=5, pady=5)
mode_button = tk.Button(root, text="CHXRD Mode", command=toggle_mode, bg="black", fg="red", activebackground="#330000", activeforeground="white")
mode_button.grid(row=0, column=1, padx=5, pady=5)
reset_button = tk.Button(root, text="Reset", command=reset_all, bg="black", fg="red", activebackground="#330000", activeforeground="white")
reset_button.grid(row=0, column=2, padx=5, pady=5)

root_grid = tk.Frame(root, bg="black")
root_grid.grid(row=1, column=0, columnspan=3, pady=5)
for i, note in enumerate(NOTE_NAMES):
    row = 0 if i < 6 else 1
    col = i if i < 6 else i - 6
    btn = tk.Button(root_grid, text=note, width=4, command=lambda n=note: set_root(n), bg="black", fg="red", activebackground="#550000", activeforeground="white")
    btn.grid(row=row, column=col, padx=2, pady=2)

oct_grid = tk.Frame(root, bg="black")
oct_grid.grid(row=2, column=0, columnspan=3, pady=5)
for i in range(10):
    btn = tk.Button(oct_grid, text=str(i), width=4, command=lambda o=i: set_octave(o), bg="black", fg="red", activebackground="#550000", activeforeground="white")
    btn.grid(row=i//5, column=i%5, padx=2, pady=2)

base_frame = tk.Frame(root, bg="black")
base_frame.grid(row=3, column=0, columnspan=3, pady=5)
for item in BASES:
    btn = tk.Button(base_frame, text=item, width=4, command=lambda b=item: set_base(b), bg="black", fg="red", activebackground="#550000", activeforeground="white")
    btn.pack(side="left", padx=2, pady=2)

quality_frame = tk.Frame(root, bg="black")
quality_frame.grid(row=4, column=0, columnspan=3, pady=5)
for item in QUALITIES:
    btn = tk.Button(quality_frame, text=item, width=4, command=lambda q=item: set_quality(q), bg="black", fg="red", activebackground="#550000", activeforeground="white")
    btn.pack(side="left", padx=2, pady=2)

extension_frame = tk.Frame(root, bg="black")
extension_frame.grid(row=5, column=0, columnspan=3, pady=5)
for item in EXTENSIONS:
    btn = tk.Button(extension_frame, text=item, width=4, command=lambda e=item: set_extension(e), bg="black", fg="red", activebackground="#550000", activeforeground="white")
    btn.pack(side="left", padx=2, pady=2)

selected_path_label = tk.Label(root, text="", fg="white", bg="black", justify="left")
selected_path_label.grid(row=6, column=0, columnspan=3, pady=5)

result_label = tk.Label(root, text="", fg="red", bg="black", justify="left")
result_label.grid(row=7, column=0, columnspan=3, pady=10)

refresh_display()
root.mainloop()
