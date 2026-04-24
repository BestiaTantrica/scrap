"""
=============================================================
  COMPARADOR INMOBILIARIO — Backend Flask
  Multi-plataforma: ZonaProp, ML, OLX, Argenprop, Infocasas
  API + Panel Web + SSE para resultados en tiempo real
=============================================================
"""
import json
import os
import threading
import time
import uuid
from datetime import datetime, timedelta

import pandas as pd
from flask import Flask, Response, jsonify, request, send_from_directory, redirect
import mercadopago
from dotenv import load_dotenv

# Cargar variables de entorno (Token MP)
load_dotenv()

# Inicializar MercadoPago
sdk = mercadopago.SDK(os.environ.get("MP_ACCESS_TOKEN", ""))

from scrapers import argenprop, properati, mercadolibre, remax, zonaprop, infocasas, lagraninmo
import zona_intel

app = Flask(__name__, static_folder="static", template_folder="templates")

# Base de datos simple de pagos
PAYMENTS_FILE = "payments.json"

def registrar_pago(chat_id, zona, dias=1):
    data = {}
    if os.path.exists(PAYMENTS_FILE):
        with open(PAYMENTS_FILE, "r") as f: data = json.load(f)
    
    # Expiracion (ej: acceso por 24hs)
    expiracion = (datetime.now() + timedelta(days=dias)).isoformat()
    data[str(chat_id)] = {"zona": zona, "expira": expiracion}
    
    with open(PAYMENTS_FILE, "w") as f: json.dump(data, f)
    print(f"[Pagos] Acceso liberado para {chat_id} en {zona}")

def tiene_acceso(chat_id):
    if not os.path.exists(PAYMENTS_FILE): return False
    with open(PAYMENTS_FILE, "r") as f: data = json.load(f)
    user = data.get(str(chat_id))
    if not user: return False
    # Verificar si no expiro
    if datetime.now() > datetime.fromisoformat(user["expira"]): return False
    return True

# Estado global de los trabajos de scraping
jobs: dict = {}

SCRAPER_MAP = {
    "zonaprop": zonaprop.scrape,
    "mercadolibre": mercadolibre.scrape,
    "properati": properati.scrape,
    "argenprop": argenprop.scrape,
    "remax": remax.scrape,
    "infocasas": infocasas.scrape_infocasas,
    "lagraninmo": lagraninmo.scrape_lagraninmo,
}

FUENTE_COLORS = {
    "ZonaProp": "#00d4ff",
    "MercadoLibre": "#ffe000",
    "Properati": "#7c3aed",
    "Argenprop": "#22c55e",
    "Remax": "#f97316",
}

os.makedirs("resultados", exist_ok=True)


def _run_scraper(job_id, plataformas, operacion, tipo, zona, max_paginas):
    """Ejecuta scrapers en threads paralelos y acumula resultados."""
    jobs[job_id]["status"] = "running"
    jobs[job_id]["resultados"] = []
    jobs[job_id]["log"] = []
    all_results = []
    lock = threading.Lock()

    def scrape_one(nombre):
        fn = SCRAPER_MAP.get(nombre)
        if not fn:
            return
        jobs[job_id]["log"].append(f"[{nombre}] Iniciando...")
        try:
            res = fn(
                operacion=operacion,
                tipo=tipo,
                zona=zona,
                max_paginas=max_paginas,
            )
            with lock:
                all_results.extend(res)
                jobs[job_id]["resultados"] = sorted(
                    all_results, key=lambda x: x["score_urgencia"], reverse=True
                )
            jobs[job_id]["log"].append(f"[{nombre}] OK — {len(res)} resultados")
        except Exception as e:
            jobs[job_id]["log"].append(f"[{nombre}] ERROR: {e}")

    threads = [threading.Thread(target=scrape_one, args=(p,)) for p in plataformas]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Guardar Excel y CSV
    if all_results:
        df = pd.DataFrame(all_results)
        
        # Excel
        fname_excel = f"resultados/comparador_{zona}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        try:
            with pd.ExcelWriter(fname_excel, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Resultados")
            jobs[job_id]["excel"] = fname_excel
            jobs[job_id]["log"].append(f"[Excel] Guardado en {fname_excel}")
        except Exception as e:
            jobs[job_id]["log"].append(f"[Excel] Error: {e}")
            
        # CSV para la IA
        fname_csv = f"resultados/comparador_{zona}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            df.to_csv(fname_csv, index=False, encoding='utf-8')
            jobs[job_id]["csv"] = fname_csv
            jobs[job_id]["log"].append(f"[CSV] Generado para IA en {fname_csv}")
        except Exception as e:
            jobs[job_id]["log"].append(f"[CSV] Error: {e}")

    # Inteligencia de Zona
    jobs[job_id]["log"].append("[Intel] Calculando score de zona y tendencias...")
    try:
        intel_data = zona_intel.analizar_zona(zona.replace("-", " "))
        jobs[job_id]["intel"] = intel_data
        jobs[job_id]["log"].append("[Intel] Completado.")
    except Exception as e:
        jobs[job_id]["intel"] = None
        jobs[job_id]["log"].append(f"[Intel] Error: {e}")

    jobs[job_id]["status"] = "done"
    jobs[job_id]["total"] = len(all_results)
    jobs[job_id]["log"].append(f"COMPLETADO — {len(all_results)} resultados totales")


# ──────────────────────────────────────────────
# RUTAS API
# ──────────────────────────────────────────────

@app.route("/")
def landing():
    """Landing Page publica — El negocio."""
    return send_from_directory("templates", "landing.html")

@app.route("/lab")
def index():
    """Panel interno de analisis."""
    return send_from_directory("templates", "index.html")

@app.route("/api/zonas_calientes")
def zonas_calientes():
    """Retorna las ultimas zonas analizadas con su score para la landing."""
    zonas = []
    for jid, job in jobs.items():
        if job.get("status") == "done" and job.get("intel"):
            intel = job["intel"]
            zonas.append({
                "zona": job["params"]["zona"].title(),
                "score": intel.get("zona_score", 0),
                "label": intel.get("zona_score_label", "Estable"),
                "total": job["total"],
                "timestamp": intel.get("timestamp", ""),
            })
    # Devolver las 6 mas recientes
    return jsonify(zonas[-6:])


@app.route("/api/buscar", methods=["POST"])
def buscar():
    data = request.json
    plataformas = data.get("plataformas", list(SCRAPER_MAP.keys()))
    operacion = data.get("operacion", "venta")
    tipo = data.get("tipo", "departamentos")
    zona = data.get("zona", "palermo")
    max_paginas = int(data.get("max_paginas", 2))

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": "pending",
        "resultados": [],
        "log": [],
        "total": 0,
        "excel": None,
        "params": {"plataformas": plataformas, "operacion": operacion, "tipo": tipo, "zona": zona},
    }

    t = threading.Thread(
        target=_run_scraper,
        args=(job_id, plataformas, operacion, tipo, zona, max_paginas),
        daemon=True,
    )
    t.start()
    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job no encontrado"}), 404
    return jsonify({
        "status": job["status"],
        "total": job["total"],
        "log": job["log"][-10:],
        "resultados": job["resultados"][:100],
        "excel": job["excel"],
    })


