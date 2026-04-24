"""
=============================================================
  INTELIGENCIA DE ZONA — Sprint 1
  Capas: Google Trends + Dias Publicado + Eventos basicos
=============================================================
"""
import time
import random
import json
from datetime import datetime, timedelta

# ──────────────────────────────────────────────
# CAPA: GOOGLE TRENDS
# ──────────────────────────────────────────────
def get_trends(zona: str) -> dict:
    """
    Obtiene el interes de busqueda de Google para la zona en Argentina.
    Retorna tendencia de las ultimas 12 semanas y comparativa de terminos.
    """
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="es-AR", tz=-180, timeout=(10, 25), retries=2, backoff_factor=0.5)

        terminos = [
            f"departamento {zona}",
            f"alquiler {zona}",
            f"vivir en {zona}",
        ]

        pt.build_payload(terminos[:2], cat=0, timeframe="today 3-m", geo="AR")
        df = pt.interest_over_time()

        if df.empty:
            return {"error": "Sin datos de Google Trends", "zona": zona}

        col = terminos[0]
        if col not in df.columns:
            col = df.columns[0]

        promedio = round(float(df[col].mean()), 1)
        ultimo = round(float(df[col].iloc[-1]), 1)
        pico = round(float(df[col].max()), 1)
        tendencia = "subiendo" if df[col].iloc[-1] > df[col].iloc[-4] else "bajando"

        # Semana a semana (ultimas 4)
        historico = [
            {"semana": str(idx.date()), "valor": round(float(row[col]), 1)}
            for idx, row in df.tail(8).iterrows()
        ]

        return {
            "zona": zona,
            "termino": col,
            "promedio_3m": promedio,
            "interes_actual": ultimo,
            "pico_3m": pico,
            "tendencia": tendencia,
            "historico": historico,
            "interpretacion": _interpretar_trends(promedio, tendencia),
        }
    except Exception as e:
        return {"error": str(e), "zona": zona}


def _interpretar_trends(promedio: float, tendencia: str) -> str:
    if promedio > 60 and tendencia == "subiendo":
        return "Zona caliente: alto interes y en alza. Competencia alta, pero demanda real."
    elif promedio > 60 and tendencia == "bajando":
        return "Zona consolidada pero enfriandose. Posible ventana de oportunidad."
    elif promedio > 30 and tendencia == "subiendo":
        return "Zona emergente: interes creciente. Entrar antes que suba el precio."
    elif promedio > 30 and tendencia == "bajando":
        return "Zona en transicion. Monitorear antes de invertir."
    elif tendencia == "subiendo":
        return "Zona muy de nicho pero con crecimiento. Mercado poco explorado."
    else:
        return "Baja demanda digital. Puede ser oportunidad en mercado informal o zona subestimada."


# ──────────────────────────────────────────────
# CAPA: DIAS PUBLICADO (urgencia real)
# ──────────────────────────────────────────────
def get_dias_publicado(link: str, fuente: str) -> dict:
    """
    Scrape la pagina de detalle de un aviso para extraer la fecha de publicacion.
    Soporta ZonaProp y MercadoLibre.
    """
    try:
        from curl_cffi import requests as cffi_req
        time.sleep(random.uniform(1.0, 2.0))
        r = cffi_req.get(link, impersonate="chrome120", timeout=15)
        if r.status_code != 200:
            return {"dias": None, "error": f"HTTP {r.status_code}"}

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")

        if "zonaprop" in link:
            fecha_tag = soup.select_one("[class*='fecha']") or soup.select_one("[data-qa='POSTING_CARD_PUBLICATION_DATE']")
            if fecha_tag:
                texto = fecha_tag.get_text(strip=True).lower()
                dias = _parsear_dias_texto(texto)
                return {"dias": dias, "texto_original": texto}

        if "mercadolibre" in link:
            fecha_tag = soup.select_one(".ui-pdp-color--GRAY") or soup.select_one("[class*='date']")
            if fecha_tag:
                texto = fecha_tag.get_text(strip=True).lower()
                dias = _parsear_dias_texto(texto)
                return {"dias": dias, "texto_original": texto}

        # Busqueda generica
        for selector in ["[class*='date']", "[class*='fecha']", "time"]:
            tag = soup.select_one(selector)
            if tag:
                texto = tag.get_text(strip=True).lower()
                dias = _parsear_dias_texto(texto)
                if dias:
                    return {"dias": dias, "texto_original": texto}

        return {"dias": None, "error": "No se encontro fecha"}
    except Exception as e:
        return {"dias": None, "error": str(e)}


