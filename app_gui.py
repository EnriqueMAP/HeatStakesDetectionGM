import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import sys

# Importamos tu lógica existente
from src.geometry import GeometryProcessor
from src.analyzer import HeatStakeAnalyzer
from src.visualizer import ResultVisualizer
from src.family_merger import FamilyMerger

class HeatStakeLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Heat Stakes Detector - Launcher")
        self.root.geometry("500x420") # Un poco más alto para la barra
        self.root.resizable(False, False)
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # --- Variables ---
        self.file_path = tk.StringVar()
        self.view_3d = tk.BooleanVar(value=True)
        self.show_rejected = tk.BooleanVar(value=False)
        self.custom_rules = tk.BooleanVar(value=True)
        self.eps_val = tk.DoubleVar(value=15.0)

        # --- UI Layout ---
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        lbl_title = ttk.Label(main_frame, text="Detector de Heat Stakes GM", font=("Helvetica", 16, "bold"))
        lbl_title.pack(pady=(0, 20))

        # Selección de Archivo
        file_frame = ttk.LabelFrame(main_frame, text="1. Archivo STEP", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        self.lbl_file = ttk.Label(file_frame, text="Ningún archivo seleccionado", foreground="gray")
        self.lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        btn_browse = ttk.Button(file_frame, text="📂 Buscar...", command=self.browse_file)
        btn_browse.pack(side=tk.RIGHT)

        # Opciones
        opts_frame = ttk.LabelFrame(main_frame, text="2. Configuración", padding="10")
        opts_frame.pack(fill=tk.X, pady=10)
        
        ttk.Checkbutton(opts_frame, text="Visualización 3D Interactiva", variable=self.view_3d).pack(anchor="w")
        ttk.Checkbutton(opts_frame, text="Mostrar Candidatos Rechazados", variable=self.show_rejected).pack(anchor="w")
        ttk.Checkbutton(opts_frame, text="Usar Reglas de Fusión Personalizadas", variable=self.custom_rules).pack(anchor="w")
        
        # Botón de Acción
        self.btn_run = ttk.Button(main_frame, text="🚀 INICIAR ANÁLISIS", command=self.start_analysis_thread)
        self.btn_run.pack(fill=tk.X, pady=(20, 10))
        
        # Barra de Progreso (Inicialmente oculta)
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='indeterminate')
        
        # Barra de estado
        self.status_var = tk.StringVar(value="Listo.")
        lbl_status = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        lbl_status.pack(side=tk.BOTTOM, fill=tk.X)

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo STEP",
            filetypes=[("Archivos STEP", "*.stp *.step"), ("Todos los archivos", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
            self.lbl_file.config(text=os.path.basename(filename), foreground="black")

    def start_analysis_thread(self):
        """Prepara la UI y lanza el hilo de procesamiento"""
        step_file = self.file_path.get()
        if not step_file:
            messagebox.showwarning("Atención", "Por favor selecciona un archivo .stp primero.")
            return

        # UI en modo "Cargando"
        self.btn_run.config(state="disabled")
        self.progress.pack(fill=tk.X, pady=5) # Mostrar barra
        self.progress.start(10) # Iniciar animación
        self.status_var.set("⏳ Procesando geometría... (Esto puede tardar unos segundos)")
        
        # Ejecutar lógica pesada en otro hilo para no congelar la ventana
        threading.Thread(target=self.process_logic_background, args=(step_file,), daemon=True).start()

    def process_logic_background(self, file_path):
        """Lógica pesada que corre en segundo plano"""
        try:
            # 1. Geometría
            geo = GeometryProcessor(file_path)
            geo.load_step()
            cylinders = geo.extract_features_topology()

            # 2. Análisis
            analyzer = HeatStakeAnalyzer()
            topo_stakes, remaining = analyzer.analyze_topology(cylinders)
            cluster_stakes, rejected = analyzer.analyze_clusters_legacy(remaining, eps=self.eps_val.get())
            
            all_valid_stakes = topo_stakes + cluster_stakes

            # 3. Fusión
            if self.custom_rules.get():
                merger = FamilyMerger()
                by_fam = {}
                for s in all_valid_stakes:
                    fam = s.get('family_id', 'DEFAULT')
                    if fam not in by_fam: by_fam[fam] = []
                    by_fam[fam].append(s)
                
                all_valid_stakes = merger.merge_all_families(by_fam)

            # Exportar reporte
            output_file = "reporte_deteccion.txt"
            
            # --- VOLVER AL HILO PRINCIPAL ---
            # No podemos tocar la GUI (Visualizador) desde este hilo secundario.
            # Usamos root.after para programar la visualización en el hilo principal.
            self.root.after(0, lambda: self.on_processing_finished(geo, all_valid_stakes, rejected, output_file))

        except Exception as e:
            self.root.after(0, lambda: self.on_error(str(e)))

    def on_processing_finished(self, geo, valid_stakes, rejected, output_file):
        """Se ejecuta en el hilo principal cuando termina el cálculo"""
        # Detener animación
        self.progress.stop()
        self.progress.pack_forget() # Ocultar barra
        self.btn_run.config(state="normal")
        self.status_var.set(f"✅ Listo. Detectados: {len(valid_stakes)}")

        # Abrir Visualizador
        if self.view_3d.get():
            self.root.withdraw() # Ocultar Launcher
            
            try:
                # Instanciar y exportar
                viz = ResultVisualizer(geo.shape, valid_stakes, rejected)
                viz.export_report(output_file)
                
                # Mostrar ventana 3D (Bloqueante hasta que se cierra)
                viz.show_3d(show_rejected=self.show_rejected.get())
            except SystemExit:
                pass # Capturar si visualizer lanza sys.exit()
            except Exception as e:
                messagebox.showerror("Error Visualización", str(e))
            finally:
                # --- REAPARECER LAUNCHER ---
                self.root.deiconify() 
                self.status_var.set("Esperando nueva orden.")

    def on_error(self, error_msg):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn_run.config(state="normal")
        self.status_var.set("Error.")
        messagebox.showerror("Error", f"Ocurrió un error:\n{error_msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HeatStakeLauncher(root)
    root.mainloop()