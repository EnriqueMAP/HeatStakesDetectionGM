# diagnostico.py
"""
Script de diagnóstico para verificar por qué la fusión no funciona.
Ejecuta: python diagnostico.py tu_archivo.step
"""
import sys
import argparse
from src.geometry import GeometryProcessor
from src.analyzer import HeatStakeAnalyzer
import numpy as np

def distance_xz(p1, p2):
    """Distancia en plano horizontal."""
    dx = p1[0] - p2[0]
    dz = p1[2] - p2[2]
    return np.sqrt(dx**2 + dz**2)

def main():
    parser = argparse.ArgumentParser(description="Diagnóstico de Fusión")
    parser.add_argument("file", help="Archivo .step")
    args = parser.parse_args()
    
    print("=" * 80)
    print("🔍 DIAGNÓSTICO DE FUSIÓN DE HEAT STAKES")
    print("=" * 80)
    
    # Cargar geometría
    print("\n[1] Cargando geometría...")
    try:
        geo = GeometryProcessor(args.file)
        geo.load_step()
        cylinders = geo.extract_features_topology()
        print(f"✓ Cilindros: {len(cylinders)}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    # Analizar familias
    print("\n[2] Detectando familias...")
    analyzer = HeatStakeAnalyzer()
    topo_stakes, remaining = analyzer.analyze_topology(cylinders)
    cluster_stakes, _ = analyzer.analyze_clusters_legacy(remaining, eps=15.0)
    
    all_stakes = topo_stakes + cluster_stakes
    print(f"✓ Familias detectadas: {len(all_stakes)}")
    
    if not all_stakes:
        print("❌ No se detectaron familias. Fin del diagnóstico.")
        return 0
    
    # Análisis detallado
    print("\n[3] Analizando posiciones y distancias...")
    print("=" * 80)
    
    for i, stake in enumerate(all_stakes):
        c = stake['analysis']['centroid']
        fam = stake.get('family_id', stake['cluster_id'])
        rad = stake['analysis'].get('avg_radius', 0)
        
        print(f"\n[{i+1}] {stake['cluster_id']} (Familia: {fam})")
        print(f"    Centroide: X={c[0]:8.2f}, Y={c[1]:8.2f}, Z={c[2]:8.2f}")
        print(f"    Radio promedio: {rad:.2f} mm")
        print(f"    Cilindros: {stake['analysis'].get('num_cylinders', 0)}")
    
    # Matriz de distancias
    print("\n" + "=" * 80)
    print("\n[4] Matriz de Distancias (para detectar pares):")
    print("=" * 80)
    print("\nCriterios de fusión:")
    print("   • Distancia XZ < 12.0 mm")
    print("   • Diferencia Y < 8.0 mm")
    print("   • Diferencia Z < 40.0 mm")
    print("\n" + "-" * 80)
    
    found_pairs = []
    
    for i, stake_a in enumerate(all_stakes):
        ca = stake_a['analysis']['centroid']
        
        for j, stake_b in enumerate(all_stakes):
            if i >= j:  # Evitar duplicados
                continue
            
            cb = stake_b['analysis']['centroid']
            
            dist_xz = distance_xz(ca, cb)
            dist_y = abs(ca[1] - cb[1])
            dist_z = abs(ca[2] - cb[2])
            
            print(f"\n{stake_a['cluster_id']} vs {stake_b['cluster_id']}:")
            print(f"   Distancia XZ: {dist_xz:6.2f} mm {'✓' if dist_xz < 12.0 else '✗'}")
            print(f"   Diferencia Y: {dist_y:6.2f} mm {'✓' if dist_y < 8.0 else '✗'}")
            print(f"   Diferencia Z: {dist_z:6.2f} mm {'✓' if dist_z < 40.0 else '✗'}")
            
            if dist_xz < 12.0 and dist_y < 8.0 and dist_z < 40.0:
                print(f"   ✅ CANDIDATOS A FUSIÓN")
                found_pairs.append((i, j, dist_xz))
            else:
                print(f"   ❌ No cumplen criterios")
    
    # Resumen
    print("\n" + "=" * 80)
    print("\n[5] RESUMEN DEL DIAGNÓSTICO")
    print("=" * 80)
    print(f"\nFamilias totales: {len(all_stakes)}")
    print(f"Pares candidatos a fusión: {len(found_pairs)}")
    
    if found_pairs:
        print("\n✅ Se detectaron pares que DEBERÍAN fusionarse:")
        for idx_a, idx_b, dist in found_pairs:
            print(f"   • {all_stakes[idx_a]['cluster_id']} + {all_stakes[idx_b]['cluster_id']} (dist={dist:.2f}mm)")
        print("\n🔧 La fusión debería funcionar correctamente.")
        print("   Si ves 2 esferas, ejecuta con --debug para más info:")
        print(f"   python main.py {args.file} --view --debug")
    else:
        print("\n⚠️ NO se detectaron pares cercanos.")
        print("\nPosibles causas:")
        print("   1. Las familias están muy separadas (>12mm en XZ)")
        print("   2. Diferentes alturas Y (>8mm de diferencia)")
        print("   3. Muy distantes verticalmente (>40mm en Z)")
        print("\nSoluciones:")
        print("   • Edita src/merger.py y aumenta los límites:")
        print("     self.MAX_DISTANCE_XZ = 20.0  # Aumentar si están lejos")
        print("     self.MAX_DISTANCE_Y = 15.0")
        print("     self.MAX_DISTANCE_Z = 50.0")
    
    print("\n" + "=" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(main())