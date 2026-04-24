"""
=============================================================
  MARKETING AUTOMATICO — Brazo Comercial 24/7
  Estrategia B2B: Venta de Leads (Dueños Directos) a Inmobiliarias
=============================================================
"""
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# ──────────────────────────────────────────────
# BASE DE DATOS DE CLIENTES POTENCIALES (Leads B2B)
# En el futuro, esto se puebla scrapeando Google Maps "Inmobiliarias en Lujan"
# ──────────────────────────────────────────────
CLIENTES_B2B = {
    "lujan": [
        {"nombre": "Inmobiliaria Ejemplo Lujan", "telegram_id": "TU_CHAT_ID_PARA_PROBAR", "email": "ventas@ejemplolujan.com.ar", "plan": "free"},
        # {"nombre": "Remax Lujan", "telegram_id": "...", "plan": "premium"}
    ],
    "palermo": [
        {"nombre": "Capital Inmuebles", "telegram_id": "TU_CHAT_ID_PARA_PROBAR", "email": "info@capital.com.ar", "plan": "free"},
    ]
}


def buscar_oportunidades_fuego(zona: str):
    """
    Usa la API local del comparador para buscar dueños directos altamente urgentes.
    """
    print(f"[Marketing] Buscando oportunidades en {zona}...")
    try:
        r = requests.post(
            "http://localhost:5000/api/buscar",
            json={"plataformas": ["mercadolibre", "zonaprop"], "zona": zona, "max_paginas": 1},
            timeout=10
        )
        job_id = r.json()["job_id"]
        
        # Esperar resultados
        for _ in range(20):
            time.sleep(3)
            s = requests.get(f"http://localhost:5000/api/status/{job_id}").json()
            if s.get("status") == "done":
                resultados = s.get("resultados", [])
                
                # FILTRO DE ORO: Solo dueños directos con urgencia alta
                oportunidades = [
                    res for res in resultados 
                    if res["score_urgencia"] > 50 and 
                    ("dueño" in res["descripcion"].lower() or "particular" in res["descripcion"].lower())
                ]
                
                intel = s.get("intel", {})
                return oportunidades, intel
                
        return [], {}
    except Exception as e:
        print(f"[Marketing] Error buscando en API: {e}")
        return [], {}


def enviar_oferta_marketing(oportunidad: dict, intel: dict, cliente: dict):
    """
    Arma un mensaje persuasivo para vender el lead a la inmobiliaria.
    """
    zona = oportunidad.get('zona', 'la zona')
    precio = oportunidad.get('precio', 'Consultar')
    score = intel.get('zona_score_label', 'Alta Demanda')
    
    if cliente["plan"] == "free":
        # Estrategia Freemium: Mostramos que tenemos el dato, pero censuramos el link
        mensaje = (
            f"🎯 *NUEVO LEAD DE DUEÑO DIRECTO EN {zona.upper()}*\n\n"
            f"Hola {cliente['nombre']}, nuestro radar acaba de detectar un dueño directo vendiendo urgente.\n\n"
            f"💰 *Precio publicado:* {precio}\n"
            f"📈 *Contexto de Zona:* {score}\n\n"
            f"🔒 *Link de contacto:* `[CENSURADO - REQUIERE PLAN PREMIUM]`\n\n"
            f"👉 Respondé 'QUIERO' a este bot para destrabar el acceso a este y todos los dueños directos de {zona} en tiempo real."
        )
    else:
        # Plan Premium: Le damos todo masticado
        mensaje = (
            f"🔥 *LEAD EXCLUSIVO - {zona.upper()}*\n\n"
            f"Dueño vendiendo urgente (Score {oportunidad['score_urgencia']}/100).\n"
            f"Precio: {precio}\n"
            f"Detalle: {oportunidad['descripcion'][:100]}...\n\n"
            f"🔗 Link directo: {oportunidad['link']}\n"
            f"¡Llamalo antes que otra inmobiliaria!"
        )

    # Reemplazar con tu chat ID para pruebas
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "0") 
    
    print(f"[Marketing] Enviando oferta a {cliente['nombre']}...")
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"}
        )
    except Exception as e:
        print(f"[Marketing] Error Telegram: {e}")


def ciclo_marketing_247():
    print("="*50)
    print(" INICIANDO BRAZO COMERCIAL B2B 24/7")
    print("="*50)
    
    zonas_objetivo = ["lujan", "palermo"]
    
    while True:
        for zona in zonas_objetivo:
            oportunidades, intel = buscar_oportunidades_fuego(zona)
            
            if oportunidades:
                print(f"[!] Se encontraron {len(oportunidades)} dueños directos en {zona}")
                clientes_zona = CLIENTES_B2B.get(zona, [])
                
                # Seleccionar la mejor oportunidad para mandar de cebo
                top_op = oportunidades[0] 
                
                for cliente in clientes_zona:
                    enviar_oferta_marketing(top_op, intel, cliente)
                    time.sleep(1) # Anti-spam
            else:
                print(f"[-] Nada relevante en {zona} por ahora.")
                
        print("\n[Zzz] Ciclo terminado. Esperando 1 hora para el próximo barrido...\n")
        # Para pruebas, ponemos 60 segundos. En producción sería 3600 (1 hora).
        time.sleep(60)

if __name__ == "__main__":
    ciclo_marketing_247()
