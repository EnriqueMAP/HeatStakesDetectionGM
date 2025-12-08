# main.py
import sys
import argparse
from src.geometry import GeometryProcessor
from src.analyzer import HeatStakeAnalyzer
from src.visualizer import ResultVisualizer

def main():
    parser = argparse.ArgumentParser(description="Detector Modular de Heat Stakes")
    parser.add_argument("file", help="Ruta al archivo .step")
    # Parámetros por defecto coinciden con el original
    parser.add_argument("--eps", type=float, default=25.0, help="Radio de búsqueda DBSCAN (mm)")
    parser.add_argument("--min-samples", type=int, default=5, help="Mínimo de cilindros por grupo")
    parser.add_argument("--strict", action="store_true", help="Activar modo estricto (7+/-2 cilindros)")
    
    parser.add_argument("--view", action="store_true", help="Ver en 3D al finalizar")
    parser.add_argument("--show-rejected", action="store_true", help="Mostrar clusters descartados")
    
    args = parser.parse_args()

    # 1. Procesar Geometría
    try:
        geo = GeometryProcessor(args.file)
        geo.load_step() # Carga explícita
        cylinders = geo.extract_features()
    except Exception as e:
        print(f"❌ Error crítico cargando geometría: {e}")
        return
    
    if not cylinders:
        print("❌ No se encontraron cilindros en el archivo.")
        return

    # 2. Análisis
    # Pasamos strict_mode desde los argumentos
    analyzer = HeatStakeAnalyzer(strict_mode=args.strict)
    
    # Pasamos eps y min_samples del usuario
    clusters = analyzer.cluster_data(cylinders, eps=args.eps, min_samples=args.min_samples)
    
    if not clusters:
        print("⚠️ No se formaron clusters. Intenta aumentar --eps o reducir --min-samples")
        return

    valid_stakes, rejected = analyzer.analyze_candidates(clusters, cylinders)

    # 3. Resultados
    print(f"\n✅ Resultados Finales:")
    print(f"   Heat Stakes Válidos: {len(valid_stakes)}")
    print(f"   Clusters Rechazados: {len(rejected)}")
    
    # Exportar coordenadas
    if geo.shape:
        viz = ResultVisualizer(geo.shape, valid_stakes, rejected)
        viz.export_report("heat_stakes_coordinates.txt")

        # 4. Visualización
        if args.view:
            viz.show_3d(show_rejected=args.show_rejected)

if __name__ == "__main__":
    main()