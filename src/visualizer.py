# src/visualizer.py
import sys
import os
import numpy as np
import pandas as pd
from collections import defaultdict

# Importaciones de PythonOCC
from OCC.Display.SimpleGui import init_display
from OCC.Core.AIS import AIS_Shape
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCC.Core.gp import gp_Pnt
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.V3d import V3d_TypeOfOrientation

class ResultVisualizer:
    def __init__(self, shape, valid_stakes, rejected_clusters):
        self.shape = shape
        self.valid_stakes = valid_stakes
        self.rejected_clusters = rejected_clusters
        
        self.config = {
            'GRP1':    {'color': (0.0, 1.0, 0.0), 'name': 'Verde'},
            'GRP2':    {'color': (0.0, 0.0, 1.0), 'name': 'Azul'},
            'GRP3':    {'color': (1.0, 0.0, 1.0), 'name': 'Magenta'},
            'GRP4':    {'color': (1.0, 1.0, 0.0), 'name': 'Amarillo'},
            'MERGED':  {'color': (0.5, 0.0, 1.0), 'name': 'Morado'},
            'DEFAULT': {'color': (1.0, 0.5, 0.0), 'name': 'Naranja'},
            'REJECTED':{'color': (0.1, 0.1, 0.1), 'name': 'Rechazados'}
        }
        
        self.ais_groups = defaultdict(list)
        self.visibility_states = {} 

    def show_3d(self, show_rejected=False):
        print("\n🎨 Iniciando visualización...")
        print("🖱️  CONTROLES: Clic Der (Rotar), Central (Pan), Rueda (Zoom).")
        print("👆  MENÚ: Usa el menú 'CONTROL DE CAPAS' arriba.")
        sys.stdout.flush()
        
        self.display, self.start_display, self.add_menu, self.add_function = init_display()
        
        # 1. Dibujar Pieza
        if self.shape:
            ais_shape = AIS_Shape(self.shape)
            self.display.Context.Display(ais_shape, False)
            self.display.Context.SetTransparency(ais_shape, 0.8, True)

        # 2. Dibujar Esferas
        for i, hs in enumerate(self.valid_stakes):
            self._draw_marker(hs, i, is_rejected=False)
            
        if show_rejected:
            for i, r in enumerate(self.rejected_clusters):
                self._draw_marker(r, i, is_rejected=True)

        # 3. Construir UI
        self._build_menu()
        self._focus_camera()
        
        # Mostrar todo
        self.display.Context.UpdateCurrentViewer()
        self._print_status()

        try:
            self.start_display()
        except KeyboardInterrupt:
            pass

    def _build_menu(self):
        menu_name = 'CONTROL DE CAPAS'
        self.add_menu(menu_name)
        sorted_groups = sorted(self.ais_groups.keys())
        
        for group_id in sorted_groups:
            self.visibility_states[group_id] = True
            
            # Crear nombre bonito
            color_name = self.config.get(group_id, self.config['DEFAULT'])['name']
            # Reemplazamos espacios por guiones bajos porque a veces SimpleGui corta nombres con espacios
            item_label = f"Alternar_{group_id}_({color_name})" 
            
            # --- SOLUCIÓN: Usar un método fábrica ---
            # Esto crea una función única para este grupo y le asigna el nombre correcto.
            callback_function = self._create_menu_item(group_id, item_label)
            
            self.add_function(menu_name, callback_function)

    def _create_menu_item(self, group_id, label_text):
        """
        Fábrica de funciones:
        Crea una función 'callback' dedicada para un group_id específico.
        Le asigna el __name__ para que aparezca bonito en el menú.
        """
        def callback(*args):
            # Esta función 'recuerda' el group_id con el que fue creada (Closure)
            self._toggle_visibility(group_id)
        
        # AQUÍ ESTÁ EL TRUCO: Cambiamos el nombre interno de la función
        callback.__name__ = label_text
        return callback

    def _toggle_visibility(self, group_id):
        print(f"🔄 Toggle: {group_id}")
        sys.stdout.flush()

        try:
            new_state = not self.visibility_states[group_id]
            self.visibility_states[group_id] = new_state
            
            ctx = self.display.Context
            
            for ais in self.ais_groups[group_id]:
                if new_state:
                    ctx.Display(ais, False)
                else:
                    ctx.Erase(ais, False)

            ctx.UpdateCurrentViewer()
            
            if hasattr(self.display, 'Repaint'):
                self.display.Repaint()
            
            self._print_status()

        except Exception as e:
            print(f"❌ ERROR: {e}")
            sys.stdout.flush()

    def _print_status(self):
        print("\n" + "="*30)
        print("   ESTADO DE VISIBILIDAD")
        print("="*30)
        for gid in sorted(self.ais_groups.keys()):
            mark = "[ X ]" if self.visibility_states[gid] else "[   ]"
            color_name = self.config.get(gid, self.config['DEFAULT'])['name']
            count = len(self.ais_groups[gid])
            print(f" {mark} {gid:<10} | {count:>3} items | {color_name}")
        print("-" * 30 + "\n")
        sys.stdout.flush()

    def _focus_camera(self):
        if not self.valid_stakes:
            self.display.FitAll()
            return
        points = [hs['analysis']['centroid'] for hs in self.valid_stakes]
        center = np.mean(np.array(points), axis=0)
        self.display.View.SetAt(center[0], center[1], center[2])
        dist = 300.0
        self.display.View.SetEye(center[0]+dist, center[1]-dist, center[2]+dist)
        self.display.View.SetProj(V3d_TypeOfOrientation.V3d_XposYposZpos)
        self.display.View.SetUp(0, 0, 1)

    def _draw_marker(self, item, index, is_rejected):
        c = item['analysis']['centroid']
        pnt = gp_Pnt(c[0], c[1], c[2])
        
        if is_rejected:
            group_id = 'REJECTED'
            radius = 2.0
            cfg = self.config['REJECTED']
            label = "R"
        else:
            family_id = item.get('family_id', 'DEFAULT')
            group_id = family_id
            cfg = self.config.get(family_id, self.config['DEFAULT'])
            radius = 6.0 if family_id == 'MERGED' else 4.0
            full_id = item.get('cluster_id', 'UNK')
            label = "M" if family_id == 'MERGED' else (full_id.split('-')[0] if '-' in full_id else full_id)

        rgb = cfg['color']
        occ_color = Quantity_Color(rgb[0], rgb[1], rgb[2], Quantity_TOC_RGB)
        sphere = BRepPrimAPI_MakeSphere(pnt, radius).Shape()
        ais_sphere = AIS_Shape(sphere)
        
        self.display.Context.Display(ais_sphere, False)
        self.display.Context.SetColor(ais_sphere, occ_color, False)
        
        self.ais_groups[group_id].append(ais_sphere)
        text_pos = gp_Pnt(c[0], c[1], c[2] + radius * 1.5)
        self.display.DisplayMessage(text_pos, label, height=radius*0.8, message_color=(0,0,0))

    def export_reports(self, original_filepath):
        if not original_filepath: base_name = "Sin_Nombre"
        else: base_name = os.path.splitext(os.path.basename(original_filepath))[0]
        
        output_dir = os.path.join("Reportes", base_name)
        os.makedirs(output_dir, exist_ok=True)
        xlsx_filename = os.path.join(output_dir, f"Reporte_{base_name}.xlsx")
        
        try:
            data = []
            for hs in self.valid_stakes:
                c = hs['analysis']['centroid']
                data.append({
                    "ID": hs.get('cluster_id', 'UNK'),
                    "Familia": hs.get('family_id', 'UNK'),
                    "X": round(c[0], 3), "Y": round(c[1], 3), "Z": round(c[2], 3),
                    "Radio": round(hs['analysis'].get('avg_radius', 0.0), 3)
                })
            df = pd.DataFrame(data)
            if not df.empty: df.to_excel(xlsx_filename, index=False)
            print(f"💾 Reporte Excel guardado en: {xlsx_filename}")
            sys.stdout.flush()
        except Exception as e:
            print(f"❌ Error Excel: {e}")
            sys.stdout.flush()