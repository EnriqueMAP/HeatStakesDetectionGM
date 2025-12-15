# run_process.py
import sys
import argparse
from src.geometry import GeometryProcessor
from src.analyzer import HeatStakeAnalyzer
from src.visualizer import ResultVisualizer
from src.family_merger import FamilyMerger

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Ruta al archivo STEP")
    parser.add_argument("--view", action="store_true")
    parser.add_argument("--show-rejected", action="store_true")
    parser.add_argument("--custom-rules", action="store_true")
    args = parser.parse_args()

    print(f"⚙️ Procesando: {args.file}")
    
    try:
        # 1. Geometría
        geo = GeometryProcessor(args.file)
        geo.load_step()
        cylinders = geo.extract_features_topology()

        # 2. Análisis
        analyzer = HeatStakeAnalyzer()
        topo, remaining = analyzer.analyze_topology(cylinders)
        cluster, rejected = analyzer.analyze_clusters_legacy(remaining)
        all_valid = topo + cluster

        # 3. Fusión
        if args.custom_rules:
            merger = FamilyMerger()
            by_fam = {}
            for s in all_valid:
                fam = s.get('family_id', 'DEFAULT')
                if fam not in by_fam: by_fam[fam] = []
                by_fam[fam].append(s)
            all_valid = merger.merge_all_families(by_fam)

        print(f"✅ Detección finalizada. Encontrados: {len(all_valid)}")

        # 4. Visualización y Reporte
        if args.view:
            viz = ResultVisualizer(geo.shape, all_valid, rejected)
            viz.export_reports(args.file) # Generar Excel
            viz.show_3d(show_rejected=args.show_rejected)

    except Exception as e:
        print(f"❌ Error crítico en el proceso: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()