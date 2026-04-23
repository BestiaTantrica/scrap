"""
=============================================================
  MENSAJERÍA WHATSAPP — Captación de Dueños
  Genera links 'Click-to-Chat' con mensajes pre-armados
  para ofrecer reportes gratis a los dueños.
=============================================================
"""
import os
import glob
import pandas as pd
import urllib.parse

def obtener_oportunidades_wa():
    """Busca propiedades con potencial de contacto directo."""
    archivos = glob.glob(f"resultados/*.xlsx")
    if not archivos: return None
    ultimo = max(archivos, key=os.path.getctime)
    zona = ultimo.split("_")[1].capitalize()
    df = pd.read_excel(ultimo)
    
    # Filtramos dueños urgentes (bajado a 0 temporalmente para demo)
    fuego = df[df['score_urgencia'] > 0]
    return zona, fuego

def generar_links_whatsapp():
    print("Generando Campaña de WhatsApp (Dueños Directos)...")
    res = obtener_oportunidades_wa()
    if not res:
        print("Error: No hay datos.")
        return
        
    zona, df = res
    if df.empty:
        print("Info: No se detectaron dueños urgentes en la última pasada.")
        return

    html_content = f"<html><body style='font-family:sans-serif; padding:20px; background:#0f172a; color:#f8fafc;'>"
    html_content += f"<h2>🎯 Contactos WhatsApp: {zona}</h2>"
    html_content += "<p>Hacé clic en el botón para abrir WhatsApp Web con el mensaje listo.</p>"
    
    # Simulación: en la vida real extraeríamos el teléfono de la publicacion si existe
    # Como los scrapers web a veces no sacan el tel directamente sin clickear,
    # armamos el template para cuando tengas el numero.
    
    for i, row in df.head(10).iterrows():
        precio = row['precio']
        link_pub = row['link']
        
        mensaje = f"Hola, vi tu publicación en la zona de {zona} a {precio}.\n\n"
        mensaje += "Soy de Radar Pro, analizamos el mercado inmobiliario con IA. Noté un detalle en tu precio comparado con la competencia actual del barrio que te está frenando la venta.\n\n"
        mensaje += "Te dejo un reporte gratuito de tu zona acá para que veas por qué no estás vendiendo: http://localhost:5000\n\nAbrazo!"
        
        url_wa = f"https://wa.me/?text={urllib.parse.quote(mensaje)}"
        
        html_content += f"""
        <div style='background:#1e293b; padding:15px; margin-bottom:10px; border-radius:8px; border-left:4px solid #22c55e;'>
            <strong>Oportunidad: {precio}</strong><br>
            <small style='color:#94a3b8'>{row['descripcion'][:80]}...</small><br>
            <a href='{url_wa}' target='_blank' style='display:inline-block; margin-top:10px; background:#22c55e; color:white; padding:8px 15px; text-decoration:none; border-radius:5px; font-weight:bold;'>Abrir Chat WhatsApp</a>
            <a href='{link_pub}' target='_blank' style='display:inline-block; margin-top:10px; margin-left:10px; color:#38bdf8; text-decoration:none;'>Ver Publicación</a>
        </div>
        """
        
    html_content += "</body></html>"
    
    with open("campaña_whatsapp.html", "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("Exito: Archivo 'campaña_whatsapp.html' generado. Abrilo en tu navegador.")

if __name__ == "__main__":
    generar_links_whatsapp()
