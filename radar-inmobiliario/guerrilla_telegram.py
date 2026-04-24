"""
=============================================================
  GUERRILLA TELEGRAM — Distribución B2C / Inversores
  Genera alertas de mercado y las postea en grupos para
  llevar tráfico a la Landing Page.
=============================================================
"""
import os
import glob
import pandas as pd
import requests
from pathlib import Path

# Cargar token
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Lista de IDs de grupos/canales donde el bot es administrador o miembro
# Por ahora ponemos un chat de prueba (tu propio chat ID)
GRUPOS_OBJETIVO = [
    os.environ.get("TELEGRAM_CHAT_ID", "")
]

def obtener_ultima_data():
    """Busca el ultimo excel generado por el radar."""
    archivos = glob.glob(f"resultados/*.xlsx")
    if not archivos: return None, None
    ultimo = max(archivos, key=os.path.getctime)
    zona = ultimo.split("_")[1].capitalize()
    df = pd.read_excel(ultimo)
    return zona, df

def redactar_alerta(zona, df):
    """Crea un mensaje de guerrilla con gancho comercial."""
    if df.empty: return None
    
    total = len(df)
    urgentes = len(df[df['score_urgencia'] > 40])
    
    # Buscamos la más barata o la más urgente
    oportunidad = df.iloc[0]
    precio = oportunidad['precio']
    
    mensaje = f"""
🚨 **ALERTA RADAR: {zona.upper()}** 🚨

Gente, mi sistema acaba de hacer un barrido en {zona}. 
Hay {total} propiedades publicadas, pero encontré **{urgentes} dueños directos liquidando** por debajo del precio de mercado.

La más picante que saltó está en **{precio}** (Score de urgencia alto).
Detecté también un par de publicaciones sospechosas (posibles estafas).

Dejé el reporte preliminar gratis y los links crudos en la web. El que llegue primero la capta:
👉 http://localhost:5000 

No duerman.
    """
    return mensaje.strip()

def disparar_campaña():
    print("🚀 Iniciando Campaña de Guerrilla en Telegram...")
    zona, df = obtener_ultima_data()
    
    if df is None:
        print("❌ No hay datos recientes para armar campaña.")
        return
        
    mensaje = redactar_alerta(zona, df)
    
    exitos = 0
    for chat_id in GRUPOS_OBJETIVO:
        if not chat_id: continue
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        r = requests.post(url, json=payload)
        if r.status_code == 200:
            exitos += 1
            print(f"✅ Alerta disparada al grupo/chat: {chat_id}")
        else:
            print(f"❌ Error al enviar a {chat_id}: {r.text}")
            
    print(f"🎯 Campaña finalizada. Enviado a {exitos} grupos.")

if __name__ == "__main__":
    disparar_campaña()
