# src/visualizer.py
from OCC.Display.SimpleGui import init_display
from OCC.Core.AIS import AIS_Shape
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCC.Core.gp import gp_Pnt
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.V3d import V3d_TypeOfOrientation
import numpy as np

class ResultVisualizer:
    def __init__(self, shape, valid_stakes, rejected_clusters):
        self.shape = shape
        self.valid_stakes = valid_stakes
        self.rejected_clusters = rejected_clusters
        
        self.colors = {
            'GRP1': Quantity_Color(0.0, 1.0, 0.0, Quantity_TOC_RGB),   # Verde
            'GRP2': Quantity_Color(0.0, 0.0, 1.0, Quantity_TOC_RGB),   # Azul
            'GRP3': Quantity_Color(1.0, 0.0, 1.0, Quantity_TOC_RGB),   # Magenta
            'GRP4': Quantity_Color(1.0, 1.0, 0.0, Quantity_TOC_RGB),   # Amarillo
            'MERGED': Quantity_Color(0.5, 0.0, 1.0, Quantity_TOC_RGB), # Morado
            'DEFAULT': Quantity_Color(1.0, 0.5, 0.0, Quantity_TOC_RGB) # Naranja
        }

    def show_3d(self, show_rejected=False):
        print("\n🎨 Iniciando visualización...")
        print("🖱️  CONTROLES DE MOUSE (Estándar CAD):")
        print("   [Clic Derecho + Arrastrar] : ROTAR vista")
        print("   [Rueda del Mouse]          : ZOOM In / Out")
        print("   [Clic Central + Arrastrar] : PAN (Moverse lateralmente)")
        print("   [Shift + Clic Central]     : PAN Alternativo")
        
        # Inicializar display sin callbacks de teclado problemáticos
        self.display, self.start_display, _, _ = init_display()
        
        # 1. Cargar Geometría
        if self.shape:
            ais_shape = AIS_Shape(self.shape)
            self.display.Context.Display(ais_shape, True)
            # Transparencia alta para ver los marcadores internos
            self.display.Context.SetTransparency(ais_shape, 0.8, True) 

        # 2. Dibujar Marcadores
        for i, hs in enumerate(self.valid_stakes):
            self._draw_marker(hs, i, is_rejected=False)
            
        if show_rejected:
            for i, r in enumerate(self.rejected_clusters):
                self._draw_marker(r, i, is_rejected=True)
        
        # 3. Enfoque Inicial en los Resultados (Ignorando basura)
        self._initial_view()
        
        self.start_display()

    def _initial_view(self):
        """Apunta la cámara al centro de los heat stakes detectados."""
        if not self.valid_stakes:
            # Si no hay nada, ajuste general
            self.display.FitAll()
            return

        # Calcular centroide de los resultados (solo heat stakes)
        points = [hs['analysis']['centroid'] for hs in self.valid_stakes]
        points = np.array(points)
        center = np.mean(points, axis=0)
        
        print(f"🎥 Cámara centrada en: ({center[0]:.1f}, {center[1]:.1f}, {center[2]:.1f})")
        
        # 1. Definir hacia dónde mira la cámara (At)
        self.display.View.SetAt(center[0], center[1], center[2])
        
        # 2. Definir dónde está la cámara (Eye)
        # Nos alejamos una distancia fija estándar (ej. 300mm) en diagonal
        dist_offset = 300.0 
        self.display.View.SetEye(center[0] + dist_offset, 
                                 center[1] - dist_offset, 
                                 center[2] + dist_offset)
        
        # 3. Orientación Z-Up
        self.display.View.SetProj(V3d_TypeOfOrientation.V3d_XposYposZpos)
        self.display.View.SetUp(0, 0, 1)

    def _draw_marker(self, item, index, is_rejected):
        c = item['analysis']['centroid']
        pnt = gp_Pnt(c[0], c[1], c[2])
        
        if is_rejected:
            radius = 2.0
            color = Quantity_Color(0.1, 0.1, 0.1, Quantity_TOC_RGB)
            label = "R"
        else:
            full_id = item.get('cluster_id', 'DEFAULT')
            family_id = item.get('family_id', 'DEFAULT')
            
            if family_id == 'MERGED':
                radius = 6.0
                color = self.colors['MERGED']
                label = "M"
            else:
                radius = 4.0
                color = self.colors.get(family_id, self.colors['DEFAULT'])
                # Simplificar etiqueta visual
                label = full_id.split('-')[0] if '-' in full_id else full_id

        sphere = BRepPrimAPI_MakeSphere(pnt, radius).Shape()
        ais_sphere = AIS_Shape(sphere)
        self.display.Context.Display(ais_sphere, True)
        self.display.Context.SetColor(ais_sphere, color, True)
        
        # Etiqueta de texto
        text_pos = gp_Pnt(c[0], c[1], c[2] + radius * 1.5)
        self.display.DisplayMessage(text_pos, label, height=radius*0.8, message_color=(0,0,0))

    def export_report(self, filename="report.txt"):
        print(f"💾 Guardando reporte en {filename}...")
        with open(filename, 'w') as f:
            f.write(f"REPORTE: {len(self.valid_stakes)} Heat Stakes.\n")
            for i, hs in enumerate(self.valid_stakes, 1):
                c = hs['analysis']['centroid']
                cid = hs.get('cluster_id', f'HS-{i}')
                f.write(f"{cid} | {c}\n")