@app.route("/api/stream/<job_id>")
def stream(job_id):
    """Server-Sent Events para actualizaciones en tiempo real."""
    def generate():
        last_log_len = 0
        last_result_len = 0
        while True:
            job = jobs.get(job_id, {})
            log = job.get("log", [])
            resultados = job.get("resultados", [])
            status = job.get("status", "pending")

            # Enviar nuevos logs
            if len(log) > last_log_len:
                new_logs = log[last_log_len:]
                for entry in new_logs:
                    yield f"data: {json.dumps({'type': 'log', 'msg': entry})}\n\n"
                last_log_len = len(log)

            # Enviar nuevos resultados
            if len(resultados) > last_result_len:
                new_results = resultados[last_result_len:]
                yield f"data: {json.dumps({'type': 'results', 'items': new_results})}\n\n"
                last_result_len = len(resultados)

            if status == "done":
                yield f"data: {json.dumps({'type': 'done', 'total': job.get('total', 0), 'excel': job.get('excel'), 'csv': job.get('csv'), 'intel': job.get('intel')})}\n\n"
                break

            time.sleep(0.8)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/descargar/<job_id>")
def descargar(job_id):
    from flask import send_file
    job = jobs.get(job_id)
    if not job or not job.get("excel"):
        return jsonify({"error": "Excel no disponible"}), 404
    return send_file(job["excel"], as_attachment=True)


@app.route("/api/descargar_csv/<job_id>")
def descargar_csv(job_id):
    from flask import send_file
    job = jobs.get(job_id)
    if not job or not job.get("csv"):
        return jsonify({"error": "CSV no disponible"}), 404
    return send_file(job["csv"], as_attachment=True)


@app.route("/api/generar_pago", methods=["POST"])
def generar_pago():
    """Genera un link de cobro real en MercadoPago."""
    data = request.json
    chat_id = data.get("email", "anonimo")
    zona = data.get("zona", "general").upper()
    plan = data.get("plan", "full")
    
    if not os.environ.get("MP_ACCESS_TOKEN"):
        return jsonify({"error": "Falta configurar el Token de MP en el .env"}), 500

    precio = 5000 if plan == "full" else 18000
    titulo = f"Reporte Full Radar Pro - {zona}" if plan == "full" else "Suscripcion Socio Radar Pro"

    base_url = request.host_url.rstrip('/')
    
    preference_data = {
        "items": [
            {
                "title": titulo,
                "quantity": 1,
                "currency_id": "ARS",
                "unit_price": precio
            }
        ],
        "payer": {
            "email": chat_id
        },
        "back_urls": {
            "success": f"{base_url}/api/pago_exitoso/{chat_id}?zona={zona}",
            "failure": f"{base_url}/",
            "pending": f"{base_url}/"
        },
        "auto_return": "approved",
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        return jsonify({"init_point": preference["init_point"]})
    except Exception as e:
        print(f"Error MP: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/webhook/mp", methods=["POST"])
def webhook_mp():
    # MercadoPago envia notificaciones aqui
    data = request.json
    print(f"[Webhook] Notificacion recibida: {data}")
    
    # En una integracion real, aqui consultariamos la API de MP para verificar el estado del pago
    # Por ahora, simulamos que si el topic es 'payment', liberamos el acceso
    if data.get("type") == "payment" or data.get("topic") == "payment":
        resource_id = data.get("data", {}).get("id") or data.get("id")
        # Aqui vendria la logica de matchear el resource_id con el chat_id
        # Para el test, vamos a crear un endpoint de 'pago_simulado'
        pass

    return jsonify({"status": "received"}), 200

@app.route("/api/pago_exitoso/<chat_id>")
def pago_exitoso(chat_id):
    # Endpoint para simular que el pago entro
    registrar_pago(chat_id, "todas", dias=30)
    return f"<h1>¡Pago Aprobado!</h1><p>Ya podés volver al bot de Telegram y pedir tus reportes Premium.</p>"

@app.route("/api/verificar_acceso/<chat_id>")
def verificar_acceso(chat_id):
    return jsonify({"acceso": tiene_acceso(chat_id)})


if __name__ == "__main__":
    print("=" * 55)
    print("  COMPARADOR INMOBILIARIO — Iniciando servidor")
    print("  Panel web: http://localhost:5000")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
