"""
OLX Argentina Scraper — Comparador Inmobiliario
"""
import random
import time
from curl_cffi import requests
from bs4 import BeautifulSoup

BASE = "https://www.olx.com.ar"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9",
    "Referer": "https://www.olx.com.ar/",
}

OP_MAP = {"venta": "venta", "alquiler": "alquiler"}

def scrape(operacion="venta", tipo="departamentos", zona="palermo", max_paginas=2):
    resultados = []
    seen = set()
    op = OP_MAP.get(operacion, operacion)
    slug_zona = zona.lower().replace(" ", "-")

    for pagina in range(1, max_paginas + 1):
        url = f"{BASE}/inmuebles/{tipo}/{op}/{slug_zona}"
        if pagina > 1:
            url += f"?page={pagina}"
        try:
            time.sleep(random.uniform(1.5, 3.0))
            r = requests.get(url, impersonate="chrome120", headers=HEADERS, timeout=20)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, "html.parser")
            # OLX cards
            items = soup.select("li[data-aut-id='itemBox']")
            if not items:
                items = soup.select("li[class*='item']")
            if not items:
                # Try generic article approach
                items = soup.select("article")
            if not items:
                break

            for item in items:
                link_tag = item.select_one("a[href]")
                link = link_tag["href"] if link_tag else url
                if not link.startswith("http"):
                    link = BASE + link
                if link in seen:
                    continue
                seen.add(link)

                precio_tag = item.select_one("[data-aut-id='itemPrice']") or item.select_one('[class*="price"]')
                precio = precio_tag.get_text(strip=True) if precio_tag else "Consultar"

                titulo_tag = item.select_one("[data-aut-id='itemTitle']") or item.select_one("h2,h3")
                titulo = titulo_tag.get_text(strip=True) if titulo_tag else ""

                texto = item.get_text(" ", strip=True)
                palabras_clave = ["urgente", "oportunidad", "dueno", "particular", "liquida"]
                score = sum(10 for kw in palabras_clave if kw in texto.lower())

                resultados.append({
                    "fuente": "OLX",
                    "precio": precio,
                    "zona": zona.replace("-", " ").title(),
                    "descripcion": titulo[:200],
                    "link": link,
                    "score_urgencia": min(score, 100),
                })
        except Exception as e:
            print(f"[OLX] Error pagina {pagina}: {e}")
            break

    return resultados
