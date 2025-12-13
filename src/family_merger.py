# src/family_merger.py
import numpy as np
from itertools import combinations
class FamilyMerger:
    """
    Sistema completo para fusionar diferentes familias de heat stakes
    según reglas configurables y calcular centros de gravedad.
    """
    
    def __init__(self):
        # Distancias de fusión por tipo de combinación
        self.merge_rules = {
            'GRP1+GRP2': 20.0,      # Verde + Azul
            'GRP2+DEFAULT': 25.0,   # Azul + Naranja
            'GRP1+GRP1': 30.0,      # Verde + Verde
            'GRP2+GRP2': 25.0,      # Azul + Azul (múltiples)
            'GRP3+GRP3': 25.0,      # Magenta + Magenta
        }
        
        # Prioridad de fusión (se procesan en este orden)
        self.fusion_priority = [
            ['GRP1', 'GRP2'],        # Verde + Azul (más común)
            ['GRP2', 'DEFAULT'],     # Azul + Naranja
            ['GRP1', 'GRP1'],        # Múltiples verdes
            ['GRP2', 'GRP2'],        # Múltiples azules
        ]
        
    def merge_all_families(self, family_stakes):
        """
        Fusiona todas las familias según las reglas definidas.
        
        Args:
            family_stakes: Dict {family_id: [stakes]}
            
        Returns:
            Lista de stakes fusionados con centros de gravedad calculados
        """
        print(f"\n🔗 Sistema de fusión de familias iniciado...")
        
        all_stakes = []
        used_stakes = set()  # Rastrear stakes ya fusionados
        
        # Asignar IDs únicos a todos los stakes
        stake_id_map = {}
        stake_counter = 0
        for family_id, stakes in family_stakes.items():
            for stake in stakes:
                stake_id = f"{family_id}_{stake_counter}"
                stake_id_map[stake_id] = stake
                stake_counter += 1
        
        # Procesar cada regla de fusión en orden de prioridad
        for families_to_merge in self.fusion_priority:
            merged = self._process_fusion_rule(
                families_to_merge, 
                family_stakes, 
                stake_id_map,
                used_stakes
            )
            all_stakes.extend(merged)
        
        # Agregar stakes no fusionados
        for stake_id, stake in stake_id_map.items():
            if stake_id not in used_stakes:
                all_stakes.append(stake)
        
        print(f"✅ Total de heat stakes finales: {len(all_stakes)}")
        return all_stakes
    
    def _process_fusion_rule(self, families_to_merge, family_stakes, stake_id_map, used_stakes):
        """
        Procesa una regla de fusión específica.
        """
        family1, family2 = families_to_merge
        rule_key = f"{family1}+{family2}"
        max_distance = self.merge_rules.get(rule_key, 20.0)
        
        stakes1 = family_stakes.get(family1, [])
        stakes2 = family_stakes.get(family2, [])
        
        if not stakes1 or not stakes2:
            return []
        
        # Caso especial: fusión de la misma familia (ej: GRP1+GRP1)
        if family1 == family2:
            return self._merge_same_family(
                family1, stakes1, stake_id_map, used_stakes, max_distance
            )
        
        # Caso general: fusión de familias diferentes
        return self._merge_different_families(
            family1, family2, stakes1, stakes2, 
            stake_id_map, used_stakes, max_distance
        )
    
    def _merge_different_families(self, family1, family2, stakes1, stakes2, 
                                   stake_id_map, used_stakes, max_distance):
        """
        Fusiona stakes de dos familias diferentes que estén cerca.
        """
        merged_stakes = []
        
        print(f"\n   🔍 Buscando fusiones: {family1} + {family2} (distancia máx: {max_distance}mm)")
        
        # Encontrar IDs de stakes
        stakes1_ids = self._find_stake_ids(stakes1, stake_id_map, used_stakes)
        stakes2_ids = self._find_stake_ids(stakes2, stake_id_map, used_stakes)
        
        # Comparar cada stake de family1 con cada stake de family2
        for id1 in stakes1_ids:
            stake1 = stake_id_map[id1]
            centroid1 = np.array(stake1['analysis']['centroid'])
            
            closest_id2 = None
            min_distance = float('inf')
            
            for id2 in stakes2_ids:
                if id2 in used_stakes:
                    continue
                
                stake2 = stake_id_map[id2]
                centroid2 = np.array(stake2['analysis']['centroid'])
                distance = np.linalg.norm(centroid1 - centroid2)
                
                if distance < min_distance and distance < max_distance:
                    min_distance = distance
                    closest_id2 = id2
            
            if closest_id2:
                # ⭐⭐⭐ FUSIONAR STAKES ⭐⭐⭐
                stake2 = stake_id_map[closest_id2]
                merged = self._create_merged_stake(
                    [stake1, stake2],
                    [family1, family2],
                    min_distance
                )
                
                merged_stakes.append(merged)
                used_stakes.add(id1)
                used_stakes.add(closest_id2)
                
                print(f"      ✅ Fusionados: {stake1['cluster_id']} + {stake2['cluster_id']}")
                print(f"         Distancia: {min_distance:.2f}mm | Cilindros: {merged['analysis']['num_cylinders']}")
        
        return merged_stakes
    
    def _merge_same_family(self, family_id, stakes, stake_id_map, used_stakes, max_distance):
        """
        Fusiona múltiples stakes de la misma familia que estén cerca.
        """
        merged_stakes = []
        
        print(f"\n   🔍 Buscando múltiples {family_id} cercanos (distancia máx: {max_distance}mm)")
        
        stake_ids = self._find_stake_ids(stakes, stake_id_map, used_stakes)
        
        while stake_ids:
            # Tomar el primer stake disponible
            base_id = stake_ids.pop(0)
            if base_id in used_stakes:
                continue
                
            base_stake = stake_id_map[base_id]
            base_centroid = np.array(base_stake['analysis']['centroid'])
            
            # Buscar todos los stakes cercanos
            group = [base_stake]
            group_ids = [base_id]
            
            ids_to_remove = []
            for other_id in stake_ids:
                if other_id in used_stakes:
                    continue
                
                other_stake = stake_id_map[other_id]
                other_centroid = np.array(other_stake['analysis']['centroid'])
                distance = np.linalg.norm(base_centroid - other_centroid)
                
                if distance < max_distance:
                    group.append(other_stake)
                    group_ids.append(other_id)
                    ids_to_remove.append(other_id)
            
            # Remover stakes usados
            for id_to_remove in ids_to_remove:
                stake_ids.remove(id_to_remove)
            
            # Si hay más de un stake en el grupo, fusionar
            if len(group) > 1:
                merged = self._create_merged_stake(
                    group,
                    [family_id] * len(group),
                    distance=0  # No aplica distancia específica
                )
                merged_stakes.append(merged)
                
                for gid in group_ids:
                    used_stakes.add(gid)
                
                stake_names = ' + '.join([s['cluster_id'] for s in group])
                print(f"      ✅ Fusionados {len(group)} stakes: {stake_names}")
                print(f"         Cilindros totales: {merged['analysis']['num_cylinders']}")
        
        return merged_stakes
    
    def _create_merged_stake(self, stakes_to_merge, original_families, distance):
        """
        ⭐⭐⭐ Crea un stake fusionado con centro de gravedad calculado ⭐⭐⭐
        """
        # Combinar todos los cilindros
        all_cylinders = []
        for stake in stakes_to_merge:
            all_cylinders.extend(stake.get('cylinders', []))
        
        # ⭐ CALCULAR CENTRO DE GRAVEDAD ⭐
        positions = np.array([c['center'] for c in all_cylinders])
        centroid = np.mean(positions, axis=0)
        
        # Calcular distancias desde el centro de gravedad
        distances = np.linalg.norm(positions - centroid, axis=1)
        max_spread = np.max(distances)
        
        # Métricas combinadas
        all_radii = [c['radius'] for c in all_cylinders]
        avg_radius = np.mean(all_radii)
        
        all_planes = [stake['analysis'].get('connected_planes', 0) for stake in stakes_to_merge]
        max_planes = max(all_planes) if all_planes else 0
        
        # Generar ID único
        unique_families = list(set(original_families))
        family_str = '+'.join(unique_families)
        merged_id = f"MERGED-{family_str}-{id(stakes_to_merge)%1000}"
        
        return {
            'cluster_id': merged_id,
            'family_id': 'MERGED',
            'original_families': unique_families,
            'cylinders': all_cylinders,
            'analysis': {
                'centroid': tuple(centroid),  # ⭐ Centro de gravedad
                'num_cylinders': len(all_cylinders),
                'avg_radius': avg_radius,
                'max_spread': max_spread,
                'connected_planes': int(max_planes)
            },
            'validation': {
                'confidence': 'HIGH',
                'type': 'MERGED_FAMILIES',
                'score': 6.0 + len(stakes_to_merge) * 0.5,
                'merge_distance': distance if distance > 0 else None,
                'num_merged': len(stakes_to_merge)
            }
        }
    
    def _find_stake_ids(self, stakes, stake_id_map, used_stakes):
        """
        Encuentra los IDs de stakes en el mapa que no han sido usados.
        """
        stake_ids = []
        for stake in stakes:
            for sid, mapped_stake in stake_id_map.items():
                if (sid not in used_stakes and 
                    mapped_stake['cluster_id'] == stake['cluster_id']):
                    stake_ids.append(sid)
                    break
        return stake_ids
    
    def add_fusion_rule(self, family1, family2, max_distance):
        """
        Agrega una nueva regla de fusión personalizada.
        
        Args:
            family1: ID de la primera familia (ej: 'GRP1')
            family2: ID de la segunda familia (ej: 'GRP2')
            max_distance: Distancia máxima para considerar fusión (mm)
        """
        rule_key = f"{family1}+{family2}"
        self.merge_rules[rule_key] = max_distance
        
        # Agregar a prioridad si no existe
        rule = [family1, family2]
        if rule not in self.fusion_priority:
            self.fusion_priority.append(rule)
        
        print(f"✅ Nueva regla agregada: {rule_key} con distancia {max_distance}mm")
    
    def print_fusion_summary(self, merged_stakes):
        """
        Imprime un resumen de las fusiones realizadas.
        """
        print("\n" + "="*60)
        print("📊 RESUMEN DE FUSIONES")
        print("="*60)
        
        by_type = {}
        for stake in merged_stakes:
            if stake['family_id'] == 'MERGED':
                families = '+'.join(sorted(stake['original_families']))
                if families not in by_type:
                    by_type[families] = []
                by_type[families].append(stake)
        
        for fusion_type, stakes in by_type.items():
            print(f"\n🔹 Tipo: {fusion_type}")
            print(f"   Cantidad: {len(stakes)}")
            
            total_cylinders = sum(s['analysis']['num_cylinders'] for s in stakes)
            avg_cylinders = total_cylinders / len(stakes)
            print(f"   Cilindros promedio: {avg_cylinders:.1f}")
            
            for stake in stakes:
                c = stake['analysis']['centroid']
                num_cyl = stake['analysis']['num_cylinders']
                print(f"      • {stake['cluster_id']}: {num_cyl} cilindros en ({c[0]:.1f}, {c[1]:.1f}, {c[2]:.1f})")
        
        print("\n" + "="*60)