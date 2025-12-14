import sys
import os
import numpy as np

# --- CAMBIO: Usamos PySide6 en lugar de PyQt5 ---
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFileDialog, QDockWidget, 
                             QTreeWidget, QTreeWidgetItem, QLabel, QMessageBox, 
                             QProgressBar, QSplitter)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QColor, QPixmap, QPainter

# --- CAMBIO: Importamos el visor de PySide6 ---
from OCC.Display.Qt import qtViewer3d

from OCC.Core.AIS import AIS_Shape
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCC.Core.gp import gp_Pnt
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.V3d import V3d_TypeOfOrientation

# Importaciones de TU lógica
from src.geometry import GeometryProcessor
from src.analyzer import HeatStakeAnalyzer
from src.family_merger import FamilyMerger

class HeatStakeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detector de Heat Stakes GM - v3.0 GUI (PySide6)")
        self.resize(1280, 800)
        
        # --- Variables de Estado ---
        self.ais_groups = {} # Diccionario { 'GRP1': [ais_shape1, ais_shape2...] }
        self.valid_stakes = []
        
        # Definición de Colores y Nombres
        self.color_map = {
            'GRP1':    (0.0, 1.0, 0.0, "Verde"),
            'GRP2':    (0.0, 0.0, 1.0, "Azul"),
            'GRP3':    (1.0, 0.0, 1.0, "Magenta"),
            'GRP4':    (1.0, 1.0, 0.0, "Amarillo"),
            'MERGED':  (0.5, 0.0, 1.0, "Morado (Fusionado)"),
            'DEFAULT': (1.0, 0.5, 0.0, "Naranja")
        }

        self.init_ui()

    def init_ui(self):
        # 1. Widget Central (Visor 3D)
        self.canvas = qtViewer3d(self)
        self.setCentralWidget(self.canvas)
        
        # 2. Panel Lateral (Dock)
        self.dock = QDockWidget("Panel de Control", self)
        self.dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.dock.setMinimumWidth(300)
        
        # Contenedor del panel
        panel_widget = QWidget()
        layout = QVBoxLayout()
        
        # --- Botones ---
        btn_layout = QVBoxLayout()
        self.btn_load = QPushButton("📂 Cargar Archivo STEP")
        self.btn_load.setStyleSheet("padding: 10px; font-weight: bold; font-size: 14px;")
        self.btn_load.clicked.connect(self.load_and_process)
        
        self.btn_export = QPushButton("💾 Exportar Reporte")
        self.btn_export.clicked.connect(self.export_report)
        self.btn_export.setEnabled(False)
        
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_export)
        layout.addLayout(btn_layout)
        
        # --- Lista de Capas (Árbol) ---
        layout.addWidget(QLabel("<b>Capas y Familias Detectadas:</b>"))
        self.layer_tree = QTreeWidget()
        self.layer_tree.setHeaderLabel("Familia / Color")
        self.layer_tree.itemChanged.connect(self.on_layer_toggle)
        layout.addWidget(self.layer_tree)
        
        # --- Info ---
        self.lbl_info = QLabel("Esperando archivo...")
        self.lbl_info.setWordWrap(True)
        layout.addWidget(self.lbl_info)
        
        # Spacer
        layout.addStretch()
        
        panel_widget.setLayout(layout)
        self.dock.setWidget(panel_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        
        # 3. Barra de Estado
        self.status_bar = self.statusBar()
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress)
        
        # Inicializar Viewer
        self.canvas.InitDriver()
        self.display = self.canvas._display

    def load_and_process(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir archivo STEP", "", "STEP Files (*.stp *.step)")
        if not file_path:
            return

        self.lbl_info.setText("⏳ Procesando... Por favor espere.")
        self.progress.setVisible(True)
        self.progress.setRange(0, 0) # Indeterminado
        QApplication.processEvents() # Forzar actualización UI

        try:
            # 1. Limpiar escena anterior
            self.display.Context.RemoveAll(True)
            self.layer_tree.clear()
            self.ais_groups = {}
            
            # 2. Geometría
            geo = GeometryProcessor(file_path)
            geo.load_step()
            
            # Dibujar la pieza (Transparente)
            ais_shape = AIS_Shape(geo.shape)
            self.display.Context.Display(ais_shape, True)
            self.display.Context.SetTransparency(ais_shape, 0.8, True)
            
            # 3. Análisis
            cylinders = geo.extract_features_topology()
            
            analyzer = HeatStakeAnalyzer()
            topo_stakes, remaining = analyzer.analyze_topology(cylinders)
            cluster_stakes, rejected = analyzer.analyze_clusters_legacy(remaining)
            
            all_valid = topo_stakes + cluster_stakes
            
            # 4. Fusión (Opcional, activada por defecto para limpieza)
            merger = FamilyMerger()
            # Organizar para fusión
            by_fam = {}
            for s in all_valid:
                fam = s.get('family_id', 'DEFAULT')
                if fam not in by_fam: by_fam[fam] = []
                by_fam[fam].append(s)
            
            self.valid_stakes = merger.merge_all_families(by_fam)
            
            # 5. Visualizar Resultados
            self.draw_results(self.valid_stakes)
            
            # 6. Enfocar Cámara
            self.focus_camera(self.valid_stakes)
            
            self.lbl_info.setText(f"✅ Proceso completado.\nDetectados: {len(self.valid_stakes)}")
            self.btn_export.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error crítico:\n{str(e)}")
            self.lbl_info.setText("❌ Error en el procesamiento.")
        
        finally:
            self.progress.setVisible(False)

    def draw_results(self, stakes):
        # Agrupar para el árbol
        grouped_display = {} # { 'GRP1': {'color': col, 'items': [ais]} }
        
        for hs in stakes:
            c = hs['analysis']['centroid']
            pnt = gp_Pnt(c[0], c[1], c[2])
            
            # Determinar Familia y Color
            fam_id = hs.get('family_id', 'DEFAULT')
            cluster_id = hs.get('cluster_id', 'UNK')
            
            # Obtener datos de color
            if fam_id in self.color_map:
                r, g, b, color_name = self.color_map[fam_id]
            else:
                r, g, b, color_name = self.color_map['DEFAULT']
            
            occ_color = Quantity_Color(r, g, b, Quantity_TOC_RGB)
            
            # Tamaño según tipo
            radius = 6.0 if fam_id == 'MERGED' else 4.0
            
            # Crear Esfera
            sphere = BRepPrimAPI_MakeSphere(pnt, radius).Shape()
            ais_sphere = AIS_Shape(sphere)
            
            self.display.Context.Display(ais_sphere, False)
            self.display.Context.SetColor(ais_sphere, occ_color, False)
            
            # Guardar referencia
            if fam_id not in self.ais_groups:
                self.ais_groups[fam_id] = []
            self.ais_groups[fam_id].append(ais_sphere)
            
            # Preparar datos para el árbol UI
            if fam_id not in grouped_display:
                grouped_display[fam_id] = {
                    'color_name': color_name,
                    'count': 0,
                    'hex': QColor.fromRgbF(r, g, b)
                }
            grouped_display[fam_id]['count'] += 1

        self.display.Context.UpdateCurrentViewer()
        
        # Rellenar el Árbol de Capas
        for fam_id, data in sorted(grouped_display.items()):
            item = QTreeWidgetItem(self.layer_tree)
            item.setText(0, f"{fam_id} ({data['color_name']}) - [{data['count']}]")
            item.setCheckState(0, Qt.Checked)
            
            # Guardar el ID de familia en el item para recuperarlo luego
            item.setData(0, Qt.UserRole, fam_id)
            
            # Icono de color
            pixmap = self._create_color_pixmap(data['hex'])
            item.setIcon(0, QIcon(pixmap))

        self.layer_tree.expandAll()

    def on_layer_toggle(self, item, column):
        """Muestra u oculta las esferas cuando cambias el checkbox"""
        fam_id = item.data(0, Qt.UserRole)
        is_visible = (item.checkState(0) == Qt.Checked)
        
        if fam_id in self.ais_groups:
            # Acción en lote
            for ais in self.ais_groups[fam_id]:
                if is_visible:
                    self.display.Context.Display(ais, False)
                else:
                    self.display.Context.Erase(ais, False)
            
            self.display.Context.UpdateCurrentViewer()

    def focus_camera(self, stakes):
        if not stakes:
            self.display.FitAll()
            return
            
        points = [s['analysis']['centroid'] for s in stakes]
        center = np.mean(np.array(points), axis=0)
        
        self.display.View.SetAt(center[0], center[1], center[2])
        dist = 300.0
        self.display.View.SetEye(center[0]+dist, center[1]-dist, center[2]+dist)
        self.display.View.SetProj(V3d_TypeOfOrientation.V3d_XposYposZpos)
        self.display.View.SetUp(0, 0, 1)

    def export_report(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Reporte", "reporte.txt", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(f"REPORTE HEAT STAKES\n{'='*30}\n")
                    f.write(f"Total: {len(self.valid_stakes)}\n\n")
                    for i, hs in enumerate(self.valid_stakes, 1):
                        c = hs['analysis']['centroid']
                        cid = hs.get('cluster_id', '?')
                        fid = hs.get('family_id', '?')
                        f.write(f"{i}. {cid} ({fid}) | Pos: {c}\n")
                
                QMessageBox.information(self, "Éxito", "Reporte guardado correctamente.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _create_color_pixmap(self, color):
        """Crea un cuadradito de color para el icono del árbol"""
        pix = QPixmap(16, 16)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, 16, 16)
        painter.end()
        return pix

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HeatStakeApp()
    window.show()
    # CAMBIO: exec() en lugar de exec_() (PySide6 standard)
    sys.exit(app.exec())