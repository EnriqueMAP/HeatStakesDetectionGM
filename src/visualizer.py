# src/visualizer.py
from OCC.Display.SimpleGui import init_display
from OCC.Core.AIS import AIS_Shape
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCC.Core.gp import gp_Pnt
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
import sys

class ResultVisualizer:
    def __init__(self, shape, valid_stakes, rejected_clusters):
        self.shape = shape
        self.valid_stakes = valid_stakes
        self.rejected_clusters = rejected_clusters
        
        # Paleta de colores para distintos grupos
        self.colors = {
            'GRP1': Quantity_Color(0.0, 1.0, 0.0, Quantity_TOC_RGB), # Verde (Más común)
            'GRP2': Quantity_Color(0.0, 0.0, 1.0, Quantity_TOC_RGB), # Azul
            'GRP3': Quantity_Color(1.0, 0.0, 1.0, Quantity_TOC_RGB), # Magenta
            'GRP4': Quantity_Color(1.0, 1.0, 0.0, Quantity_TOC_RGB), # Amarillo
            'DEFAULT': Quantity_Color(1.0, 0.5, 0.0, Quantity_TOC_RGB) # Naranja
        }

    def show_3d(self, show_rejected=False):
        print("\n🎨 Iniciando visualización MULTI-GRUPO...")
        self.display, self.start_display, _, _ = init_display()
        self._setup_scene()
        
        # Dibujar Heat Stakes
        for i, hs in enumerate(self.valid_stakes):
            self._draw_marker(hs, i, is_rejected=False)
            
        # Dibujar Rechazados
        if show_rejected:
            for i, r in enumerate(self.rejected_clusters):
                self._draw_marker(r, i, is_rejected=True)
                
        self.display.FitAll()
        self.start_display()

    def _setup_scene(self):
        if self.shape:
            ais_shape = AIS_Shape(self.shape)
            self.display.Context.Display(ais_shape, True)
            self.display.Context.SetTransparency(ais_shape, 0.7, True)
            
            bbox = Bnd_Box()
            brepbndlib.Add(self.shape, bbox)
            xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
            cx, cy, cz = (xmin+xmax)/2, (ymin+ymax)/2, (zmin+zmax)/2
            self.display.View.SetAt(cx, cy, cz)

    def _draw_marker(self, item, index, is_rejected):
        c = item['analysis']['centroid']
        pnt = gp_Pnt(c[0], c[1], c[2])
        
        if is_rejected:
            radius = 2.0
            color = Quantity_Color(0.1, 0.1, 0.1, Quantity_TOC_RGB)
            label = "R"
        else:
            radius = 4.0
            # Obtener ID de familia (ej: "GRP1" de "GRP1-5")
            full_id = item.get('cluster_id', 'DEFAULT')
            family_id = full_id.split('-')[0] if '-' in full_id else 'DEFAULT'
            
            color = self.colors.get(family_id, self.colors['DEFAULT'])
            label = full_id

        sphere = BRepPrimAPI_MakeSphere(pnt, radius).Shape()
        ais_sphere = AIS_Shape(sphere)
        self.display.Context.Display(ais_sphere, True)
        self.display.Context.SetColor(ais_sphere, color, True)
        
        text_pos = gp_Pnt(c[0], c[1], c[2] + radius * 1.5)
        self.display.DisplayMessage(text_pos, label, height=radius, message_color=(0,0,0))

    def export_report(self, filename="report.txt"):
        print(f"💾 Guardando reporte en {filename}...")
        with open(filename, 'w') as f:
            f.write(f"REPORTE: {len(self.valid_stakes)} Heat Stakes detectados.\n")
            f.write("LEYENDA: GRP1=Verde (Común), GRP2=Azul, GRP3=Magenta\n\n")
            
            for hs in self.valid_stakes:
                c = hs['analysis']['centroid']
                cid = hs['cluster_id']
                rad = hs['analysis']['avg_radius']
                f.write(f"{cid}: R={rad:.2f}mm en {c}\n")