def _parsear_dias_texto(texto: str):
    """Convierte texto de fecha relativa a cantidad de dias."""
    texto = texto.lower()
    if "hoy" in texto or "hace un momento" in texto:
        return 0
    if "ayer" in texto:
        return 1
    import re
    m = re.search(r"hace (\d+) d", texto)
    if m:
        return int(m.group(1))
    m = re.search(r"hace (\d+) sem", texto)
    if m:
        return int(m.group(1)) * 7
    m = re.search(r"hace (\d+) mes", texto)
    if m:
        return int(m.group(1)) * 30
    return None


def score_urgencia_por_dias(dias):
    """Convierte dias publicado en score de urgencia (0-100)."""
    if dias is None:
        return 0
    if dias == 0:
        return 5     # Muy nuevo, no urgente aun
    if dias <= 3:
        return 20
    if dias <= 7:
        return 35
    if dias <= 14:
        return 50
    if dias <= 30:
        return 65
    if dias <= 60:
        return 80
    if dias <= 90:
        return 90
    return 100       # +90 dias = muy urgente, no vende


# ──────────────────────────────────────────────
# CAPA: EVENTOS DE ZONA
# ──────────────────────────────────────────────
def get_eventos_zona(zona: str) -> dict:
    """
    Busca eventos proximos en la zona: recitales, ferias, actos.
    Fuentes: Eventbrite (API free), Ticketek scraping, Agenda CABA.
    """
    eventos = []

    # Eventbrite API (free tier, sin key para busquedas publicas)
    try:
        from curl_cffi import requests as cffi_req
        slug_zona = zona.lower().replace(" ", "%20")
        url = f"https://www.eventbrite.com.ar/d/argentina--{zona.lower().replace(' ', '-')}/events/"
        r = cffi_req.get(url, impersonate="chrome120", timeout=15)
        if r.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("[class*='event-card']")[:10]
            for card in cards:
                titulo = card.select_one("h2,h3,[class*='title']")
                fecha = card.select_one("[class*='date'],[class*='time']")
                link = card.select_one("a[href]")
                if titulo:
                    eventos.append({
                        "fuente": "Eventbrite",
                        "titulo": titulo.get_text(strip=True)[:100],
                        "fecha": fecha.get_text(strip=True) if fecha else "Ver link",
                        "link": link["href"] if link else url,
                        "tipo": _clasificar_evento(titulo.get_text(strip=True)),
                    })
    except Exception:
        pass

    # Agenda Cultural CABA (datos abiertos)
    try:
        from curl_cffi import requests as cffi_req
        url = f"https://data.buenosaires.gob.ar/api/3/action/datastore_search?resource_id=d4831394-1e17-4862-9be7-59c5c0748f2f&q={zona}&limit=10"
        r = cffi_req.get(url, impersonate="chrome120", timeout=10)
        if r.status_code == 200:
            data = r.json()
            records = data.get("result", {}).get("records", [])
            for rec in records:
                nombre = rec.get("nombre") or rec.get("nombre_establecimiento", "")
                if nombre:
                    eventos.append({
                        "fuente": "Agenda CABA",
                        "titulo": nombre[:100],
                        "fecha": rec.get("fecha_inicio", "Proximamente"),
                        "link": rec.get("url", "https://buenosaires.gob.ar/cultura"),
                        "tipo": "Cultural",
                    })
    except Exception:
        pass

    return {
        "zona": zona,
        "total_eventos": len(eventos),
        "eventos": eventos[:15],
        "actividad_score": min(len(eventos) * 10, 100),
        "interpretacion": _interpretar_eventos(len(eventos)),
    }


def _clasificar_evento(titulo: str) -> str:
    titulo_l = titulo.lower()
    if any(w in titulo_l for w in ["recital", "concert", "musica", "show", "festival"]):
        return "Recital/Musica"
    if any(w in titulo_l for w in ["feria", "mercado", "exposicion"]):
        return "Feria/Expo"
    if any(w in titulo_l for w in ["teatro", "comedia", "obra"]):
        return "Teatro"
    if any(w in titulo_l for w in ["deporte", "maraton", "futbol"]):
        return "Deporte"
    return "General"


def _interpretar_eventos(total: int) -> str:
    if total >= 10:
        return "Zona muy activa culturalmente. Alta demanda de alquiler temporal (Airbnb). Ruido posible."
    elif total >= 5:
        return "Zona con vida propia. Buena convivencia entre residentes y turistas."
    elif total >= 2:
        return "Actividad cultural moderada. Zona tranquila con puntos de interes."
    else:
        return "Zona residencial tranquila o datos limitados. Investigar en terreno."


