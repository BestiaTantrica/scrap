"""
=============================================================
  GENERADOR DE REPORTES PDF — El Producto Digital
  Crea estudios de mercado esteticos para venta automatica.
=============================================================
"""
from fpdf import FPDF
import os
from datetime import datetime

class ReporteInmobiliario(FPDF):
    def header(self):
        # Fondo oscuro en la cabecera
        self.set_fill_color(15, 23, 42) # Slate 900
        self.rect(0, 0, 210, 40, 'F')
        
        # Logo o Texto principal
        self.set_y(10)
        self.set_font('Helvetica', 'B', 22)
        self.set_text_color(56, 189, 248) # Sky 400
        self.cell(0, 10, 'RADAR PRO', 0, 1, 'C')
        
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'INTELIGENCIA INMOBILIARIA AUTONOMA', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f'Reporte Confidencial - RADAR PRO v2.0 - Generado el {datetime.now().strftime("%d/%m/%Y")}', 0, 0, 'C')
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'R')

def generar_pdf_estudio(zona, data_intel, oportunidades, es_premium=False):
    pdf = ReporteInmobiliario()
    pdf.add_page()
    
    # TITULO Y SCORE (Caja Estetica)
    pdf.set_y(45)
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 15, f"Estudio de Mercado: {zona.upper()}", 0, 1, 'L')
    
    score = data_intel.get('zona_score', 0)
    label = data_intel.get('zona_score_label', 'Estable')
    
    # Widget de Score
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(56, 189, 248)
    pdf.rect(10, 65, 190, 30, 'DF')
    
    pdf.set_y(68)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 10, "CONFIANZA DE INVERSION (ZONA SCORE)", 0, 1, 'C')
    
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(2, 132, 199)
    pdf.cell(0, 12, f"{score}/100 - {label.upper()}", 0, 1, 'C')
    
    # TENDENCIAS
    pdf.ln(10)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, "1. ANALISIS DE DEMANDA DIGITAL", 0, 1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(0, 6, data_intel['capas']['trends']['interpretacion'])
    
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, "2. ENTORNO Y OPORTUNIDAD", 0, 1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(0, 6, data_intel['capas']['eventos']['interpretacion'])

    # TABLA DE PROPIEDADES (ESTILO PRO)
    pdf.ln(10)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(14, 165, 233) # Sky 500
    pdf.cell(0, 10, "3. SELECCION DE ACTIVOS DE ALTA RENTABILIDAD", 0, 1)
    
    for i, op in enumerate(oportunidades[:10], 1):
        # Caja para cada propiedad
        pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(226, 232, 240)
        pdf.rect(10, pdf.get_y(), 190, 25, 'D')
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(15, 23, 42)
        pdf.set_x(12)
        pdf.cell(100, 8, f"{i}. {op['precio']} - {op['fuente']}", 0, 0)
        
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(220, 38, 38) # Rojo urgencia
        pdf.cell(0, 8, f"Score Urgencia: {op['score_urgencia']}/100", 0, 1, 'R')
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(71, 85, 105)
        pdf.set_x(12)
        pdf.multi_cell(180, 5, f"{op['descripcion'][:150]}...")
        
        if es_premium:
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(2, 132, 199)
            pdf.set_x(12)
            pdf.cell(0, 5, f"URL DE CONTACTO: {op['link']}", 0, 1)
        else:
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(148, 163, 184)
            pdf.set_x(12)
            pdf.cell(0, 5, "[LINK CENSURADO - REQUIERE ACCESO PREMIUM]", 0, 1)
        
        pdf.ln(5)

    # GUARDAR
    os.makedirs("reportes_generados", exist_ok=True)
    tipo = "PREMIUM" if es_premium else "TEASER"
    filename = f"reportes_generados/estudio_{zona}_{tipo}_{datetime.now().strftime('%H%M%S')}.pdf"
    pdf.output(filename)
    return filename

if __name__ == "__main__":
    # Prueba rapida
    mock_intel = {
        "zona_score": 85, "zona_score_label": "Alta Urgencia",
        "capas": {
            "trends": {"interpretacion": "Demanda subiendo un 15% este mes."},
            "eventos": {"interpretacion": "Zona con 12 eventos culturales proximos."}
        }
    }
    generar_pdf_estudio("Palermo", mock_intel, [{"precio": "USD 120.000", "fuente": "Zonaprop", "descripcion": "Venta urgente dueño directo", "link": "http://link.com"}])
