#!/usr/bin/env python3
"""
Photo Renamer GUI
-----------------
Graphical interface for renaming JPG and ARW photo files according to EXIF timestamp.
"""

import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime

from renamer import process_renaming, VALID_EXTENSIONS, get_photo_datetime, generate_target_name

class RenamerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Photo EXIF Renamer (JPG & ARW)")
        self.geometry("750x550")
        self.minsize(650, 450)

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Color Palette
        self.bg_color = "#1e1e2e"
        self.fg_color = "#cdd6f4"
        self.card_bg = "#181825"
        self.accent_color = "#89b4fa"

        self.configure(bg=self.bg_color)
        
        # Variables
        self.selected_dir = tk.StringVar(value=str(Path.cwd()))
        self.dry_run_var = tk.BooleanVar(value=True)
        self.recursive_var = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self):
        # Header
        header_frame = tk.Frame(self, bg=self.bg_color, pady=15)
        header_frame.pack(fill=tk.X, padx=20)
        
        title_label = tk.Label(
            header_frame, 
            text="📷 Photo EXIF Renamer", 
            font=("Segoe UI", 16, "bold"), 
            bg=self.bg_color, 
            fg=self.accent_color
        )
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(
            header_frame, 
            text="Standardize JPG & ARW filenames to YYYY-MM-DD-unixtimestamp", 
            font=("Segoe UI", 10), 
            bg=self.bg_color, 
            fg="#a6adc8"
        )
        subtitle_label.pack(anchor="w")

        # Controls Container
        ctrl_frame = tk.LabelFrame(
            self, 
            text=" Folder & Options ", 
            font=("Segoe UI", 10, "bold"),
            bg=self.card_bg, 
            fg=self.fg_color, 
            bd=1, 
            relief=tk.SOLID, 
            padx=15, 
            pady=15
        )
        ctrl_frame.pack(fill=tk.X, padx=20, pady=5)

        # Directory selector
        dir_label = tk.Label(ctrl_frame, text="Target Folder:", bg=self.card_bg, fg=self.fg_color, font=("Segoe UI", 9))
        dir_label.grid(row=0, column=0, sticky="w", pady=5)

        dir_entry = tk.Entry(ctrl_frame, textvariable=self.selected_dir, font=("Segoe UI", 9), bg="#313244", fg="#cdd6f4", insertbackground="white")
        dir_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

        browse_btn = tk.Button(
            ctrl_frame, 
            text="Browse...", 
            command=self._browse_directory,
            bg="#45475a", 
            fg="white", 
            activebackground="#585b70", 
            activeforeground="white",
            relief=tk.FLAT,
            padx=10
        )
        browse_btn.grid(row=0, column=2, pady=5)

        ctrl_frame.columnconfigure(1, weight=1)

        # Options checkbuttons
        opts_frame = tk.Frame(ctrl_frame, bg=self.card_bg)
        opts_frame.grid(row=1, column=0, columnspan=3, sticky="w", pady=10)

        dry_chk = tk.Checkbutton(
            opts_frame, 
            text="Dry Run (Preview changes without renaming)", 
            variable=self.dry_run_var, 
            bg=self.card_bg, 
            fg=self.fg_color, 
            selectcolor="#313244", 
            activebackground=self.card_bg, 
            activeforeground=self.fg_color,
            font=("Segoe UI", 9)
        )
        dry_chk.pack(side=tk.LEFT, padx=(0, 20))

        rec_chk = tk.Checkbutton(
            opts_frame, 
            text="Include Subdirectories", 
            variable=self.recursive_var, 
            bg=self.card_bg, 
            fg=self.fg_color, 
            selectcolor="#313244", 
            activebackground=self.card_bg, 
            activeforeground=self.fg_color,
            font=("Segoe UI", 9)
        )
        rec_chk.pack(side=tk.LEFT)

        # Action Buttons
        btn_frame = tk.Frame(self, bg=self.bg_color, pady=10)
        btn_frame.pack(fill=tk.X, padx=20)

        preview_btn = tk.Button(
            btn_frame, 
            text="🔍 Preview (Dry Run)", 
            command=lambda: self._run_renamer(force_dry_run=True),
            bg="#313244", 
            fg=self.accent_color, 
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=15, 
            pady=8
        )
        preview_btn.pack(side=tk.LEFT, padx=(0, 10))

        execute_btn = tk.Button(
            btn_frame, 
            text="🚀 Execute Rename", 
            command=lambda: self._run_renamer(force_dry_run=False),
            bg="#a6e3a1", 
            fg="#11111b", 
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=15, 
            pady=8
        )
        execute_btn.pack(side=tk.LEFT)

        # Output Log Box
        log_frame = tk.LabelFrame(
            self, 
            text=" Activity Log ", 
            font=("Segoe UI", 10, "bold"),
            bg=self.card_bg, 
            fg=self.fg_color, 
            bd=1, 
            relief=tk.SOLID, 
            padx=10, 
            pady=10
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 20))

        self.log_text = tk.Text(
            log_frame, 
            bg="#11111b", 
            fg="#a6adc8", 
            font=("Consolas", 9), 
            wrap=tk.WORD, 
            relief=tk.FLAT
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview, bg="#181825")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def _browse_directory(self):
        dir_path = filedialog.askdirectory(initialdir=self.selected_dir.get())
        if dir_path:
            self.selected_dir.set(dir_path)

    def _log(self, message: str):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _run_renamer(self, force_dry_run: bool | None = None):
        target_dir = Path(self.selected_dir.get()).resolve()
        if not target_dir.exists() or not target_dir.is_dir():
            messagebox.showerror("Invalid Directory", f"The directory '{target_dir}' does not exist.")
            return

        dry_run = force_dry_run if force_dry_run is not None else self.dry_run_var.get()
        recursive = self.recursive_var.get()

        if not dry_run:
            confirm = messagebox.askyesno(
                "Confirm Renaming", 
                f"Are you sure you want to rename files in:\n{target_dir}\n\nThis action will alter filenames on disk."
            )
            if not confirm:
                return

        self.log_text.delete("1.0", tk.END)
        self._log(f"Processing folder: {target_dir}")
        self._log(f"Mode: {'DRY RUN (Preview Only)' if dry_run else 'ACTUAL RENAME'}\n")

        # Custom stdout capture for log window
        class LogStream:
            def __init__(gui, log_func):
                gui.log_func = log_func
            def write(gui, text):
                if text.strip():
                    gui.log_func(text.rstrip())
            def flush(gui):
                pass

        sys.stdout = LogStream(self._log)
        try:
            process_renaming(directory=target_dir, dry_run=dry_run, recursive=recursive, verbose=True)
        finally:
            sys.stdout = sys.__stdout__

if __name__ == "__main__":
    app = RenamerGUI()
    app.mainloop()
