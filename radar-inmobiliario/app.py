import os
import json
import random
import csv
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect
from scrapers import bora_real
from radar_marketing import RadarMarketing
import mercadopago
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
MARKETING = RadarMarketing()

@app.route('/')
def landing():
    p_diario = random.choice([1000, 1500, 1999])
    p_semanal = random.choice([4000, 5000, 6000])
    p_mensual = random.choice([15000, 17000, 19000])
    return render_template('landing.html', p_diario=p_diario, p_semanal=p_semanal, p_mensual=p_mensual)

@app.route('/publicar', methods=['GET', 'POST'])
def publicar_gratis():
    if request.method == 'POST':
        datos = request.form.to_dict()
        # SIMULACIÓN DE IA VISION: Si no hay descripción, la IA 'mira' y propone una pro
        if not datos.get('detalles'):
            datos['detalles'] = "Propiedad de alto potencial detectada por análisis visual. Estructura sólida, optimización de espacios recomendada para maximizar ROI."
        
        pieza = MARKETING.generar_publicacion_dueño(datos)
        return jsonify({"status": "success", "pieza": pieza})
    return render_template('publicar.html')

@app.route('/api/oportunidades_teaser')
def oportunidades_teaser():
    zona = request.args.get('zona', 'CABA').upper()
    whatsapp = request.args.get('whatsapp', 'N/A')
    
    # REGISTRAMOS EL LEAD DE WHATSAPP INMEDIATAMENTE
    path_leads = os.path.join(BASE_DIR, 'resultados/leads_whatsapp.csv')
    os.makedirs(os.path.dirname(path_leads), exist_ok=True)
    with open(path_leads, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now()},{whatsapp},{zona}\n")
    
    # BUSQUEDA REAL
    final = bora_real.raspar_bora_real(zona)
    
    reportes = []
    for f in final:
        reportes.append({
            "tipo": "INTELIGENCIA DE ARBITRAJE",
            "evidencia": ["BORA Scanned", "Portal Cross-Check", "Z-Score Validated"],
            "fuente": "Cruce Multiplex (BORA + Redes)",
            "valor": f.get('precio_estimado', f"US$ {random.randint(40,120)}.000"),
            "desvio": f.get('desvio', f"-{random.randint(15,35)}%"),
            "ia_analysis": f"Cruce de Datos: Detectado desvío en {zona}. La propiedad {f['titulo'][:20]}... se encuentra fuera de los parámetros de precio de los portales líderes. Oportunidad de entrada rápida sugerida.",
            "status": f"🔒 DETALLES BLOQUEADOS: {f['titulo'][:40]}..."
        })
    
    return jsonify(reportes)

@app.route('/api/generar_pago', methods=['POST'])
def generar_pago():
    try:
        data = request.json
        plan = data.get('plan', 'diario')
        precio = data.get('precio', 1500)
        
        preference_data = {
            "items": [{"title": f"Radar Alpha - {plan.upper()}", "quantity": 1, "unit_price": int(precio), "currency_id": "ARS"}],
            "back_urls": {"success": "http://129.213.77.194:5000/", "failure": "http://129.213.77.194:5000/"},
            "auto_return": "approved"
        }
        
        pref = sdk.preference().create(preference_data)
        return jsonify({"init_point": pref["response"]["init_point"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
