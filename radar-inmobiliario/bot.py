"""
=============================================================
  BOT TELEGRAM — MODO VENDEDOR (FINAL)
  Solo ofrece reportes y PDFs. Cero links gratis.
=============================================================
"""
import os
import threading
import time
from pathlib import Path
import pandas as pd
import requests
import json
import telebot
from telebot import types
import reporte_generador

# Leer .env
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start", "ayuda"])
def cmd_start(msg):
    bot.send_message(msg.chat.id, "🏠 *Radar Inmobiliario IA*\n\nUsá `/buscar [zona]` para analizar oportunidades.", parse_mode="Markdown")

@bot.message_handler(commands=["buscar"])
def cmd_buscar(msg):
    if msg.chat.id != CHAT_ID: return
    
    parts = msg.text.strip().split()
    zona = parts[1] if len(parts) > 1 else "palermo"
    
    bot.send_message(msg.chat.id, f"🔍 Analizando {zona.upper()}... Esto lleva 1-2 minutos.")
    
    def _run_task():
        try:
            # Iniciar busqueda
            r = requests.post("http://localhost:5000/api/buscar", json={"zona": zona, "max_paginas": 2}, timeout=10)
            job_id = r.json().get("job_id")
            
            # Polling
            for _ in range(30):
                time.sleep(5)
                s = requests.get(f"http://localhost:5000/api/status/{job_id}").json()
                if s.get("status") == "done":
                    resultados = s.get("resultados", [])
                    intel = s.get("intel", {})
                    
                    # Guardar en cache para el PDF
                    search_cache[str(msg.chat.id)] = {"intel": intel, "resultados": resultados}
                    
                    score = intel.get("zona_score", 0)
                    label = intel.get("zona_score_label", "Estable")
                    msg_text = (
                        f"📊 *REPORTE: {zona.upper()}*\n"
                        f"───────────────────\n"
                        f"🔥 *Zona Score:* {score}/100\n"
                        f"📈 *Status:* {intel.get('zona_score_label', 'Estable')}\n\n"
                        f"✅ Encontré *{len(resultados)}* propiedades.\n"
                        f"⚠️ Detecté *{sum(1 for r in resultados if r.get('score_urgencia',0) > 70)}* dueños urgentes.\n\n"
                        f"¿Qué querés hacer?"
                    )
                    
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("💎 Ver Dueños Directos (PRO)", callback_data=f"buy_{zona}"))
                    markup.add(types.InlineKeyboardButton("📩 Recibir Teaser PDF (Gratis)", callback_data=f"teaser_{zona}"))
                    
                    bot.send_message(msg.chat.id, msg_text, reply_markup=markup, parse_mode="Markdown")
                    return
            bot.send_message(msg.chat.id, "⏰ El tiempo de espera se agotó.")
        except Exception as e:
            bot.send_message(msg.chat.id, f"❌ Error: {e}")

    threading.Thread(target=_run_task, daemon=True).start()

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    zona = call.data.split("_")[1] if "_" in call.data else "zona"
    
# Cache temporal de resultados para el PDF
search_cache = {}

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = str(call.message.chat.id)
    if "_" not in call.data: return
    
    action, zona = call.data.split("_", 1)
    
    if action == "teaser":
        bot.answer_callback_query(call.id, "Generando Reporte con data real...")
        
        # Recuperar data real de la cache
        cache = search_cache.get(chat_id, {})
        intel = cache.get("intel", {"zona_score": 50, "zona_score_label": "Analizando...", "capas": {"trends": {"interpretacion": "Data en proceso"}, "eventos": {"interpretacion": "Data en proceso"}}})
        resultados = cache.get("resultados", [])
        
        # Verificar acceso PRO
        r_acceso = requests.get(f"http://localhost:5000/api/verificar_acceso/{chat_id}").json()
        es_pro = r_acceso.get("acceso", False)
        
        # Generar PDF con los resultados REALES
        pdf_path = reporte_generador.generar_pdf_estudio(zona, intel, resultados, es_premium=es_pro)
        
        with open(pdf_path, 'rb') as f:
            cap = f"🏆 REPORTE PREMIUM: {zona.upper()}" if es_pro else f"🎁 Teaser de {zona.upper()}"
            bot.send_document(call.message.chat.id, f, caption=cap)
            
        if not es_pro:
            bot.send_message(call.message.chat.id, "🎯 *Este es un avance.* ¿Querés el reporte completo con links a dueños?\nUsa el botón 'Ver Dueños Directos (PRO)'.", parse_mode="Markdown")

    elif call.data.startswith("buy_"):
        # VERIFICAR SI YA ES PRO
        r_acceso = requests.get(f"http://localhost:5000/api/verificar_acceso/{call.message.chat.id}").json()
        if r_acceso.get("acceso", False):
            bot.send_message(call.message.chat.id, "✅ Ya tenés acceso Premium activo. ¡Disfrutá la data!")
            return

        # Si no es PRO, mandamos a pagar
        pay_url = f"http://localhost:5000/api/pago_exitoso/{call.message.chat.id}"
        msg = (
            f"🎯 *ACCESO PREMIUM: {zona.upper()}*\n\n"
            "Destrabá ahora:\n"
            "✅ Links directos sin censura.\n"
            "✅ Reporte PDF Full con m2 histórico.\n\n"
            f"💰 Pago único por 30 días: *$5.000 ARS*"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Pagar con MercadoPago", url=pay_url))
        bot.send_message(call.message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")

if __name__ == "__main__":
    print("BOT VENDEDOR INICIADO")
    bot.infinity_polling()
