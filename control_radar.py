"""
=============================================================
  CENTRO DE MANDO RADAR — MIGRACION_SCRAPING_CASH
  Escucha órdenes de Telegram y lanza los Scrapers (Con Botones)
=============================================================
"""

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
USER_ID = int(os.environ.get("TELEGRAM_CHAT_ID", "6527908321"))

if not TOKEN:
    print("[!] ERROR: No se encontró TELEGRAM_BOT_TOKEN en .env")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# Generar Teclado Principal (Botones Interactivos)
def menu_principal():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_status = KeyboardButton("📊 Estado del Sistema")
    btn_zp = KeyboardButton("🕸️ Escanear Zonaprop (CABA)")
    btn_ml = KeyboardButton("🕸️ Escanear MercadoLibre (CABA)")
    btn_zp_lujan = KeyboardButton("🎯 Escanear Zonaprop: Lujan")
    markup.add(btn_zp, btn_ml, btn_zp_lujan, btn_status)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.from_user.id != USER_ID: return
    help_text = (
        "🚀 *CENTRO DE MANDO RADAR*\n\n"
        "Seleccione una acción del menú inferior o use los comandos clásicos:\n"
        "🔹 `/radar <zona>` - Busca en Zonaprop (ej: /radar lujan)\n"
        "🔹 `/ml <zona>` - Busca en MercadoLibre (ej: /ml lujan)\n"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown", reply_markup=menu_principal())

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.from_user.id != USER_ID: return
    text = message.text

    if text == "📊 Estado del Sistema":
        try:
            res = subprocess.check_output("free -h", shell=True).decode()
            bot.reply_to(message, f"📊 *Estado del Servidor:*\n```\n{res}\n```", parse_mode="Markdown")
        except:
            bot.reply_to(message, "Estado local.")
            
    elif text == "🕸️ Escanear Zonaprop (CABA)":
        run_scraper(message, "scraper.py", "Zonaprop CABA")
        
    elif text == "🕸️ Escanear MercadoLibre (CABA)":
        run_scraper(message, "scraper_ml.py", "MercadoLibre CABA")
        
    elif text == "🎯 Escanear Zonaprop: Lujan":
        run_scraper(message, "scraper.py lujan", "Zonaprop Lujan")
        
    elif text.startswith("/radar "):
        zona = text.replace("/radar ", "").strip()
        run_scraper(message, f"scraper.py {zona}", f"Zonaprop {zona}")
        
    elif text.startswith("/ml "):
        zona = text.replace("/ml ", "").strip()
        run_scraper(message, f"scraper_ml.py {zona}", f"ML {zona}")

def run_scraper(message, cmd, nombre):
    msg_init = f"🔍 *Iniciando Radar en:* `{nombre}`\nEsto tomará unos minutos... ☕"
    bot.send_message(USER_ID, msg_init, parse_mode="Markdown", reply_markup=menu_principal())
    
    try:
        subprocess.run(f"python3 {cmd}", shell=True, check=True)
        # Una vez terminado, lanzamos el notificador que lee los JSON y envía los leads
        subprocess.run("python3 notificador_telegram.py", shell=True, check=True)
        bot.send_message(USER_ID, f"✅ *Radar {nombre} completado.* Resultados enviados arriba. 👆")
    except Exception as e:
        bot.send_message(USER_ID, f"❌ *Error en Radar {nombre}:* \n`{str(e)}`", parse_mode="Markdown")

print("[OK] Centro de Mando Radar Iniciado. Esperando órdenes en Telegram...")
bot.infinity_polling()
