# main.py
import sys
import argparse
from src.geometry import GeometryProcessor
from src.analyzer import HeatStakeAnalyzer
from src.visualizer import ResultVisualizer
from src.family_merger import FamilyMerger

def main():
    parser = argparse.ArgumentParser(
        description="Detector Estadístico de Heat Stakes con Sistema de Fusión de Familias"
    )
    parser.add_argument("file", help="Ruta al archivo .step")
    parser.add_argument("--eps", type=float, default=15.0, help="Radio DBSCAN para respaldo")
    parser.add_argument("--view", action="store_true", help="Ver resultados en 3D")
    parser.add_argument("--show-rejected", action="store_true", help="Mostrar candidatos rechazados")
    parser.add_argument("--custom-rules", action="store_true", help="Usar reglas de fusión personalizadas")
    parser.add_argument("--output", default="heat_stakes_coordinates.txt", help="Archivo de salida")
    args = parser.parse_args()

    print("="*70)
    print("🔥 DETECTOR DE HEAT STAKES CON FUSIÓN DE FAMILIAS v2.0")
    print("="*70)

    # ============================================================================
    # 1. CARGAR GEOMETRÍA
    # ============================================================================
    print("\n📂 Cargando geometría...")
    try:
        geo = GeometryProcessor(args.file)
        geo.load_step()
        cylinders = geo.extract_features_topology()
        print(f"✅ Cilindros extraídos: {len(cylinders)}")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return

    # ============================================================================
    # 2. ANÁLISIS ESTADÍSTICO POR FAMILIAS
    # ============================================================================
    print("\n🔬 Iniciando análisis por familias...")
    analyzer = HeatStakeAnalyzer()
    
    # FASE A: Topología por Consenso (con fusión automática de familias)
    topo_stakes, remaining = analyzer.analyze_topology(cylinders)
    
    # FASE B: Clustering de Respaldo (solo lo que sobra)
    cluster_stakes, rejected = analyzer.analyze_clusters_legacy(remaining, eps=args.eps)
    
    all_valid_stakes = topo_stakes + cluster_stakes

    # ============================================================================
    # 3. FUSIÓN PERSONALIZADA (OPCIONAL)
    # ============================================================================
    if args.custom_rules:
        print("\n🔧 Aplicando reglas de fusión personalizadas...")
        merger = FamilyMerger()
        
        # Agregar reglas personalizadas adicionales
        merger.add_fusion_rule('GRP3', 'GRP4', max_distance=22.0)
        merger.add_fusion_rule('GRP4', 'DEFAULT', max_distance=30.0)
        
        # Reorganizar stakes por familia
        family_stakes = {}
        for stake in all_valid_stakes:
            family = stake.get('family_id', 'DEFAULT')
            if family not in family_stakes:
                family_stakes[family] = []
            family_stakes[family].append(stake)
        
        # Reaplicar fusiones con reglas personalizadas
        all_valid_stakes = merger.merge_all_families(family_stakes)
        merger.print_fusion_summary(all_valid_stakes)

    # ============================================================================
    # 4. RESUMEN DE RESULTADOS
    # ============================================================================
    print("\n" + "="*70)
    print("📊 RESUMEN DE DETECCIÓN")
    print("="*70)
    print(f"✅ Heat Stakes detectados: {len(all_valid_stakes)}")
    print(f"   └─ Por topología (familias): {len(topo_stakes)}")
    print(f"   └─ Por clustering (respaldo): {len(cluster_stakes)}")
    print(f"❌ Candidatos rechazados: {len(rejected)}")
    
    # Estadísticas por tipo
    by_type = {}
    merged_count = 0
    for stake in all_valid_stakes:
        family = stake.get('family_id', 'UNKNOWN')
        if family not in by_type:
            by_type[family] = []
        by_type[family].append(stake)
        
        if family == 'MERGED':
            merged_count += 1
    
    print(f"\n📈 Distribución por tipo:")
    for family, stakes in sorted(by_type.items()):
        print(f"   {family}: {len(stakes)} heat stakes")
        
        if family == 'MERGED':
            # Desglosar tipos de fusión
            fusion_types = {}
            for stake in stakes:
                ftype = '+'.join(sorted(stake.get('original_families', [])))
                if ftype not in fusion_types:
                    fusion_types[ftype] = 0
                fusion_types[ftype] += 1
            
            for ftype, count in fusion_types.items():
                print(f"      └─ {ftype}: {count}")
    
    if merged_count > 0:
        print(f"\n🟣 Total de familias fusionadas: {merged_count}")
        print("   (Se visualizarán en color MORADO)")

    # ============================================================================
    # 5. VISUALIZACIÓN Y EXPORTACIÓN
    # ============================================================================
    if geo.shape:
        viz = ResultVisualizer(geo.shape, all_valid_stakes, rejected)
        
        # Exportar reporte detallado
        print(f"\n💾 Exportando reporte a: {args.output}")
        viz.export_report(args.output)
        
        # Visualización 3D
        if args.view:
            print("\n🎨 Iniciando visualización 3D...")
            print("\n" + "="*70)
            print("GUÍA DE COLORES")
            print("="*70)
            print("🟢 Verde (GRP1)  : Familia principal sin fusionar")
            print("🔵 Azul (GRP2)   : Familia secundaria sin fusionar")
            print("🟣 MORADO (MERGED): ⭐ FAMILIAS FUSIONADAS ⭐")
            print("                    - Verde + Azul (GRP1+GRP2)")
            print("                    - Azul + Naranja (GRP2+DEFAULT)")
            print("                    - Múltiples Verdes (GRP1+GRP1)")
            print("                    - Múltiples Azules (GRP2+GRP2)")
            print("🟡 Amarillo      : Otras familias")
            print("🟠 Naranja       : Sin clasificar")
            print("\n💡 TIP: Los marcadores MORADOS son más grandes (6mm)")
            print("="*70)
            
            viz.show_3d(show_rejected=args.show_rejected)
    
    print("\n✅ Proceso completado exitosamente!")
    print("="*70)


def print_usage_examples():
    """Imprime ejemplos de uso del script"""
    print("""

3. Mostrar también candidatos rechazados:
   python main.py pieza.step --view --show-rejected


Para modificar distancias de fusión, edita src/family_merger.py:

    self.merge_rules = {
        'GRP1+GRP2': 20.0,      # Verde + Azul
        'GRP2+DEFAULT': 25.0,   # Azul + Naranja
        'GRP1+GRP1': 30.0,      # Múltiples verdes
        'GRP2+GRP2': 25.0,      # Múltiples azules
    }

Para agregar nuevas combinaciones en tiempo de ejecución, usa --custom-rules

═══════════════════════════════════════════════════════════════════════════
    """)


if __name__ == "__main__":
    if len(sys.argv) == 1 or '--help' in sys.argv or '-h' in sys.argv:
        print_usage_examples()
    main()