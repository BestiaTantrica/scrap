import os

class RadarMarketing:
    def __init__(self):
        self.watermark_text = "RADAR ALPHA — INTELIGENCIA INMOBILIARIA"

    def generar_publicacion_dueño(self, datos):
        """
        Genera un KIT de Marketing PROFESIONAL y COPIABLE.
        """
        zona = datos.get('zona', 'CABA').upper()
        precio = datos.get('precio', 'Consultar')
        detalles = datos.get('detalles', '')
        plataforma = datos.get('plataforma', 'instagram')
        operacion = datos.get('operacion', 'VENTA').upper()

        # --- COPY DE INSTAGRAM (PRO) ---
        copy_ig = f"""💎 OPORTUNIDAD DE {operacion} EN {zona}

📍 Ubicación: {zona}
💰 Valor: US$ {precio}
🏠 Detalles: {detalles}

🔥 Detectado por el Radar Alpha. Contacto directo con el dueño sin intermediarios.

#RealEstate #Argentina #Inversiones #RadarAlpha #DueñoDirecto #{zona.replace(' ', '')}"""

        # --- MENSAJE DE WHATSAPP (DIRECTO) ---
        copy_wa = f"""🏠 *NUEVA OPORTUNIDAD EN {zona}*

💵 *Precio:* US$ {precio}
📝 *Detalles:* {detalles}

👉 _Ver más detalles en Radar Alpha: http://129.213.77.194:5000/_"""

        # --- PREVISUALIZACION VISUAL ---
        html_preview = f"""
        <div style='background: #050508; color: #fff; padding: 40px; border: 2px solid #00f2ff; font-family: sans-serif; border-radius: 15px;'>
            <div style='color: #00f2ff; font-size: 0.8rem; font-weight: bold; margin-bottom: 10px;'>EXCLUSIVO RADAR ALPHA</div>
            <h1 style='margin: 0; font-size: 2.5rem;'>{zona}</h1>
            <div style='font-size: 1.5rem; margin: 15px 0; color: #ffcc00;'>US$ {precio}</div>
            <p style='color: #888; font-size: 1rem;'>{detalles}</p>
            <div style='margin-top: 30px; border-top: 1px solid #333; padding-top: 10px; font-size: 0.7rem; opacity: 0.5;'>
                {self.watermark_text}
            </div>
        </div>
        """

        return {
            "html_preview": html_preview,
            "copy": copy_ig if plataforma == 'instagram' else copy_wa,
            "copy_ig": copy_ig,
            "copy_wa": copy_wa
        }
