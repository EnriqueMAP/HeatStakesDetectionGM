# src/visualizer.py
import sys
import numpy as np
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
        
        # Configuración de Colores
        self.config = {
            'GRP1':    {'color': (0.0, 1.0, 0.0), 'name': 'Verde'},
            'GRP2':    {'color': (0.0, 0.0, 1.0), 'name': 'Azul'},
            'GRP3':    {'color': (1.0, 0.0, 1.0), 'name': 'Magenta'},
            'GRP4':    {'color': (1.0, 1.0, 0.0), 'name': 'Amarillo'},
            'MERGED':  {'color': (0.5, 0.0, 1.0), 'name': 'Morado (Fusionado)'},
            'DEFAULT': {'color': (1.0, 0.5, 0.0), 'name': 'Naranja'},
            'REJECTED':{'color': (0.1, 0.1, 0.1), 'name': 'Rechazados (Negro)'}
        }
        
        # Almacén de objetos gráficos
        self.ais_groups = defaultdict(list)
        self.visibility_states = {} 

    def show_3d(self, show_rejected=False):
        print("\n🎨 Iniciando visualización SimpleGUI...")
        print("🖱️  CONTROLES:")
        print("   - Rotar: Clic Derecho")
        print("   - Pan: Clic Central")
        print("   - Zoom: Rueda")
        print("   - MENÚ SUPERIOR 'Capas': Haz clic para ocultar/mostrar familias.")
        
        # Inicializar Display
        self.display, self.start_display, self.add_menu, self.add_function = init_display()
        
        # 1. Cargar Geometría Base (Transparente)
        if self.shape:
            ais_shape = AIS_Shape(self.shape)
            self.display.Context.Display(ais_shape, True)
            self.display.Context.SetTransparency(ais_shape, 0.8, True)

        # 2. Dibujar Heat Stakes
        for i, hs in enumerate(self.valid_stakes):
            self._draw_marker(hs, i, is_rejected=False)
            
        if show_rejected:
            for i, r in enumerate(self.rejected_clusters):
                self._draw_marker(r, i, is_rejected=True)

        # 3. Construir el Menú de Filtros
        self._build_menu()

        # 4. Enfoque Inteligente
        self._focus_camera()
        
        # --- BUCLE PRINCIPAL ---
        try:
            self.start_display()
        except KeyboardInterrupt:
            pass
        finally:
            print("\n👋 Cerrando aplicación y limpiando procesos...")
            # ESTO ES LO QUE MATA LA CONSOLA AL CERRAR LA VENTANA
            sys.exit(0)

    def _build_menu(self):
        """Construye el menú superior con nombres legibles"""
        menu_name = 'Capas (Ver/Ocultar)'
        self.add_menu(menu_name)
        
        sorted_groups = sorted(self.ais_groups.keys())
        
        for group_id in sorted_groups:
            self.visibility_states[group_id] = True # Todos visibles al inicio
            
            # Nombre legible
            color_data = self.config.get(group_id, self.config['DEFAULT'])
            color_name = color_data['name']
            item_label = f"Alternar {group_id} ({color_name})"
            
            # Crear callback encapsulado
            callback = self._create_callback(group_id)
            callback.__name__ = item_label # Texto del botón
            
            self.add_function(menu_name, callback)
            
        print(f"✅ Menú creado con opciones para: {', '.join(sorted_groups)}")

    def _create_callback(self, group_id):
        """Factory para aislar el scope de group_id"""
        def callback():
            self._toggle_visibility(group_id)
        return callback

    def _toggle_visibility(self, group_id):
        """Muestra u oculta los objetos del grupo seleccionado"""
        new_state = not self.visibility_states[group_id]
        self.visibility_states[group_id] = new_state
        
        action = "MOSTRANDO" if new_state else "OCULTANDO"
        count = len(self.ais_groups[group_id])
        print(f"👁️  {action} {group_id} ({count} objetos)...")
        
        ctx = self.display.Context
        
        # Operación en lote
        for ais in self.ais_groups[group_id]:
            if new_state:
                # Redisplay refresca si ya estaba cargado pero oculto
                ctx.Display(ais, False)
            else:
                # Erase oculta el objeto del visor pero lo mantiene en memoria
                ctx.Erase(ais, False)
        
        # Actualizar visor OBLIGATORIO
        ctx.UpdateCurrentViewer()
        # Forzar repintado de la ventana (Fix para Linux/SimpleGUI)
        self.display.Repaint()

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
            
            if family_id == 'MERGED':
                radius = 6.0
                label = "M"
            else:
                radius = 4.0
                full_id = item.get('cluster_id', 'UNK')
                label = full_id.split('-')[0] if '-' in full_id else full_id

        rgb = cfg['color']
        occ_color = Quantity_Color(rgb[0], rgb[1], rgb[2], Quantity_TOC_RGB)

        sphere = BRepPrimAPI_MakeSphere(pnt, radius).Shape()
        ais_sphere = AIS_Shape(sphere)
        
        self.display.Context.Display(ais_sphere, True)
        self.display.Context.SetColor(ais_sphere, occ_color, True)
        
        # Guardar en lista para el toggle
        self.ais_groups[group_id].append(ais_sphere)
        
        # Etiqueta
        text_pos = gp_Pnt(c[0], c[1], c[2] + radius * 1.5)
        self.display.DisplayMessage(text_pos, label, height=radius*0.8, message_color=(0,0,0))

    def export_report(self, filename="report.txt"):
        print(f"💾 Guardando reporte en {filename}...")
        try:
            with open(filename, 'w') as f:
                f.write(f"REPORTE HEAT STAKES\n{'='*30}\n")
                f.write(f"Total Detectados: {len(self.valid_stakes)}\n\n")
                for i, hs in enumerate(self.valid_stakes, 1):
                    c = hs['analysis']['centroid']
                    cid = hs.get('cluster_id', '?')
                    fid = hs.get('family_id', '?')
                    rad = hs['analysis'].get('avg_radius', 0.0)
                    f.write(f"{i}. {cid} ({fid}) | Pos: {c} | R={rad:.2f}\n")
            print("✅ Reporte guardado.")
        except Exception as e:
            print(f"❌ Error guardando reporte: {e}")