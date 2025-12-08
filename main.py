# main.py
import sys
import argparse
from src.geometry import GeometryProcessor
from src.analyzer import HeatStakeAnalyzer
from src.visualizer import ResultVisualizer

def main():
    parser = argparse.ArgumentParser(description="Detector Estadístico de Heat Stakes")
    parser.add_argument("file", help="Ruta al archivo .step")
    parser.add_argument("--eps", type=float, default=15.0, help="Radio DBSCAN para respaldo")
    parser.add_argument("--view", action="store_true", help="Ver resultados en 3D")
    args = parser.parse_args()

    # 1. Geometría (Optimizada)
    try:
        geo = GeometryProcessor(args.file)
        geo.load_step()
        cylinders = geo.extract_features_topology()
    except Exception as e:
        print(f"Error crítico: {e}")
        return

    # 2. Análisis Estadístico
    analyzer = HeatStakeAnalyzer()
    
    # FASE A: Topología por Consenso
    topo_stakes, remaining = analyzer.analyze_topology(cylinders)
    
    # FASE B: Clustering de Respaldo (solo lo que sobra)
    cluster_stakes, rejected = analyzer.analyze_clusters_legacy(remaining, eps=args.eps)
    
    all_valid_stakes = topo_stakes + cluster_stakes

    print(f"\n✅ RESULTADOS TOTALES: {len(all_valid_stakes)}")

    # 3. Visualizar Resultados
    if geo.shape:
        viz = ResultVisualizer(geo.shape, all_valid_stakes, rejected)
        viz.export_report("heat_stakes_coordinates.txt")
        if args.view:
            viz.show_3d()

if __name__ == "__main__":
    main()