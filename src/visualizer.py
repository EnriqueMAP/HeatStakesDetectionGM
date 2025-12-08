# src/visualizer.py
from OCC.Display.SimpleGui import init_display
from OCC.Core.AIS import AIS_Shape
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCC.Core.gp import gp_Pnt
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
import time

class ResultVisualizer:
    def __init__(self, shape, valid_stakes, rejected_clusters):
        self.shape = shape
        self.valid_stakes = valid_stakes
        self.rejected_clusters = rejected_clusters

    def show_3d(self, show_rejected=False):
        print("\n🎨 Iniciando visualización 3D...")
        display, start_display, _, _ = init_display()
        
        # 1. Dibujar modelo base transparente
        if self.shape:
            ais_shape = AIS_Shape(self.shape)
            display.Context.Display(ais_shape, True)
            display.Context.SetTransparency(ais_shape, 0.7, True)
            
        # 2. Dibujar Heat Stakes (Verde/Rojo/Azul)
        for i, hs in enumerate(self.valid_stakes):
            self._draw_marker(display, hs, i, is_rejected=False)
            
        # 3. Dibujar Rechazados (Negro)
        if show_rejected:
            for i, r in enumerate(self.rejected_clusters):
                self._draw_marker(display, r, i, is_rejected=True)
                
        display.FitAll()
        start_display()

    def _draw_marker(self, display, item, index, is_rejected):
        c = item['analysis']['centroid']
        pnt = gp_Pnt(c[0], c[1], c[2])
        
        if is_rejected:
            radius = 3.0
            color = Quantity_Color(0.1, 0.1, 0.1, Quantity_TOC_RGB) # Negro
            label = f"R-{index}"
        else:
            conf = item['validation']['confidence']
            radius = 6.0 if conf == 'HIGH' else 4.0
            color = Quantity_Color(0.0, 1.0, 0.0, Quantity_TOC_RGB) # Verde base
            label = f"HS-{index}"

        sphere = BRepPrimAPI_MakeSphere(pnt, radius).Shape()
        ais_sphere = AIS_Shape(sphere)
        display.Context.Display(ais_sphere, True)
        display.Context.SetColor(ais_sphere, color, True)
        
        # Texto
        text_pos = gp_Pnt(c[0], c[1], c[2] + radius * 1.5)
        display.DisplayMessage(text_pos, label, height=radius, message_color=(0,0,0))

    def export_report(self, filename="report.txt"):
        print(f"💾 Guardando reporte en {filename}...")
        with open(filename, 'w') as f:
            f.write(f"REPORTE DE HEAT STAKES - {time.ctime()}\n")
            f.write(f"Detectados: {len(self.valid_stakes)}\n")
            f.write("-" * 40 + "\n")
            for i, hs in enumerate(self.valid_stakes):
                c = hs['analysis']['centroid']
                f.write(f"HS-{i+1}: X={c[0]:.2f}, Y={c[1]:.2f}, Z={c[2]:.2f} [{hs['validation']['confidence']}]\n")