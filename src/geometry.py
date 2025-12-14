# src/geometry.py
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopExp import TopExp_Explorer, topexp
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
from OCC.Core.BRepTools import breptools
from OCC.Core.TopTools import TopTools_IndexedDataMapOfShapeListOfShape, TopTools_ListIteratorOfListOfShape
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add
# NUEVO: Para calcular Centro de Gravedad exacto
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop_SurfaceProperties

class GeometryProcessor:
    def __init__(self, step_file):
        self.step_file = step_file
        self.shape = None
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
        print("\n🔍 Analizando topología con CENTROS DE GRAVEDAD PRECISOS...")
        
        if not self.shape:
            self.load_step()

        self._cache_all_planes()
        map_edges_faces = TopTools_IndexedDataMapOfShapeListOfShape()
        topexp.MapShapesAndAncestors(self.shape, TopAbs_EDGE, TopAbs_FACE, map_edges_faces)

        candidates = []
        explorer = TopExp_Explorer(self.shape, TopAbs_FACE)
        total_cyl = 0
        
        while explorer.More():
            face = explorer.Current()
            surf = BRepAdaptor_Surface(face)
            
            if surf.GetType() == GeomAbs_Cylinder:
                connected_planes = self._count_connected_planes_topo(face, map_edges_faces)
                
                # Procesar cilindro con cálculo de CoG
                cyl_data = self._process_cylinder(face, surf)
                
                if connected_planes < 3 and cyl_data['radius'] < 10.0:
                    connected_planes = self._count_connected_planes_spatial(face)

                cyl_data['connected_planes'] = connected_planes
                candidates.append(cyl_data)
                total_cyl += 1
            
            explorer.Next()
        
        print(f"✓ Analizados {total_cyl} cilindros.")
        return candidates

    def _process_cylinder(self, face, surf):
        cylinder_geom = surf.Cylinder()
        
        # --- CÁLCULO DE CENTRO DE GRAVEDAD (CoG) ---
        # En lugar de usar la ubicación del eje (que puede estar desplazada),
        # calculamos el centro geométrico real de la superficie.
        props = GProp_GProps()
        brepgprop_SurfaceProperties(face, props)
        cog = props.CentreOfMass() # Punto exacto del centro
        
        # Altura aproximada por UV
        _, _, v_min, v_max = breptools.UVBounds(face)
        height = abs(v_max - v_min)
        
        return {
            'face': face,
            'center': (cog.X(), cog.Y(), cog.Z()), # Usamos el CoG real
            'radius': cylinder_geom.Radius(),
            'height': height,
            'direction': (cylinder_geom.Axis().Direction().X(), 
                          cylinder_geom.Axis().Direction().Y(), 
                          cylinder_geom.Axis().Direction().Z())
        }

    # --- Funciones auxiliares (Sin cambios) ---
    def _cache_all_planes(self):
        self.cached_planes = []
        exp = TopExp_Explorer(self.shape, TopAbs_FACE)
        while exp.More():
            face = exp.Current()
            surf = BRepAdaptor_Surface(face)
            if surf.GetType() == GeomAbs_Plane:
                bbox = Bnd_Box()
                brepbndlib_Add(face, bbox)
                self.cached_planes.append((face, bbox))
            exp.Next()

    def _count_connected_planes_topo(self, cylinder_face, map_map):
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
        spatial_hits = 0
        tolerance = 0.15 
        cyl_bbox = Bnd_Box()
        brepbndlib_Add(cylinder_face, cyl_bbox)
        cyl_bbox.Enlarge(tolerance)

        for plane_face, plane_bbox in self.cached_planes:
            if not cyl_bbox.IsOut(plane_bbox):
                dist_algo = BRepExtrema_DistShapeShape(cylinder_face, plane_face)
                if dist_algo.IsDone():
                    if dist_algo.Value() < tolerance:
                        spatial_hits += 1
        return spatial_hits