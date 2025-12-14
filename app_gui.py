import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os

# Importamos tu lógica existente
from src.geometry import GeometryProcessor
from src.analyzer import HeatStakeAnalyzer
from src.visualizer import ResultVisualizer
from src.family_merger import FamilyMerger

class HeatStakeLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Heat Stakes Detector - Launcher")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # --- Variables ---
        self.file_path = tk.StringVar()
        self.view_3d = tk.BooleanVar(value=True)
        self.show_rejected = tk.BooleanVar(value=False)
        self.custom_rules = tk.BooleanVar(value=False)
        self.eps_val = tk.DoubleVar(value=15.0)

        # --- UI Layout ---
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        lbl_title = ttk.Label(main_frame, text="Detector de Heat Stakes GM", font=("Helvetica", 16, "bold"))
        lbl_title.pack(pady=(0, 20))

        # Selección de Archivo
        file_frame = ttk.LabelFrame(main_frame, text="Archivo STEP", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        self.lbl_file = ttk.Label(file_frame, text="Ningún archivo seleccionado", foreground="gray")
        self.lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        btn_browse = ttk.Button(file_frame, text="📂 Buscar...", command=self.browse_file)
        btn_browse.pack(side=tk.RIGHT)

        # Opciones
        opts_frame = ttk.LabelFrame(main_frame, text="Configuración", padding="10")
        opts_frame.pack(fill=tk.X, pady=10)
        
        ttk.Checkbutton(opts_frame, text="Visualización 3D Interactiva", variable=self.view_3d).pack(anchor="w")
        ttk.Checkbutton(opts_frame, text="Mostrar Candidatos Rechazados", variable=self.show_rejected).pack(anchor="w")
        ttk.Checkbutton(opts_frame, text="Usar Reglas de Fusión Personalizadas", variable=self.custom_rules).pack(anchor="w")
        
        # Botón de Acción
        self.btn_run = ttk.Button(main_frame, text="🚀 INICIAR ANÁLISIS", command=self.run_analysis)
        self.btn_run.pack(fill=tk.X, pady=20)
        
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

    def run_analysis(self):
        step_file = self.file_path.get()
        if not step_file:
            messagebox.showwarning("Atención", "Por favor selecciona un archivo .stp primero.")
            return

        # Desactivar botón para evitar doble clic
        self.btn_run.config(state="disabled")
        self.status_var.set("⏳ Procesando... Por favor espere (la ventana puede congelarse unos segundos).")
        self.root.update()

        # Ejecutar en un hilo separado para no congelar la UI totalmente (opcional pero recomendado)
        # Sin embargo, pythonocc necesita el hilo principal para la GUI. 
        # Así que ejecutamos la lógica pesada aquí y lanzamos el visualizador al final.
        try:
            self.process_logic(step_file)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")
            self.status_var.set("Error.")
        finally:
            self.btn_run.config(state="normal")

    def process_logic(self, file_path):
        # 1. Geometría
        self.status_var.set("Analizando geometría...")
        self.root.update()
        
        geo = GeometryProcessor(file_path)
        geo.load_step()
        cylinders = geo.extract_features_topology()

        # 2. Análisis
        self.status_var.set("Detectando Heat Stakes...")
        self.root.update()
        
        analyzer = HeatStakeAnalyzer()
        topo_stakes, remaining = analyzer.analyze_topology(cylinders)
        cluster_stakes, rejected = analyzer.analyze_clusters_legacy(remaining, eps=self.eps_val.get())
        
        all_valid_stakes = topo_stakes + cluster_stakes

        # 3. Fusión (Si está activada o por defecto en analyzer)
        if self.custom_rules.get():
            self.status_var.set("Fusionando familias...")
            merger = FamilyMerger()
            # ... lógica extra si necesitas añadir reglas específicas ...
            # Por ahora el analyzer ya hace una fusión interna, pero si quieres usar
            # el FamilyMerger externo para reagrupar todo:
            
            by_fam = {}
            for s in all_valid_stakes:
                fam = s.get('family_id', 'DEFAULT')
                if fam not in by_fam: by_fam[fam] = []
                by_fam[fam].append(s)
            
            all_valid_stakes = merger.merge_all_families(by_fam)

        # 4. Reporte y Visualización
        self.status_var.set(f"¡Listo! Detectados: {len(all_valid_stakes)}")
        
        # Exportar automáticamente
        output_file = "reporte_deteccion.txt"
        
        if self.view_3d.get():
            # Ocultamos el launcher mientras se ve el 3D
            self.root.withdraw()
            
            viz = ResultVisualizer(geo.shape, all_valid_stakes, rejected)
            viz.export_report(output_file)
            
            messagebox.showinfo("Éxito", f"Detección completada.\nEncontrados: {len(all_valid_stakes)}\nAbriendo visualizador 3D...")
            
            # Esto bloquea hasta que cierras la ventana 3D
            viz.show_3d(show_rejected=self.show_rejected.get())
            
            # Volver a mostrar el launcher al cerrar
            self.root.deiconify()
            self.status_var.set("Visualización finalizada.")

if __name__ == "__main__":
    root = tk.Tk()
    app = HeatStakeLauncher(root)
    root.mainloop()