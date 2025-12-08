# diagnostic.py
import sys
import pandas as pd
from src.geometry import GeometryProcessor

def run_diagnostic(step_file):
    print(f"🕵️  DIAGNÓSTICO PROFUNDO: {step_file}")
    print("="*60)
    
    geo = GeometryProcessor(step_file)
    try:
        geo.load_step()
        # Usamos la extracción topológica que ya tienes
        cylinders = geo.extract_features_topology()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        return

    print(f"\n📊 Generando reporte de {len(cylinders)} geometrías encontradas...")
    
    data = []
    for i, c in enumerate(cylinders):
        data.append({
            'ID': i,
            'X': c['center'][0],
            'Y': c['center'][1],
            'Z': c['center'][2],
            'Radio (mm)': round(c['radius'], 4),
            'Altura (mm)': round(c['height'], 4),
            'Aletas_Detectadas': c['connected_planes'], # ¡El dato clave!
            'Es_HeatStake_Potencial': c['connected_planes'] >= 3
        })
    
    # Crear DataFrame y exportar
    df = pd.DataFrame(data)
    
    # Ordenar por distancia al origen (para encontrar el lejano fácil)
    df['Distancia_Origen'] = (df['X']**2 + df['Y']**2 + df['Z']**2)**0.5
    df = df.sort_values('Distancia_Origen', ascending=False)
    
    output_file = "diagnostico_geometria.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\n💾 Reporte guardado en: {output_file}")
    print("\n🔍 TOP 5 - POSIBLES HEAT STAKES FLOTANTES (Más lejanos):")
    print(df.head(5)[['ID', 'Radio (mm)', 'Aletas_Detectadas', 'Distancia_Origen', 'X', 'Y', 'Z']].to_string())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python diagnostic.py <archivo.step>")
    else:
        run_diagnostic(sys.argv[1])