# ──────────────────────────────────────────────
# CAPA: ECONOMÍA (Precio/m2 Promedio)
# ──────────────────────────────────────────────
def get_precio_m2_zona(zona: str) -> dict:
    """
    Obtiene un estimado del valor del m2 en la zona basandose en datos de mercado actuales.
    En una version final, esto se conecta a la API de Properati Stats o Reporte Inmobiliario.
    Por ahora, utiliza una matriz de referencia de mercado 2026.
    """
    zona = zona.lower().strip()
    
    # Matriz de valores USD/m2 promedio por zona (Venta) - Valores aprox 2026
    matriz_valores = {
        "palermo": {"promedio": 2800, "min": 2100, "max": 3500, "tendencia": "Estable"},
        "belgrano": {"promedio": 2600, "min": 2000, "max": 3300, "tendencia": "Baja leve"},
        "recoleta": {"promedio": 2750, "min": 2200, "max": 3400, "tendencia": "Baja leve"},
        "caballito": {"promedio": 2100, "min": 1700, "max": 2500, "tendencia": "Estable"},
        "villa urquiza": {"promedio": 2300, "min": 1800, "max": 2800, "tendencia": "Sube leve"},
        "lujan": {"promedio": 1100, "min": 800, "max": 1500, "tendencia": "Sube estable"},
        "pilar": {"promedio": 1600, "min": 1100, "max": 2400, "tendencia": "Estable"},
    }
    
    data = matriz_valores.get(zona)
    
    if not data:
        # Valor default para zonas no mapeadas (Promedio GBA/CABA periferia)
        return {
            "zona": zona,
            "valor_m2_usd": 1500,
            "rango": "1000 - 2000",
            "tendencia": "Desconocida",
            "interpretacion": "Zona fuera del radar principal. Usar USD 1,500/m2 como base."
        }
        
    return {
        "zona": zona,
        "valor_m2_usd": data["promedio"],
        "rango": f"{data['min']} - {data['max']}",
        "tendencia": data["tendencia"],
        "interpretacion": f"El valor medio es de USD {data['promedio']}/m2. Cualquier oferta por debajo de USD {data['min']}/m2 es una oportunidad de arbitraje clara."
    }

# ──────────────────────────────────────────────
# ORQUESTADOR PRINCIPAL
# ──────────────────────────────────────────────
def analizar_zona(zona: str) -> dict:
    """
    Ejecuta todas las capas de inteligencia para una zona.
    Retorna un dict completo con todos los datos y el zona_score.
    """
    print(f"[ZonaIntel] Analizando: {zona}")
    resultado = {
        "zona": zona,
        "timestamp": datetime.now().isoformat(),
        "capas": {},
    }

    # Capa: Google Trends
    print("[ZonaIntel] > Google Trends...")
    resultado["capas"]["trends"] = get_trends(zona)

    # Capa: Eventos
    print("[ZonaIntel] > Eventos de zona...")
    resultado["capas"]["eventos"] = get_eventos_zona(zona)
    
    # Capa: Economía (Precio/m2)
    print("[ZonaIntel] > Datos económicos y Precio/m2...")
    resultado["capas"]["economia"] = get_precio_m2_zona(zona)

    # Zona Score parcial
    trends_score = resultado["capas"]["trends"].get("interes_actual", 0)
    eventos_score = resultado["capas"]["eventos"].get("actividad_score", 0)
    
    # Bonus al score si la tendencia del m2 esta subiendo
    tendencia_m2 = resultado["capas"]["economia"]["tendencia"]
    bonus_eco = 15 if "Sube" in tendencia_m2 else (5 if "Estable" in tendencia_m2 else 0)
    
    score_crudo = (trends_score * 0.5) + (eventos_score * 0.3) + bonus_eco
    resultado["zona_score"] = min(round(score_crudo, 1), 100)
    resultado["zona_score_label"] = _label_score(resultado["zona_score"])

    return resultado


def _label_score(score: float) -> str:
    if score >= 70:
        return "Zona Caliente"
    elif score >= 50:
        return "Zona Activa"
    elif score >= 30:
        return "Zona Estable"
    else:
        return "Zona Tranquila"


if __name__ == "__main__":
    import sys
    zona = sys.argv[1] if len(sys.argv) > 1 else "palermo"
    resultado = analizar_zona(zona)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
