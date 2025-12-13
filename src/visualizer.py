# src/visualizer.py
from OCC.Display.SimpleGui import init_display
from OCC.Core.AIS import AIS_Shape
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCC.Core.gp import gp_Pnt
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.V3d import V3d_TypeOfOrientation
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
            'MERGED': Quantity_Color(0.5, 0.0, 1.0, Quantity_TOC_RGB), # Morado (GRP1+GRP2 fusionados)
            'DEFAULT': Quantity_Color(1.0, 0.5, 0.0, Quantity_TOC_RGB) # Naranja
        }

    def show_3d(self, show_rejected=False):
        print("\n🎨 Iniciando visualización MULTI-GRUPO...")
        print("🖱️  Controles:")
        print("   - Clic Medio + Arrastrar: Rotar")
        print("   - Shift + Clic Medio: Pan/Mover")
        print("   - Rueda del Mouse: Zoom")
        print("   - Ctrl + Clic Medio: Zoom dinámico")
        print("\n🎨 Colores:")
        print("   - Verde (GRP1): Familia principal")
        print("   - Azul (GRP2): Familia secundaria")
        print("   - Morado (MERGED): Familias GRP1+GRP2 fusionadas")
        
        self.display, self.start_display, _, _ = init_display()
        self._setup_scene()
        
        # Dibujar Heat Stakes
        for i, hs in enumerate(self.valid_stakes):
            self._draw_marker(hs, i, is_rejected=False)
            
        # Dibujar Rechazados
        if show_rejected:
            for i, r in enumerate(self.rejected_clusters):
                self._draw_marker(r, i, is_rejected=True)
        
        # Ajustar vista inicial
        self.display.FitAll()
        self.display.View.SetProj(V3d_TypeOfOrientation.V3d_XposYposZpos)
        
        # Asegurar que se actualice la vista
        self.display.Repaint()
        
        self.start_display()

    def _setup_scene(self):
        if self.shape:
            ais_shape = AIS_Shape(self.shape)
            self.display.Context.Display(ais_shape, True)
            self.display.Context.SetTransparency(ais_shape, 0.7, True)
            
            # Calcular centro de la geometría
            bbox = Bnd_Box()
            brepbndlib.Add(self.shape, bbox)
            xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
            cx, cy, cz = (xmin+xmax)/2, (ymin+ymax)/2, (zmin+zmax)/2
            
            # Configurar punto de enfoque
            self.display.View.SetAt(cx, cy, cz)
            
            # Configurar iluminación
            self.display.View.SetLightOn()

    def _draw_marker(self, item, index, is_rejected):
        c = item['analysis']['centroid']
        pnt = gp_Pnt(c[0], c[1], c[2])
        
        if is_rejected:
            radius = 2.0
            color = Quantity_Color(0.1, 0.1, 0.1, Quantity_TOC_RGB)
            label = "R"
        else:
            radius = 5.0  # Radio más grande para familias fusionadas
            
            # Obtener ID de familia
            full_id = item.get('cluster_id', 'DEFAULT')
            family_id = item.get('family_id', 'DEFAULT')
            
            # Si es familia fusionada, usar color morado
            if family_id == 'MERGED':
                color = self.colors['MERGED']
                # Mostrar familias originales en el label
                original = '+'.join(item.get('original_families', []))
                label = f"M:{original}"
                radius = 6.0  # Aún más grande para destacar fusiones
            else:
                # Familia normal
                family_key = full_id.split('-')[0] if '-' in full_id else family_id
                color = self.colors.get(family_key, self.colors['DEFAULT'])
                label = full_id

        sphere = BRepPrimAPI_MakeSphere(pnt, radius).Shape()
        ais_sphere = AIS_Shape(sphere)
        self.display.Context.Display(ais_sphere, True)
        self.display.Context.SetColor(ais_sphere, color, True)
        
        text_pos = gp_Pnt(c[0], c[1], c[2] + radius * 1.5)
        self.display.DisplayMessage(text_pos, label, height=radius*0.8, message_color=(0,0,0))

    def export_report(self, filename="report.txt"):
        print(f"💾 Guardando reporte en {filename}...")
        with open(filename, 'w') as f:
            # Encabezado
            f.write(f"{'='*70}\n")
            f.write(f"REPORTE DE HEAT STAKES DETECTADOS\n")
            f.write(f"{'='*70}\n\n")
            f.write(f"Total detectados: {len(self.valid_stakes)}\n")
            f.write("LEYENDA: GRP1=Verde, GRP2=Azul, MERGED=Morado (Fusionados)\n\n")
            
            # Estadísticas por tipo
            by_type = {}
            for hs in self.valid_stakes:
                family = hs.get('family_id', 'UNKNOWN')
                if family not in by_type:
                    by_type[family] = []
                by_type[family].append(hs)
            
            f.write(f"\n{'='*70}\n")
            f.write("ESTADÍSTICAS POR TIPO\n")
            f.write(f"{'='*70}\n")
            for family, stakes in by_type.items():
                f.write(f"\n{family}: {len(stakes)} heat stakes\n")
                
                if family == 'MERGED':
                    # Desglose de fusiones
                    fusion_types = {}
                    for stake in stakes:
                        ftype = '+'.join(sorted(stake.get('original_families', [])))
                        if ftype not in fusion_types:
                            fusion_types[ftype] = 0
                        fusion_types[ftype] += 1
                    
                    for ftype, count in fusion_types.items():
                        f.write(f"  - {ftype}: {count} fusiones\n")
            
            # Detalle de cada heat stake
            f.write(f"\n{'='*70}\n")
            f.write("DETALLE DE HEAT STAKES\n")
            f.write(f"{'='*70}\n\n")
            
            for i, hs in enumerate(self.valid_stakes, 1):
                c = hs['analysis']['centroid']
                cid = hs['cluster_id']
                rad = hs['analysis']['avg_radius']
                num_cyl = hs['analysis']['num_cylinders']
                
                f.write(f"{i}. {cid}\n")
                f.write(f"   Posición: ({c[0]:.2f}, {c[1]:.2f}, {c[2]:.2f})\n")
                f.write(f"   Radio promedio: {rad:.2f}mm\n")
                f.write(f"   Cilindros: {num_cyl}\n")
                
                # Información adicional si es fusionado
                if 'original_families' in hs:
                    families = '+'.join(hs['original_families'])
                    f.write(f"   Tipo: FUSIONADO ({families})\n")
                    
                    if 'merge_distance' in hs['validation'] and hs['validation']['merge_distance']:
                        dist = hs['validation']['merge_distance']
                        f.write(f"   Distancia de fusión: {dist:.2f}mm\n")
                    
                    if 'num_merged' in hs['validation']:
                        num_merged = hs['validation']['num_merged']
                        f.write(f"   Componentes fusionados: {num_merged}\n")
                
                # Dispersión máxima si está disponible
                if 'max_spread' in hs['analysis']:
                    spread = hs['analysis']['max_spread']
                    f.write(f"   Dispersión máxima: {spread:.2f}mm\n")
                
                f.write("\n")
    
    def set_view_orientation(self, orientation='iso'):
        """Establece orientaciones de vista predefinidas"""
        if orientation == 'top':
            self.display.View.SetProj(V3d_TypeOfOrientation.V3d_Zpos)
        elif orientation == 'front':
            self.display.View.SetProj(V3d_TypeOfOrientation.V3d_Xpos)
        elif orientation == 'right':
            self.display.View.SetProj(V3d_TypeOfOrientation.V3d_Ypos)
        elif orientation == 'iso':
            self.display.View.SetProj(V3d_TypeOfOrientation.V3d_XposYposZpos)
        
        self.display.FitAll()