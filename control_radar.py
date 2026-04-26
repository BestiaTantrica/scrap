"""
=============================================================
  BOT ÚNICO v3.0: CENTRO DE MANDO + MODO AUTOMÁTICO
  - Botones para disparar scrapers manualmente
  - Modo AUTO: scrapea cada 6hs y manda resultados solo
  - Funciona en WSL2 y Oracle Cloud sin cambios
=============================================================
"""

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import subprocess
import os
import json
import threading
import time
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Directorio base = carpeta donde está este script
BASE_DIR = Path(__file__).parent.resolve()
load_dotenv(dotenv_path=BASE_DIR / ".env")

TOKEN   = os.environ.get("RADAR_BOT_TOKEN")
USER_ID = int(os.environ.get("TELEGRAM_CHAT_ID", "6527908321"))

if not TOKEN:
    print("[!] ERROR: No se encontró RADAR_BOT_TOKEN en .env")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# Estado del modo automático
auto_activo = {"valor": False}

# ─── MENÚ ────────────────────────────────────────────────────
def menu_principal():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🕸️ Zonaprop CABA"),
        KeyboardButton("🕸️ MercadoLibre CABA"),
        KeyboardButton("🤖 AUTO: Activar" if not auto_activo["valor"] else "🛑 AUTO: Detener"),
        KeyboardButton("📊 Estado Servidor"),
    )
    return markup

# ─── LÓGICA DE SCRAPING ──────────────────────────────────────
def worker_scraper(cmd, nombre, silencioso=False):
    """Ejecuta el scraper y luego el notificador. silencioso=True para el modo auto."""
    try:
        if not silencioso:
            print(f"[RUN] Ejecutando Scraper: {nombre}")
        
        subprocess.run(f"python3 {cmd}", shell=True, check=True, cwd=str(BASE_DIR))
        
        # Buscar el archivo generado (MIX primero, luego CABA)
        hoy = datetime.datetime.now().strftime('%Y/%m/%d')
        proveedor = "mercadolibre.json" if "ml" in cmd.lower() else "zonaprop.json"
        
        ruta = f"base_datos/{hoy}/MIX/{proveedor}"
        if not (BASE_DIR / ruta).exists():
            ruta = f"base_datos/{hoy}/CABA/{proveedor}"

        subprocess.run(
            f"python3 notificador_telegram.py {ruta}",
            shell=True, check=True, cwd=str(BASE_DIR)
        )
        print(f"[OK] Notificación enviada: {ruta}")

    except Exception as e:
        bot.send_message(USER_ID, f"❌ *Error en {nombre}:*\n`{str(e)}`", parse_mode="Markdown")

def run_scraper(nombre, cmd):
    bot.send_message(USER_ID,
        f"🔍 *Iniciando Radar:* `{nombre}`...\nTe aviso cuando termine.",
        parse_mode="Markdown", reply_markup=menu_principal()
    )
    t = threading.Thread(target=worker_scraper, args=(cmd, nombre))
    t.daemon = True
    t.start()

# ─── MODO AUTOMÁTICO ─────────────────────────────────────────
def ciclo_automatico():
    """Corre scrapers cada 6 horas mientras auto_activo sea True."""
    while auto_activo["valor"]:
        ahora = datetime.datetime.now().strftime("%H:%M")
        bot.send_message(USER_ID,
            f"🤖 *MODO AUTO* — Ciclo iniciado a las {ahora}\nEscaneando ZonaProp y MercadoLibre...",
            parse_mode="Markdown"
        )
        worker_scraper("scraper.py", "Zonaprop AUTO", silencioso=True)
        time.sleep(30)  # Pausa entre scrapers para no sobrecargar
        worker_scraper("scraper_ml.py", "MercadoLibre AUTO", silencioso=True)
        
        # Esperar 6 horas (21600 segundos), pero chequeando si se desactivó
        for _ in range(360):  # 360 x 60s = 6hs
            if not auto_activo["valor"]:
                break
            time.sleep(60)

# ─── HANDLERS DE TELEGRAM ────────────────────────────────────
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    estado_auto = "🟢 ACTIVO" if auto_activo["valor"] else "🔴 INACTIVO"
    text = (
        f"👑 *CENTRO DE MANDO — RADAR INMOBILIARIO*\n\n"
        f"🤖 Modo Automático: {estado_auto}\n\n"
        f"Usá los botones de abajo para controlar el sistema."
    )
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=menu_principal())

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text

    if text == "🕸️ Zonaprop CABA":
        run_scraper("Zonaprop CABA", "scraper.py")

    elif text == "🕸️ MercadoLibre CABA":
        run_scraper("MercadoLibre CABA", "scraper_ml.py")

    elif text == "📊 Estado Servidor":
        try:
            ram = subprocess.check_output("free -h", shell=True).decode()
            estado_auto = "🟢 ACTIVO" if auto_activo["valor"] else "🔴 INACTIVO"
            bot.reply_to(message,
                f"📊 *Estado RAM:*\n```\n{ram}\n```\n🤖 *Modo Auto:* {estado_auto}",
                parse_mode="Markdown"
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {e}")

    elif "AUTO: Activar" in text:
        if not auto_activo["valor"]:
            auto_activo["valor"] = True
            bot.reply_to(message,
                "🤖 *Modo Automático ACTIVADO*\n"
                "Voy a scrapear ZonaProp + MercadoLibre cada 6 horas y mandarte los resultados acá.",
                parse_mode="Markdown", reply_markup=menu_principal()
            )
            t = threading.Thread(target=ciclo_automatico)
            t.daemon = True
            t.start()
        else:
            bot.reply_to(message, "⚠️ El modo automático ya está activo.")

    elif "AUTO: Detener" in text:
        auto_activo["valor"] = False
        bot.reply_to(message,
            "🛑 *Modo Automático DETENIDO*\nEl bot ya no escaneará automáticamente.",
            parse_mode="Markdown", reply_markup=menu_principal()
        )

print("[OK] Centro de Mando v3.0 listo — Modo Auto disponible")
print(f"[OK] Chat ID configurado: {USER_ID}")
bot.infinity_polling()

