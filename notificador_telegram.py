"""
=============================================================
  TELEGRAM NOTIFIER v1.0 — RADAR INMOBILIARIO
  Envía el reporte diario al Arquitecto (y al cliente)
  via Telegram Bot. Costo: $0.
=============================================================
"""

import json
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIGURACIÓN (llenar con tus datos) ───────────────────
# Para crear un bot: habla con @BotFather en Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("RADAR_BOT_TOKEN")
# Tu chat_id personal (o el del cliente): usa @userinfobot para obtenerlo
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID",   "6527908321")

# Cuántas propiedades urgentes mandar por mensaje (máx. para no spamear)
MAX_PROPIEDADES_ALERTA = 5

def enviar_mensaje(texto: str) -> bool:
    """Envía un mensaje de texto a Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"  [X] Error Telegram: {e}")
        return False

def enviar_reporte(json_file: str = "resultados_radar.json"):
    """Lee el JSON del scraper y envía el reporte al cliente."""
    
    if not os.path.exists(json_file):
        print(f"[-] No se encontró {json_file}. Corré el scraper primero.")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        propiedades = json.load(f)

    if not propiedades:
        enviar_mensaje("⚠️ <b>Radar Inmobiliario</b>\nHoy no se encontraron propiedades nuevas.")
        return

    urgentes     = [p for p in propiedades if p["score_urgencia"] >= 60]
    interesantes = [p for p in propiedades if 30 <= p["score_urgencia"] < 60]

    # ── Mensaje resumen ──
    resumen = (
        f"🕸️ <b>RADAR INMOBILIARIO</b> — {datetime.now().strftime('%d/%m/%Y')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Total encontradas: <b>{len(propiedades)}</b>\n"
        f"🔥 Urgentes:          <b>{len(urgentes)}</b>\n"
        f"⚠️ Interesantes:     <b>{len(interesantes)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 Top oportunidades de hoy:"
    )
    enviar_mensaje(resumen)

    # ── Mandar las top N urgentes ──
    top = urgentes[:MAX_PROPIEDADES_ALERTA]
    if not top:
        top = interesantes[:MAX_PROPIEDADES_ALERTA]

    for i, prop in enumerate(top, 1):
        msg = (
            f"{prop.get('etiqueta', 'NORMAL')} <b>#{i}</b>\n"
            f"ZONA: <b>{prop.get('zona', 'N/A')}</b>\n"
            f"PRECIO: {prop.get('precio', 'Consultar')}\n"
            f"TITULO: {prop.get('titulo', 'Sin titulo')}\n"
            f"DIR: {prop.get('direccion', 'Ver link')}\n"
            f"SCORE: {prop.get('score_urgencia', 0)}/100\n"
            f"SENALES: {prop.get('señales', 'Dueño directo')}\n"
        )
        if prop.get("link"):
            msg += f"LINK: <a href='{prop['link']}'>Ver publicacion</a>"
        
        enviar_mensaje(msg)

    print(f"Reporte enviado a Telegram: {len(top)} propiedades.")

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        archivo = sys.argv[1]
        enviar_reporte(archivo)
    else:
        # Por defecto intenta buscar en la raíz (legacy fallback)
        enviar_reporte()
