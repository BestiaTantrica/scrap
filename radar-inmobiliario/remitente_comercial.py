"""
=============================================================
  REMITENTE COMERCIAL — El Brazo de Salida
  Toma los borradores del Cerebro Redactor y los despacha.
=============================================================
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def enviar_propuesta_inmobiliaria(destinatario_email, asunto, cuerpo):
    """Envia un mail real usando las credenciales del .env"""
    user = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")
    host = os.environ.get("EMAIL_HOST")
    port = int(os.environ.get("EMAIL_PORT", 587))

    if not user or "tu_mail" in user:
        print(f"[!] Email no configurado. Borrador para {destinatario_email} guardado en log.")
        _guardar_en_log(destinatario_email, asunto, cuerpo)
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = destinatario_email
        msg['Subject'] = asunto

        msg.attach(MIMEText(cuerpo, 'plain'))

        server = smtplib.SMTP(host, port)
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Mail enviado con exito a: {destinatario_email}")
        return True
    except Exception as e:
        print(f"❌ Error enviando a {destinatario_email}: {e}")
        return False

def _guardar_en_log(email, asunto, cuerpo):
    """Simulacion de envio si no hay credenciales."""
    os.makedirs("logs_marketing", exist_ok=True)
    with open("logs_marketing/campaña_emails.txt", "a", encoding="utf-8") as f:
        f.write(f"\n--- DESTINATARIO: {email} ---\n")
        f.write(f"ASUNTO: {asunto}\n")
        f.write(f"CUERPO:\n{cuerpo}\n")
        f.write("-" * 40 + "\n")

if __name__ == "__main__":
    # Prueba de concepto
    test_asunto = "Oportunidad de Captacion Directa"
    test_cuerpo = "Este es un mensaje de prueba del Agente Radar."
    enviar_propuesta_inmobiliaria("prueba@ejemplo.com", test_asunto, test_cuerpo)
