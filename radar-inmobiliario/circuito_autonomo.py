import time
import os
import requests
import json
from datetime import datetime
from scrapers import bora_real
from radar_marketing import RadarMarketing
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def buscar_clientes_potenciales(zona):
    """Busca en la base de leads quiénes están interesados en esta zona."""
    clientes_interesados = []
    try:
        if os.path.exists('leads_clientes.json'):
            with open('leads_clientes.json', 'r') as f:
                db = json.load(f)
                for c in db:
                    if zona.upper() in c.get('zonas_interes', '').upper():
                        clientes_interesados.append(c)
    except: pass
    return clientes_interesados

def ejecutar_ciclo_pro():
    print(f"\n🔱 [SISTEMA] Iniciando Ciclo de Inteligencia: {datetime.now()}")
    
    # 1. Escaneo y Acumulación
    remates = bora_real.raspar_bora_real(zona="CABA")
    
    if remates:
        marketing = RadarMarketing()
        for r in remates:
            # --- EL CEREBRO DE NEGOCIO ---
            clientes = buscar_clientes_potenciales("CABA")
            
            # Generar Informe de Match
            resumen_match = f"🎯 *MATCH DE NEGOCIO DETECTADO*\n\n📍 Oportunidad: {r['titulo']}\n👥 Clientes Potenciales en Base: {len(clientes)}\n\n"
            
            if clientes:
                resumen_match += "*ACCION RECOMENDADA:* Disparar kit de marketing a estos leads."
            else:
                resumen_match += "*ACCION RECOMENDADA:* Ampliar base de leads en zona con Google Maps Scraper."
            
            # Notificar al Comandante
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          json={"chat_id": CHAT_ID, "text": resumen_match, "parse_mode": "Markdown"})
            
            # 2. Guardar en Base Maestra para Análisis Semanal
            with open('resultados/master_radar.csv', 'a') as f:
                f.write(f"{datetime.now()},{r['titulo']},{r['link']}\n")

    print(f"🏁 [SISTEMA] Ciclo completado. Base de datos enriquecida.")

if __name__ == "__main__":
    import sys
    if "--once" in sys.argv:
        ejecutar_ciclo_pro()
    else:
        while True:
            ejecutar_ciclo_pro()
            time.sleep(10800)
