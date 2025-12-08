# src/analyzer.py
import numpy as np
from sklearn.cluster import DBSCAN
from collections import defaultdict

class HeatStakeAnalyzer:
    def __init__(self, strict_mode=False):
        # Configuración de detección
        self.STRICT_MODE = strict_mode
        self.MIN_CYLINDERS = 5
        self.MAX_CYLINDERS = 25
        self.TARGET_CYLINDERS = 7
        
        # Parámetros físicos (Filtros)
        self.MIN_SPREAD = 8.0
        self.MAX_RADIUS = 5.0
        self.MIN_HEIGHT = 8.0
        
        self.USE_SMART_FILTERING = True
        self.SCORE_THRESHOLD = 0.86 # 4.3 de 5.0 puntos

    def cluster_data(self, cylinders, eps=25.0, min_samples=5):
        """Agrupa cilindros usando DBSCAN"""
        print(f"\n🔬 Agrupando datos (eps={eps}, min={min_samples})...")
        
        if not cylinders:
            return {}

        centers = np.array([c['center'] for c in cylinders])
        clustering = DBSCAN(eps=eps, min_samples=min_samples)
        labels = clustering.fit_predict(centers)
        
        clusters = defaultdict(list)
        for idx, label in enumerate(labels):
            if label != -1:
                clusters[label].append(idx)
                
        return clusters

    def analyze_candidates(self, clusters, all_cylinders):
        """Evalúa cada cluster con la lógica EXACTA del original"""
        candidates = []
        rejected = []
        
        print(f"📊 Analizando {len(clusters)} clusters...")
        
        for cluster_id, indices in sorted(clusters.items()):
            cluster_cyls = [all_cylinders[i] for i in indices]
            analysis = self._calculate_cluster_stats(cluster_cyls)
            validation = self._validate_cluster(analysis)
            
            result = {
                'cluster_id': cluster_id,
                'analysis': analysis,
                'validation': validation
            }
            
            if validation['is_heat_stake']:
                candidates.append(result)
            else:
                rejected.append(result)
                
        return candidates, rejected

    def _calculate_cluster_stats(self, cylinders):
        """Matemáticas del cluster"""
        centers = np.array([c['center'] for c in cylinders])
        centroid = centers.mean(axis=0)
        
        # Spread
        distances = np.linalg.norm(centers - centroid, axis=1)
        
        # Dimensiones (Bounding Box)
        min_c = centers.min(axis=0)
        max_c = centers.max(axis=0)
        dims = max_c - min_c
        bbox_vol = np.prod(dims) if np.all(dims > 0) else 0
        
        # Orientación
        directions = np.array([c['direction'] for c in cylinders])
        dir_std = np.std(directions, axis=0).sum()
        
        return {
            'num_cylinders': len(cylinders),
            'centroid': tuple(centroid),
            'max_spread': distances.max(),
            'avg_radius': np.mean([c['radius'] for c in cylinders]),
            'avg_height': np.mean([c['height'] for c in cylinders]),
            'max_height': np.max([c['height'] for c in cylinders]),
            'bbox_volume': bbox_vol,
            'direction_std': dir_std,
            'cylinders': cylinders
        }

    def _validate_cluster(self, stats):
        """
        Aplica Scoring Multi-Criterio.
        RESTAURADO AL 100% DEL ORIGINAL.
        """
        num_cyl = stats['num_cylinders']
        spread = stats['max_spread']
        avg_radius = stats['avg_radius']
        avg_height = stats['avg_height']
        max_height = stats['max_height']
        direction_std = stats['direction_std']
        bbox_volume = stats['bbox_volume']

        # VALIDACIÓN 1: Número de cilindros
        cyl_valid = False
        confidence_level = 'LOW'
        
        if self.STRICT_MODE:
            cyl_valid = abs(num_cyl - self.TARGET_CYLINDERS) <= 2
            confidence_level = 'HIGH' if cyl_valid else 'LOW'
        else:
            if self.MIN_CYLINDERS <= num_cyl <= self.MAX_CYLINDERS:
                cyl_valid = True
                diff = abs(num_cyl - self.TARGET_CYLINDERS)
                if diff <= 2: confidence_level = 'HIGH'
                elif diff <= 5: confidence_level = 'MEDIUM'
                else: confidence_level = 'LOW'
            else:
                cyl_valid = False
                confidence_level = 'REJECTED'

        # SISTEMA DE SCORING (Restaurado)
        score = 0.0
        max_score = 5.0
        reasons = []

        # 1. Spread (1.0 pts)
        spread_valid = True
        if spread >= 15.0: score += 1.0
        elif spread >= 9.0: score += 0.9
        elif spread >= 7.0: score += 0.5
        else:
            spread_valid = False
            reasons.append(f"Compacto ({spread:.2f}mm)")

        # 2. Radio (1.0 pts)
        radius_valid = True
        if avg_radius <= 3.0: score += 1.0
        elif avg_radius <= self.MAX_RADIUS: score += 0.7
        elif avg_radius <= 8.0: score += 0.3 # Faltaba esto
        else:
            radius_valid = False
            reasons.append(f"Radio grande ({avg_radius:.2f}mm)")

        # 3. Altura (1.0 pts)
        height_valid = True
        if max_height > 15.0 or avg_height > 10.0: score += 1.0
        elif max_height > 10.0 or avg_height > self.MIN_HEIGHT: score += 0.7
        elif max_height > 5.0 or avg_height > 5.0: score += 0.3 # Faltaba esto
        else:
            height_valid = False
            reasons.append(f"Muy plano ({avg_height:.2f}mm)")

        # 4. Orientación (1.0 pts)
        orientation_valid = True
        if direction_std > 0.1: score += 1.0
        elif direction_std > 0.05: score += 0.7
        elif direction_std > 0.02: score += 0.3 # Faltaba esto
        else:
            orientation_valid = False
            reasons.append(f"Paralelos (std={direction_std:.4f})")

        # 5. Densidad (0.5 pts) - Faltaba completamente
        density_valid = True
        density = 0
        if bbox_volume > 0:
            density = num_cyl / bbox_volume * 1000
            if density > 0.5: score += 0.5
            elif density > 0.1: score += 0.3
            else: density_valid = False
        else:
            score += 0.3 # Caso bbox cero

        # 6. Número Ideal (0.5 pts) - Faltaba completamente
        if num_cyl == 7: score += 0.5
        elif 5 <= num_cyl <= 9: score += 0.3

        # Detección de Agujeros (Hole) - Lógica original compleja
        is_hole = (
            (spread < 8.0 and direction_std < 0.02) or
            (spread < 10.0 and direction_std < 0.01 and avg_height < 8.0) or
            (avg_radius > 8.0 and direction_std < 0.05)
        )

        # Decisión Final
        if self.USE_SMART_FILTERING:
            threshold = max_score * self.SCORE_THRESHOLD
            is_valid = (score >= threshold and cyl_valid and not is_hole)
            
            # Recalcular confianza basado en score final
            if is_valid:
                ratio = score / max_score
                if ratio >= 0.85: confidence_level = 'HIGH'
                elif ratio >= 0.70: confidence_level = 'MEDIUM'
                else: confidence_level = 'LOW'
        else:
            is_valid = (cyl_valid and spread_valid and radius_valid and 
                        height_valid and orientation_valid and density_valid and 
                        not is_hole)

        if is_hole:
            confidence_level = 'REJECTED_HOLE'
            is_valid = False

        return {
            'is_heat_stake': is_valid,
            'confidence': confidence_level,
            'score': score,
            'max_score': max_score,
            'is_likely_hole': is_hole,
            'rejection_reasons': reasons,
            'details': {
                'spread': spread,
                'cylinders': num_cyl,
                'avg_radius': avg_radius
            }
        }