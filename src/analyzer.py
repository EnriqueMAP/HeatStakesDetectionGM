# src/analyzer.py
import numpy as np
from sklearn.cluster import DBSCAN
from collections import Counter, defaultdict
from src.family_merger import FamilyMerger

class HeatStakeAnalyzer:
    def __init__(self, strict_mode=False):
        self.STRICT_MODE = strict_mode
        self.MIN_CONNECTED_PLANES = 3 
        self.MIN_HEIGHT = 2.0
        self.MERGE_DISTANCE = 15.0 
        self.FAMILY_MERGE_DISTANCE = 15.0  # Distancia para fusionar familias
        self.radius_tolerance = 0.2 

    def analyze_topology(self, cylinders):
        print(f"\n🔬 Ejecutando análisis por FAMILIAS GEOMÉTRICAS...")
        
        # 1. Recolección Inicial
        population = []
        remaining_cylinders = []
        
        for cyl in cylinders:
            if cyl['connected_planes'] >= self.MIN_CONNECTED_PLANES:
                population.append(cyl)
            else:
                remaining_cylinders.append(cyl)

        if not population:
            print("⚠️ No se encontraron candidatos con aletas.")
            return [], remaining_cylinders

        # 2. SEGREGACIÓN POR FAMILIAS (Radios)
        grouped_candidates = self._group_by_families(population)
        
        # 3. FUSIÓN DE DUPLICADOS (Por cada familia)
        family_stakes = {}
        for family_id, candidates in grouped_candidates.items():
            merged = self._merge_close_candidates(candidates, family_id)
            family_stakes[family_id] = merged
        
        # 4. ⭐ SISTEMA COMPLETO DE FUSIÓN DE FAMILIAS ⭐
        merger = FamilyMerger()
        final_stakes = merger.merge_all_families(family_stakes)
        
        # Mostrar resumen
        merger.print_fusion_summary(final_stakes)
        
        print(f"✓ Detectados totales: {len(final_stakes)}")
        return final_stakes, remaining_cylinders

    def _group_by_families(self, population):
        """Agrupa los candidatos según su radio."""
        families = defaultdict(list)
        
        for cand in population:
            rad_key = round(cand['radius'], 1) 
            families[rad_key].append(cand)
            
        valid_families = {}
        print(f"   📊 Análisis de Familias:")
        
        family_counter = 1
        sorted_keys = sorted(families.keys(), key=lambda k: len(families[k]), reverse=True)
        
        for rad in sorted_keys:
            members = families[rad]
            count = len(members)
            
            if count >= 3:
                avg_fins = int(np.median([c['connected_planes'] for c in members]))
                label = f"GRP{family_counter}"
                valid_families[label] = members
                
                print(f"      🔹 Familia {label}: {count} miembros | Radio ~{rad}mm | Aletas típicas: {avg_fins}")
                
                if rad > 3.5:
                    print(f"         ⚠ Posible WAYDOOR/LOCATOR (Radio grande)")
                elif rad < 1.0:
                    print(f"         ⚠ Posibles PINES/Restos (Radio muy pequeño)")
                else:
                    print(f"         ✅ Probable HEAT STAKE")
                
                family_counter += 1
            else:
                print(f"      ❌ Descartada familia ruido (R={rad}, N={count})")
                
        return valid_families

    def _merge_close_candidates(self, candidates, family_id):
        """Fusiona candidatos cercanos dentro de una familia"""
        if not candidates: return []
        
        points = np.array([c['center'] for c in candidates])
        clustering = DBSCAN(eps=self.MERGE_DISTANCE, min_samples=1)
        labels = clustering.fit_predict(points)
        
        merged_results = []
        for label in set(labels):
            indices = [i for i, x in enumerate(labels) if x == label]
            group_cylinders = [candidates[i] for i in indices]
            
            # ⭐ Calcular centro de gravedad real
            positions = np.array([c['center'] for c in group_cylinders])
            centroid = np.mean(positions, axis=0)
            
            avg_radius = np.mean([c['radius'] for c in group_cylinders])
            max_planes = np.max([c['connected_planes'] for c in group_cylinders])
            
            merged_results.append({
                'cluster_id': f"{family_id}-{label+1}",
                'family_id': family_id,
                'cylinders': group_cylinders,  # Guardamos los cilindros originales
                'analysis': {
                    'centroid': tuple(centroid),
                    'num_cylinders': len(group_cylinders),
                    'avg_radius': avg_radius,
                    'connected_planes': int(max_planes)
                },
                'validation': {
                    'confidence': 'HIGH',
                    'type': 'FAMILY_GROUP',
                    'score': 5.0
                }
            })
        return merged_results

    def analyze_clusters_legacy(self, cylinders, eps=25.0, min_samples=5):
        """Legacy Clustering para respaldo"""
        if not cylinders or len(cylinders) < min_samples: return [], []
        print(f"🔬 Ejecutando análisis Legacy (Respaldo)...")
        
        viable_cyls = [c for c in cylinders if c['radius'] < 10.0]
        if not viable_cyls: return [], []

        centers = np.array([c['center'] for c in viable_cyls])
        clustering = DBSCAN(eps=eps, min_samples=min_samples)
        labels = clustering.fit_predict(centers)
        
        candidates = []
        for label in set(labels):
            if label == -1: continue
            indices = [i for i, x in enumerate(labels) if x == label]
            cluster_cyls = [viable_cyls[i] for i in indices]
            
            # Datos del grupo
            center = np.mean([c['center'] for c in cluster_cyls], axis=0)
            avg_rad = np.mean([c['radius'] for c in cluster_cyls])
            
            candidates.append({
                'cluster_id': f"LEGACY-{label}",
                'analysis': {
                    'centroid': tuple(center), 
                    'num_cylinders': len(cluster_cyls),
                    'avg_radius': avg_rad  
                },
                'validation': {'confidence': 'MEDIUM', 'type': 'CLUSTER_GROUP'}
            })
            
        return candidates, []