"""
Remax Argentina Scraper — reemplaza Infocasas (no disponible)
"""
import random
import time
from curl_cffi import requests
from bs4 import BeautifulSoup

BASE = "https://www.remax.com.ar"
HEADERS = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
           "Accept-Language": "es-AR,es;q=0.9", "Referer": "https://www.remax.com.ar/"}

OP_MAP = {"venta": "compra", "alquiler": "alquiler"}

def scrape(operacion="venta", tipo="departamentos", zona="palermo", max_paginas=2):
    resultados = []
    seen = set()
    zona_slug = zona.lower().replace(" ", "-")
    op = OP_MAP.get(operacion, operacion)

    for pagina in range(1, max_paginas + 1):
        url = f"{BASE}/listings/{op}/{tipo}/{zona_slug}"
        if pagina > 1:
            url += f"?page={pagina}"
        try:
            time.sleep(random.uniform(1.5, 3.0))
            r = requests.get(url, impersonate="chrome120", headers=HEADERS, timeout=20)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.select("div.card") or soup.select("[class*='listing']") or soup.select("article")
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
                precio_tag = item.select_one("[class*='price']")
                precio = precio_tag.get_text(strip=True) if precio_tag else "Consultar"
                titulo_tag = item.select_one("h2,h3,[class*='title']")
                titulo = titulo_tag.get_text(strip=True) if titulo_tag else ""
                texto = item.get_text(" ", strip=True)
                score = sum(10 for kw in ["urgente","oportunidad","dueno","particular","liquida"] if kw in texto.lower())
                resultados.append({"fuente": "Remax", "precio": precio,
                    "zona": zona.replace("-", " ").title(), "descripcion": titulo[:200],
                    "link": link, "score_urgencia": min(score, 100)})
        except Exception as e:
            print(f"[Remax] Error pagina {pagina}: {e}")
            break
    return resultados
