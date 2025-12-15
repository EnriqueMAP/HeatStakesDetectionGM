import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import os
import sys

class HeatStakeLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Launcher GM - Heat Stakes")
        self.root.geometry("500x420")
        self.root.resizable(False, False)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Variables
        self.file_path = tk.StringVar()
        self.view_3d = tk.BooleanVar(value=True)
        self.show_rejected = tk.BooleanVar(value=False)
        self.custom_rules = tk.BooleanVar(value=True)

        # UI Layout
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Detector de Heat Stakes GM", font=("Arial", 16, "bold")).pack(pady=(0, 20))

        # Archivo
        file_frame = ttk.LabelFrame(main_frame, text="1. Archivo STEP", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        self.lbl_file = ttk.Label(file_frame, text="Sin archivo...", foreground="gray")
        self.lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="📂 Buscar", command=self.browse_file).pack(side=tk.RIGHT)

        # Opciones
        opts_frame = ttk.LabelFrame(main_frame, text="2. Configuración", padding="10")
        opts_frame.pack(fill=tk.X, pady=10)
        ttk.Checkbutton(opts_frame, text="Ver en 3D", variable=self.view_3d).pack(anchor="w")
        ttk.Checkbutton(opts_frame, text="Ver Rechazados (Debug)", variable=self.show_rejected).pack(anchor="w")
        ttk.Checkbutton(opts_frame, text="Fusión de Familias", variable=self.custom_rules).pack(anchor="w")
        
        # Botón Run
        self.btn_run = ttk.Button(main_frame, text="🚀 EJECUTAR", command=self.run_process)
        self.btn_run.pack(fill=tk.X, pady=15)
        
        # Progreso
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='indeterminate')
        self.status_var = tk.StringVar(value="Listo.")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN).pack(side=tk.BOTTOM, fill=tk.X)

    def browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("STEP", "*.stp *.step")])
        if f:
            self.file_path.set(f)
            self.lbl_file.config(text=os.path.basename(f), foreground="black")

    def run_process(self):
        if not self.file_path.get():
            messagebox.showwarning("!", "Selecciona un archivo.")
            return

        self.btn_run.config(state="disabled")
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start(10)
        self.status_var.set("⏳ Procesando... (Revisa la consola para logs)")
        
        # Ejecutar en hilo
        threading.Thread(target=self._execute_subprocess, daemon=True).start()

    def _execute_subprocess(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "run_process.py")
        
        if not os.path.exists(script_path):
            self.root.after(0, lambda: self._on_finish(1, f"Falta run_process.py en {current_dir}"))
            return

        cmd = [sys.executable, script_path, self.file_path.get()]
        if self.view_3d.get(): cmd.append("--view")
        if self.show_rejected.get(): cmd.append("--show-rejected")
        if self.custom_rules.get(): cmd.append("--custom-rules")

        # CONFIGURACIÓN DE CONSOLA:
        # En Windows: CREATE_NEW_CONSOLE (0x10) abre una ventana negra nueva con los logs.
        # En Linux: Se mostrará en la terminal donde lanzaste el app_gui.py.
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = 0x00000010 # CREATE_NEW_CONSOLE

        try:
            # IMPORTANTE: Hemos quitado stdout=PIPE y stderr=PIPE.
            # Ahora los logs van directo a la consola del usuario.
            process = subprocess.Popen(
                cmd, 
                text=True, 
                creationflags=creation_flags
            )
            
            # Esperamos a que el proceso termine
            process.wait()
            
            # Volver al hilo principal
            self.root.after(0, lambda: self._on_finish(process.returncode, None))
        except Exception as e:
            self.root.after(0, lambda: self._on_finish(1, str(e)))

    def _on_finish(self, code, error_msg):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn_run.config(state="normal")
        
        if code == 0:
            self.status_var.set("✅ Finalizado.")
        else:
            self.status_var.set("❌ Error.")
            if error_msg:
                messagebox.showerror("Error", f"Fallo en el proceso:\n{error_msg}")
            else:
                messagebox.showwarning("Aviso", "El proceso se cerró con errores (Revisa la consola).")

if __name__ == "__main__":
    root = tk.Tk()
    app = HeatStakeLauncher(root)
    root.mainloop()