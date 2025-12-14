# src/visualizer.py
from OCC.Display.SimpleGui import init_display
from OCC.Core.AIS import AIS_Shape
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCC.Core.gp import gp_Pnt
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.V3d import V3d_TypeOfOrientation
import numpy as np
from collections import defaultdict

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
        
        # Almacenamiento de objetos gráficos para poder ocultarlos
        self.ais_groups = defaultdict(list)
        self.visibility_states = {} 

    def show_3d(self, show_rejected=False):
        print("\n🎨 Iniciando visualización...")
        print("🖱️  CONTROLES:")
        print("   - Mouse: Rotar/Pan/Zoom")
        print("   - MENÚ SUPERIOR 'Capas': Activa/Desactiva familias.")
        
        self.display, self.start_display, self.add_menu, self.add_function = init_display()
        
        # 1. Cargar Geometría
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

        # 3. Crear Menú Funcional
        self._create_menu()

        # 4. Enfoque
        self._initial_view()
        
        self.start_display()

    def _create_menu(self):
        """Crea un menú más robusto para controlar visibilidad"""
        menu_name = 'Capas (Mostrar/Ocultar)'
        self.add_menu(menu_name)
        
        sorted_groups = sorted(self.ais_groups.keys())
        
        for group in sorted_groups:
            self.visibility_states[group] = True # Estado inicial: Visible
            
            # Usamos un closure para capturar el valor correcto de 'group'
            def make_callback(g_name):
                return lambda: self._toggle_visibility(g_name)
            
            self.add_function(menu_name, make_callback(group))
            
        print(f"✅ Menú de capas creado para: {', '.join(sorted_groups)}")

    def _toggle_visibility(self, group_name):
        """Fuerza la actualización visual de los objetos"""
        current_state = self.visibility_states[group_name]
        new_state = not current_state
        self.visibility_states[group_name] = new_state
        
        action = "MOSTRANDO" if new_state else "OCULTANDO"
        print(f"👁️  {action} {group_name}...")
        
        # Acceder al contexto gráfico
        ctx = self.display.Context
        
        # Iterar sobre los objetos de ese grupo
        for ais_obj in self.ais_groups[group_name]:
            if new_state:
                # Si queremos mostrar, usamos Display
                # False = no actualizar pantalla aún (para hacerlo en lote)
                ctx.Display(ais_obj, False) 
            else:
                # Si queremos ocultar, usamos Erase
                ctx.Erase(ais_obj, False)
        
        # Actualizar el visor UNA sola vez al final para rendimiento
        ctx.UpdateCurrentViewer()

    def _initial_view(self):
        if not self.valid_stakes:
            self.display.FitAll()
            return

        points = [hs['analysis']['centroid'] for hs in self.valid_stakes]
        center = np.mean(np.array(points), axis=0)
        
        self.display.View.SetAt(center[0], center[1], center[2])
        dist = 300.0 
        self.display.View.SetEye(center[0] + dist, center[1] - dist, center[2] + dist)
        self.display.View.SetProj(V3d_TypeOfOrientation.V3d_XposYposZpos)
        self.display.View.SetUp(0, 0, 1)

    def _draw_marker(self, item, index, is_rejected):
        c = item['analysis']['centroid']
        pnt = gp_Pnt(c[0], c[1], c[2])
        
        if is_rejected:
            group_id = 'RECHAZADOS'
            radius = 2.0
            color = Quantity_Color(0.1, 0.1, 0.1, Quantity_TOC_RGB)
            label = "R"
        else:
            family_id = item.get('family_id', 'DEFAULT')
            group_id = family_id
            
            if family_id == 'MERGED':
                radius = 6.0
                color = self.colors['MERGED']
                label = "M"
            else:
                radius = 4.0
                color = self.colors.get(family_id, self.colors['DEFAULT'])
                full_id = item.get('cluster_id', 'DEFAULT')
                label = full_id.split('-')[0] if '-' in full_id else full_id

        sphere = BRepPrimAPI_MakeSphere(pnt, radius).Shape()
        ais_sphere = AIS_Shape(sphere)
        
        # Dibujar inicialmente
        self.display.Context.Display(ais_sphere, True)
        self.display.Context.SetColor(ais_sphere, color, True)
        
        # Guardar en el diccionario para el menú
        self.ais_groups[group_id].append(ais_sphere)
        
        # Texto (Opcional: Si quieres que el texto también se oculte, 
        # habría que guardarlo en una lista separada, pero SimpleGui limita esto)
        text_pos = gp_Pnt(c[0], c[1], c[2] + radius * 1.5)
        self.display.DisplayMessage(text_pos, label, height=radius*0.8, message_color=(0,0,0))

    def export_report(self, filename="report.txt"):
        print(f"💾 Guardando reporte en {filename}...")
        with open(filename, 'w') as f:
            f.write(f"REPORTE: {len(self.valid_stakes)} Heat Stakes.\n")
            for i, hs in enumerate(self.valid_stakes, 1):
                c = hs['analysis']['centroid']
                cid = hs.get('cluster_id', f'HS-{i}')
                rad = hs['analysis'].get('avg_radius', 0.0)
                f.write(f"{cid} | {c} | R={rad:.2f}\n")