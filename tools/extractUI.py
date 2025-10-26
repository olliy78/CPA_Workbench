#!/usr/bin/env python3
"""
extractUI.py
GUI-Frontend für extract_files.py-Funktionalität mit moderner tkinter/ttk-Oberfläche.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import sys
import os
from pathlib import Path

def run_extract(format_val, file_path, diskname, mode):
    # Baue den Befehl
    script = os.path.join(os.path.dirname(__file__), 'extract_files.py')
    cmd = [sys.executable, script]
    if format_val:
        cmd += ['-t', format_val]
    if mode == 'file' and file_path:
        cmd += ['-f', file_path]
    elif mode == 'gw' and diskname:
        cmd += ['-g', diskname]
    else:
        return False, 'Bitte Datei oder Diskettenname angeben.'
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, proc.stdout + proc.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout + e.stderr

def show_help():
    messagebox.showinfo('Hilfe',
        'Dieses Tool extrahiert alle Dateien aus einem CP/M-Disketten-Image oder von Diskette (Greaseweazle) in einen neuen Ordner unterhalb von Disketten/.\n\n'
        '1. Wähle ein Image (Datei) ODER gib einen Diskettennamen für Greaseweazle ein.\n'
        '2. Wähle das Format (z.B. cpa800, cpa780).\n'
        '3. Klicke auf "Ausführen".\n\n'
        'Das Zielverzeichnis wird automatisch angelegt. Temporäre Images werden nach der Extraktion gelöscht.'
    )

def main():
    root = tk.Tk()
    root.title('CP/M Disketten-Extraktor')
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('TButton', font=('Segoe UI', 11))
    style.configure('TLabel', font=('Segoe UI', 11))
    style.configure('TEntry', font=('Segoe UI', 11))
    style.configure('TCombobox', font=('Segoe UI', 11))
    root.geometry('640x400')
    root.resizable(False, False)

    frm = ttk.Frame(root, padding=24)
    frm.pack(fill='both', expand=True)

    # Format-Auswahl
    ttk.Label(frm, text='Format:').grid(row=0, column=0, sticky='e', pady=5)
    format_var = tk.StringVar(value='cpa800')
    format_box = ttk.Combobox(frm, textvariable=format_var, values=['cpa800', 'cpa780'], state='readonly', width=18)
    format_box.grid(row=0, column=1, sticky='w', pady=5, columnspan=2)

    # Dateiauswahl
    file_var = tk.StringVar()
    def choose_file():
        path = filedialog.askopenfilename(title='Image-Datei auswählen', filetypes=[('Disk-Images', '*.img *.hfe *.scp *.bin *.raw'), ('Alle Dateien', '*.*')])
        if path:
            file_var.set(path)
            diskname_var.set('')
    ttk.Label(frm, text='Image-Datei:').grid(row=1, column=0, sticky='e', pady=5)
    file_entry = ttk.Entry(frm, textvariable=file_var, width=40)
    file_entry.grid(row=1, column=1, sticky='w', pady=5)
    ttk.Button(frm, text='Durchsuchen...', command=choose_file).grid(row=1, column=2, padx=5)

    # Diskettenname
    diskname_var = tk.StringVar()
    def on_diskname_entry(*_):
        if diskname_var.get():
            file_var.set('')
    ttk.Label(frm, text='Diskettenname:').grid(row=2, column=0, sticky='e', pady=5)
    disk_entry = ttk.Entry(frm, textvariable=diskname_var, width=40)
    disk_entry.grid(row=2, column=1, sticky='w', pady=5, columnspan=2)
    diskname_var.trace_add('write', on_diskname_entry)

    # Status-Ausgabe
    status = tk.Text(frm, height=10, width=72, font=('Consolas', 10), state='disabled', wrap='word')
    status.grid(row=4, column=0, columnspan=3, pady=(18, 0))

    def set_status(msg, error=False):
        status.config(state='normal')
        status.delete('1.0', 'end')
        status.insert('end', msg)
        if error:
            status.tag_configure('err', foreground='red')
            status.insert('end', '\n', 'err')
        status.config(state='disabled')

    # Ausführen-Button
    def on_run():
        file_path = file_var.get().strip()
        diskname = diskname_var.get().strip()
        format_val = format_var.get().strip()
        if file_path:
            mode = 'file'
        elif diskname:
            mode = 'gw'
        else:
            set_status('Bitte eine Image-Datei auswählen oder einen Diskettennamen angeben.', error=True)
            return
        set_status('Extrahiere Dateien... Bitte warten.')
        root.update()
        ok, out = run_extract(format_val, file_path, diskname, mode)
        set_status(out, error=not ok)

    # Buttons
    btn_frame = ttk.Frame(frm)
    btn_frame.grid(row=5, column=0, columnspan=3, pady=18)
    ttk.Button(btn_frame, text='Hilfe', command=show_help).pack(side='left', padx=8)
    ttk.Button(btn_frame, text='Ausführen', command=on_run).pack(side='left', padx=8)
    ttk.Button(btn_frame, text='Schließen', command=root.destroy).pack(side='left', padx=8)

    root.mainloop()

if __name__ == '__main__':
    main()
