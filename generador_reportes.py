"""
=============================================================
  GENERADOR DE REPORTES PREMIUM v1.1 — MIGRACION_SCRAPING_CASH
  Transforma JSON en Excel de Grado Profesional (ASCII Safe)
=============================================================
"""

import pandas as pd
import json
import os
from datetime import datetime

def generar_excel(json_file='resultados_radar.json', output_file='REPORTE_PRO_INMOBILIARIO.xlsx'):
    print(f"[*] Generando reporte profesional desde {json_file}...")
    
    if not os.path.exists(json_file):
        print("[!] Error: No se encontró el archivo de resultados.")
        return

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Error leyendo JSON: {e}")
        return

    if not data:
        print("[!] El archivo está vacío.")
        return

    df = pd.DataFrame(data)

    # Reordenar y Renombrar Columnas (Evitando caracteres especiales en el código)
    # Mapeo: 'columna_json': 'Nombre en Excel'
    mapping = {
        'etiqueta': 'ESTADO',
        'zona': 'ZONA',
        'precio': 'PRECIO',
        'score_urgencia': 'SCORE',
        'titulo': 'DETALLE',
        'link': 'URL_ZONAPROP'
    }
    
    # Solo renombramos lo que existe
    df = df.rename(columns=mapping)
    
    # Si existe la columna 'señales', la renombramos a 'NOTAS'
    if 'señales' in df.columns:
        df = df.rename(columns={'señales': 'NOTAS'})
    elif 'senales' in df.columns:
        df = df.rename(columns={'senales': 'NOTAS'})

    # Columnas finales que queremos en el Excel
    cols_to_keep = ['ESTADO', 'ZONA', 'PRECIO', 'SCORE', 'DETALLE', 'URL_ZONAPROP']
    if 'NOTAS' in df.columns:
        cols_to_keep.append('NOTAS')

    df = df[cols_to_keep]

    # Crear el Excel con formato
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Oportunidades')
            
            workbook = writer.book
            worksheet = writer.sheets['Oportunidades']

            # Estilos Básicos
            from openpyxl.styles import PatternFill, Font, Alignment
            
            header_fill = PatternFill(start_color="003366", end_color="003366", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            # Ajustar ancho de columnas
            for col in worksheet.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if cell.value and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except: pass
                worksheet.column_dimensions[column].width = min(max_length + 2, 60)

        print(f"[OK] Reporte generado con éxito: {output_file}")
    except Exception as e:
        print(f"[!] Error creando Excel: {e}")

if __name__ == "__main__":
    generar_excel()
