"""
MercadoLibre Inmuebles Scraper — Comparador Inmobiliario
"""
import random
import time
from curl_cffi import requests
from bs4 import BeautifulSoup

BASE = "https://inmuebles.mercadolibre.com.ar"

TIPO_MAP = {
    "departamentos": "departamentos",
    "casas": "casas",
    "ph": "ph",
    "locales": "locales-y-comercios",
    "terrenos": "terrenos",
}
OP_MAP = {
    "venta": "venta",
    "alquiler": "alquiler",
}

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9",
    "Referer": "https://www.mercadolibre.com.ar/",
}

def _build_url(operacion, tipo, zona, offset=0):
    t = TIPO_MAP.get(tipo, tipo)
    op = OP_MAP.get(operacion, operacion)
    slug = zona.lower().replace(" ", "-")
    url = f"{BASE}/{t}/{op}/{slug}/"
    if offset > 0:
        url += f"_Desde_{offset + 1}_NoIndex_True"
    return url

def scrape(operacion="venta", tipo="departamentos", zona="palermo", max_paginas=2):
    resultados = []
    seen = set()

    for pagina in range(max_paginas):
        offset = pagina * 48
        url = _build_url(operacion, tipo, zona, offset)
        try:
            time.sleep(random.uniform(1.5, 3.0))
            r = requests.get(url, impersonate="chrome120", headers=HEADERS, timeout=20)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.select("li.ui-search-layout__item")
            if not items:
                items = soup.select("div.ui-search-result__content")
            if not items:
                break

            for item in items:
                link_tag = item.select_one("a.ui-search-link") or item.select_one("a[href]")
                link = link_tag["href"] if link_tag else url
                if link in seen:
                    continue
                seen.add(link)

                precio_tag = item.select_one("span.price-tag-fraction") or item.select_one('[class*="price"]')
                precio = precio_tag.get_text(strip=True) if precio_tag else "Consultar"
                moneda = item.select_one("span.price-tag-symbol")
                if moneda:
                    precio = f"{moneda.get_text(strip=True)}{precio}"

                titulo_tag = item.select_one("h2") or item.select_one('[class*="title"]')
                titulo = titulo_tag.get_text(strip=True) if titulo_tag else ""

                texto = item.get_text(" ", strip=True)
                palabras_clave = ["urgente", "oportunidad", "dueno", "particular", "liquida"]
                score = sum(10 for kw in palabras_clave if kw in texto.lower())

                resultados.append({
                    "fuente": "MercadoLibre",
                    "precio": precio,
                    "zona": zona.replace("-", " ").title(),
                    "descripcion": titulo[:200],
                    "link": link,
                    "score_urgencia": min(score, 100),
                })
        except Exception as e:
            print(f"[MercadoLibre] Error pagina {pagina + 1}: {e}")
            break

    return resultados
