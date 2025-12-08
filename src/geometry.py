# src/geometry.py
from OCC.Core.STEPControl import STEPControl_Reader
# Importamos los módulos estáticos para evitar DeprecationWarnings
from OCC.Core.TopExp import TopExp_Explorer, topexp
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
from OCC.Core.BRepTools import breptools
from OCC.Core.TopTools import TopTools_IndexedDataMapOfShapeListOfShape, TopTools_ListIteratorOfListOfShape
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
# Importamos Bounding Box para la optimización
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add

class GeometryProcessor:
    def __init__(self, step_file):
        self.step_file = step_file
        self.shape = None
        # Cache optimizado: Guardará tuplas (Cara, BoundingBox)
        self.cached_planes = [] 

    def load_step(self):
        print(f"\n📂 Cargando archivo: {self.step_file}")
        reader = STEPControl_Reader()
        status = reader.ReadFile(self.step_file)
        if status != 1:
            raise Exception("❌ Error al leer el archivo STEP")
        reader.TransferRoots()
        self.shape = reader.OneShape()
        print("✓ Archivo cargado correctamente")
        return self.shape

    def extract_features_topology(self):
        print("\n🔍 Analizando topología con OPTIMIZACIÓN ESPACIAL...")
        
        if not self.shape:
            self.load_step()

        # 1. Pre-calcular Bounding Boxes de todos los planos (Solo una vez)
        self._cache_all_planes()

        # 2. Mapeo Topológico (Rápido)
        map_edges_faces = TopTools_IndexedDataMapOfShapeListOfShape()
        topexp.MapShapesAndAncestors(self.shape, TopAbs_EDGE, TopAbs_FACE, map_edges_faces)

        candidates = []
        
        # 3. Analizar Cilindros
        explorer = TopExp_Explorer(self.shape, TopAbs_FACE)
        total_cyl = 0
        
        while explorer.More():
            face = explorer.Current()
            surf = BRepAdaptor_Surface(face)
            
            if surf.GetType() == GeomAbs_Cylinder:
                # A. Intento Topológico (Contacto perfecto)
                connected_planes = self._count_connected_planes_topo(face, map_edges_faces)
                
                # Datos geométricos básicos
                cyl_data = self._process_cylinder(face, surf)
                
                # B. Si Topología falla (0-2 aletas), intentar Espacial (Proximidad)
                # OPTIMIZACIÓN: Solo gastar tiempo si el cilindro es pequeño (<10mm)
                # Si mide 95 metros, ni te molestes en medir distancias.
                if connected_planes < 3 and cyl_data['radius'] < 10.0:
                    connected_planes = self._count_connected_planes_spatial(face)

                cyl_data['connected_planes'] = connected_planes
                candidates.append(cyl_data)
                total_cyl += 1
            
            explorer.Next()
        
        print(f"✓ Analizados {total_cyl} cilindros en tiempo récord")
        return candidates

    def _cache_all_planes(self):
        """
        Pre-calcula las cajas límite de todos los planos.
        Esto evita recalcular la geometría del plano miles de veces.
        """
        self.cached_planes = []
        exp = TopExp_Explorer(self.shape, TopAbs_FACE)
        while exp.More():
            face = exp.Current()
            surf = BRepAdaptor_Surface(face)
            if surf.GetType() == GeomAbs_Plane:
                # Crear Bounding Box
                bbox = Bnd_Box()
                brepbndlib_Add(face, bbox)
                self.cached_planes.append((face, bbox))
            exp.Next()

    def _count_connected_planes_topo(self, cylinder_face, map_map):
        """Conteo por contacto estricto (rápido)"""
        plane_count = 0
        edge_exp = TopExp_Explorer(cylinder_face, TopAbs_EDGE)
        while edge_exp.More():
            edge = edge_exp.Current()
            neighbors = map_map.FindFromKey(edge)
            it = TopTools_ListIteratorOfListOfShape(neighbors)
            while it.More():
                neighbor_face = it.Value()
                if not neighbor_face.IsSame(cylinder_face):
                    nsurf = BRepAdaptor_Surface(neighbor_face)
                    if nsurf.GetType() == GeomAbs_Plane:
                        plane_count += 1
                it.Next()
            edge_exp.Next()
        return plane_count

    def _count_connected_planes_spatial(self, cylinder_face):
        """
        Conteo por proximidad OPTIMIZADO.
        Usa Bounding Boxes para descartar el 99% de los casos rápidamente.
        """
        spatial_hits = 0
        tolerance = 0.15  # mm
        
        # 1. Calcular BBox del cilindro y expandirla un poco
        cyl_bbox = Bnd_Box()
        brepbndlib_Add(cylinder_face, cyl_bbox)
        cyl_bbox.Enlarge(tolerance) # Hacemos la caja un poquito más grande

        # 2. Comparar contra el cache de planos
        for plane_face, plane_bbox in self.cached_planes:
            # FILTRO RÁPIDO: ¿Se tocan las cajas?
            # IsOut devuelve True si las cajas están separadas -> Continue
            if not cyl_bbox.IsOut(plane_bbox):
                
                # 3. Solo si las cajas se tocan, hacemos el cálculo pesado
                dist_algo = BRepExtrema_DistShapeShape(cylinder_face, plane_face)
                if dist_algo.IsDone():
                    if dist_algo.Value() < tolerance:
                        spatial_hits += 1
                    
        return spatial_hits

    def _process_cylinder(self, face, surf):
        cylinder_geom = surf.Cylinder()
        axis = cylinder_geom.Axis()
        location = axis.Location()
        
        # Uso corregido de breptools para evitar warnings
        _, _, v_min, v_max = breptools.UVBounds(face)
        height = abs(v_max - v_min)
        
        return {
            'face': face, # Referencia (útil para debug, aunque no serializable)
            'center': (location.X(), location.Y(), location.Z()),
            'radius': cylinder_geom.Radius(),
            'height': height,
            'direction': (axis.Direction().X(), axis.Direction().Y(), axis.Direction().Z())
        }