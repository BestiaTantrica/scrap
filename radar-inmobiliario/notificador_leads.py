"""
=============================================================
  RADAR ALPHA — Notificador Automático de Leads
  Telegram (siempre) + WhatsApp Twilio (opcional)
=============================================================
"""
import os
import requests as req
from dotenv import load_dotenv

load_dotenv()

BASE_URL      = os.environ.get("BASE_URL", "http://localhost:5000")
BOT_TOKEN     = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def notificar_telegram(mensaje: str):
    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        return
    req.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": ADMIN_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"},
        timeout=10,
    )


def enviar_whatsapp_lead(telefono: str, zona: str) -> bool:
    """Envía el teaser al WhatsApp del lead vía Twilio (si está configurado)."""
    sid   = os.environ.get("TWILIO_SID")
    token = os.environ.get("TWILIO_TOKEN")
    from_wa = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    if not sid or not token:
        print("[WhatsApp] Twilio no configurado. Saltando envío.")
        return False

    try:
        from twilio.rest import Client
        client = Client(sid, token)
        mensaje = (
            f"¡Hola! Soy Radar Alpha. 🎯\n"
            f"Tu Teaser de *{zona}* está listo.\n"
            f"Entrá acá para verlo: {BASE_URL}"
        )
        msg = client.messages.create(
            from_=from_wa,
            body=mensaje,
            to=f"whatsapp:{telefono.replace('+', '').replace(' ', '')}",
        )
        print(f"[WhatsApp] Enviado. SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"[WhatsApp] Fallo: {e}")
        return False


if __name__ == "__main__":
    notificar_telegram("🧪 Test de notificador — Radar Alpha online.")
