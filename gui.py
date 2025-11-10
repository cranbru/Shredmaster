import os, threading, queue, tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from core import ShredMasterCore
from utils import setup_logger, FileValidator, SettingsManager


class ShredMasterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🛡️ ShredMaster - Secure File Shredder")
        self.geometry("900x700"); self.configure(bg="#1e1e1e")
        self.style = ttk.Style(); self.style.theme_use('clam')
        self._style_dark()
        self.log_queue = queue.Queue()
        self.logger = setup_logger(self.log_queue)
        self.core = ShredMasterCore(self.logger)
        self.cancel_flag = False
        self.settings = SettingsManager.load()
        self._init_vars()
        self._create_ui()
        self.after(100, self._poll_log)

    def _style_dark(self):
        s = self.style
        s.configure(".", background="#1e1e1e", foreground="#fff", fieldbackground="#333")
        s.configure("TButton", background="#0078d7", foreground="#fff", padding=6)
        s.map("TButton", background=[('active','#1e90ff')])

    def _init_vars(self):
        s = self.settings
        self.mode = tk.StringVar(value=s.get("mode","file"))
        self.algorithm = tk.StringVar(value=s.get("algorithm","simple"))
        self.dry_run = tk.BooleanVar(value=s.get("dry_run",False))
        self.secure_rename = tk.BooleanVar(value=s.get("secure_rename",False))
        self.threads = tk.IntVar(value=s.get("threads",4))
        self.custom_pattern = tk.StringVar(value=s.get("custom_pattern","00,FF,RANDOM"))
        self.custom_passes = tk.IntVar(value=s.get("custom_passes",3))
        self.log_file = tk.StringVar(value=s.get("log_file",""))
        self.selected_files=[]; self.selected_dir=tk.StringVar()

    def _create_ui(self):
        frm = ttk.Frame(self, padding=10); frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text="🛡️ ShredMaster", font=("Segoe UI",16,"bold")).pack(pady=5)
        self._file_frame(frm); self._right_settings(frm); self._log_frame(frm)
        self.status = ttk.Label(frm, text="Ready"); self.status.pack(side=tk.BOTTOM, anchor=tk.W, pady=5)

    def _file_frame(self, parent):
        lf = ttk.LabelFrame(parent, text="Files"); lf.pack(fill=tk.BOTH, expand=True, pady=10)
        self.file_list = tk.Listbox(lf, height=8, selectmode=tk.EXTENDED, bg="#333", fg="#fff")
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(lf, command=self.file_list.yview); sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_list.config(yscrollcommand=sb.set)
        btnf = ttk.Frame(lf); btnf.pack(fill=tk.X, pady=5)
        ttk.Button(btnf,text="Add",command=self._add_files).pack(side=tk.LEFT)
        ttk.Button(btnf,text="Remove",command=self._remove_files).pack(side=tk.LEFT,padx=5)
        ttk.Button(btnf,text="Clear",command=self._clear_files).pack(side=tk.LEFT,padx=5)
        ttk.Button(btnf,text="Browse Dir",command=self._browse_dir).pack(side=tk.LEFT,padx=5)
        self.progress = ttk.Progressbar(lf, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X,pady=5)
        ttk.Button(lf, text="Start Shred", command=self._start_shred).pack(side=tk.RIGHT,padx=5)
        ttk.Button(lf, text="Cancel", command=self._cancel).pack(side=tk.RIGHT)

    def _right_settings(self, parent):
        opts = ttk.LabelFrame(parent, text="Options"); opts.pack(fill=tk.X, pady=10)
        for text, val in [("Simple","simple"),("DoD","DoD"),("Gutmann","Gutmann"),("Custom","custom")]:
            ttk.Radiobutton(opts,text=text,variable=self.algorithm,value=val).pack(anchor=tk.W)
        ttk.Checkbutton(opts,text="Dry Run",variable=self.dry_run).pack(anchor=tk.W)
        ttk.Checkbutton(opts,text="Secure Rename",variable=self.secure_rename).pack(anchor=tk.W)
        ttk.Label(opts,text="Threads:").pack(anchor=tk.W); ttk.Spinbox(opts,from_=1,to=32,textvariable=self.threads).pack(anchor=tk.W)
        ttk.Label(opts,text="Custom Pattern:").pack(anchor=tk.W)
        ttk.Entry(opts,textvariable=self.custom_pattern).pack(anchor=tk.W)
        ttk.Label(opts,text="Custom Passes:").pack(anchor=tk.W)
        ttk.Spinbox(opts,from_=1,to=100,textvariable=self.custom_passes).pack(anchor=tk.W)
        ttk.Button(opts,text="Apply Settings",command=self._apply).pack(anchor=tk.E,pady=5)

    def _log_frame(self,parent):
        lf=ttk.LabelFrame(parent,text="Logs"); lf.pack(fill=tk.BOTH,expand=True)
        self.log=scrolledtext.ScrolledText(lf,bg="#111",fg="#0f0",state=tk.DISABLED,height=10)
        self.log.pack(fill=tk.BOTH,expand=True)

    def _poll_log(self):
        try:
            while True:
                msg=self.log_queue.get_nowait()
                self.log.config(state=tk.NORMAL)
                self.log.insert(tk.END,msg+"\n")
                self.log.see(tk.END)
                self.log.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        self.after(200,self._poll_log)

    def _add_files(self):
        fs=filedialog.askopenfilenames()
        for f in fs:
            if f not in self.selected_files:
                self.selected_files.append(f); self.file_list.insert(tk.END,f)

    def _remove_files(self):
        for i in reversed(self.file_list.curselection()):
            del self.selected_files[i]; self.file_list.delete(i)

    def _clear_files(self): self.selected_files.clear(); self.file_list.delete(0,tk.END)

    def _browse_dir(self):
        d=filedialog.askdirectory()
        if d: self.selected_dir.set(d); self.selected_files=FileValidator.get_files_in_directory(d)
        self._refresh_files()

    def _refresh_files(self):
        self.file_list.delete(0,tk.END)
        for f in self.selected_files: self.file_list.insert(tk.END,f)

    def _apply(self):
        s=dict(algorithm=self.algorithm.get(),dry_run=self.dry_run.get(),
               secure_rename=self.secure_rename.get(),threads=self.threads.get(),
               custom_pattern=self.custom_pattern.get(),custom_passes=self.custom_passes.get(),
               log_file=self.log_file.get(),mode=self.mode.get())
        self.core.update_settings(s); SettingsManager.save(s)
        self.status.config(text="Settings applied.")

    def _start_shred(self):
        if not self.selected_files:
            messagebox.showwarning("No Files","Select files or directory first."); return
        self.progress["value"]=0; self.progress["maximum"]=len(self.selected_files)
        self._apply()
        threading.Thread(target=self._thread_shred,daemon=True).start()
        self.status.config(text="Shredding in progress...")

    def _thread_shred(self):
        try:
            s,t,e=self.core.shred_files(self.selected_files,self._progress)
            self.after(0,lambda:self._done(s,t,e))
        except Exception as e:
            self.after(0,lambda:messagebox.showerror("Error",str(e)))

    def _progress(self,done,total):
        self.after(0,lambda:self.progress.config(value=done))
        pct=(done/total)*100
        self.after(0,lambda:self.status.config(text=f"{done}/{total} ({pct:.0f}%)"))

    def _done(self,s,t,e):
        self.status.config(text=f"Completed: {s}/{t} in {e:.2f}s")
        messagebox.showinfo("Complete",f"Done! {s}/{t} shredded in {e:.2f}s")

    def _cancel(self):
        self.core.cancel()
        self.status.config(text="Cancelled.")
