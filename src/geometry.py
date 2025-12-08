# src/geometry.py
import sys
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.GeomAbs import GeomAbs_Cylinder
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop_SurfaceProperties
from OCC.Core.BRepTools import breptools_UVBounds

class GeometryProcessor:
    def __init__(self, step_file):
        self.step_file = step_file
        self.shape = None
        self.cylinders = []

    def load_step(self):
        """Carga el archivo STEP y retorna la forma (Shape)"""
        print(f"\n📂 Cargando archivo: {self.step_file}")
        reader = STEPControl_Reader()
        status = reader.ReadFile(self.step_file)
        
        if status != 1:
            raise Exception("❌ Error al leer el archivo STEP")
        
        reader.TransferRoots()
        self.shape = reader.OneShape()
        print("✓ Archivo cargado correctamente")
        return self.shape

    def extract_features(self):
        """
        Extrae geometrías relevantes.
        NOTA: Aquí añadiremos la detección de PLANOS en la Fase 2.
        """
        print("\n🔍 Extrayendo geometrías del modelo...")
        self.cylinders = []
        
        if not self.shape:
            self.load_step()

        explorer = TopExp_Explorer(self.shape, TopAbs_FACE)
        cylinder_count = 0
        
        while explorer.More():
            face = explorer.Current()
            surf = BRepAdaptor_Surface(face)
            
            if surf.GetType() == GeomAbs_Cylinder:
                self._process_cylinder(face, surf)
                cylinder_count += 1
            
            explorer.Next()
        
        print(f"✓ Encontrados {cylinder_count} cilindros")
        return self.cylinders

    def _process_cylinder(self, face, surf):
        """Procesa una cara cilíndrica individual"""
        cylinder_geom = surf.Cylinder()
        axis = cylinder_geom.Axis()
        location = axis.Location()
        direction = axis.Direction()
        
        # Obtener bounds UV para altura
        _, _, v_min, v_max = breptools_UVBounds(face)
        height = abs(v_max - v_min)
        
        # Calcular área
        props = GProp_GProps()
        brepgprop_SurfaceProperties(face, props)
        area = props.Mass()
        
        cylinder_info = {
            'face': face, # Referencia a objeto OCC
            'center': (location.X(), location.Y(), location.Z()),
            'direction': (direction.X(), direction.Y(), direction.Z()),
            'radius': cylinder_geom.Radius(),
            'height': height,
            'area': area
        }
        self.cylinders.append(cylinder_info)