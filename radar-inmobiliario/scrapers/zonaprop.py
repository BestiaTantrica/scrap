"""
ZonaProp Scraper — Comparador Inmobiliario
Usa curl-cffi para evadir bloqueos TLS
"""
import random
import time
from curl_cffi import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

def _build_url(operacion, tipo, zona, pagina):
    """Construye la URL de Zonaprop. Acepta slugs o URLs completas."""
    if zona.startswith("http"):
        import re
        base = re.sub(r"-pagina-\d+\.html", ".html", zona)
        if pagina > 1:
            return base.replace(".html", f"-pagina-{pagina}.html")
        return base
    slug = zona.lower().replace(" ", "-")
    return f"https://www.zonaprop.com.ar/{tipo}-{operacion}-{slug}-pagina-{pagina}.html"

def scrape(operacion="venta", tipo="departamentos", zona="palermo", max_paginas=2):
    resultados = []
    seen = set()

    for pagina in range(1, max_paginas + 1):
        url = _build_url(operacion, tipo, zona, pagina)
        try:
            time.sleep(random.uniform(1.5, 3.0))
            r = requests.get(url, impersonate="chrome120", headers=HEADERS, timeout=20)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.find_all("div", {"data-id": True})
            if not cards:
                cards = soup.select('div[class*="PostingCard"]')
            if not cards:
                break
            for card in cards:
                pid = card.get("data-id") or card.get("id", "")
                if pid in seen:
                    continue
                seen.add(pid)

                texto = card.get_text(" ", strip=True)
                precio_tag = card.select_one('[class*="price"]') or card.select_one('[class*="Price"]')
                precio = precio_tag.get_text(strip=True) if precio_tag else "Consultar"
                link_tag = card.select_one("a[href]")
                link = "https://www.zonaprop.com.ar" + link_tag["href"] if link_tag and link_tag["href"].startswith("/") else (link_tag["href"] if link_tag else url)

                # Score de urgencia
                palabras_clave = ["urgente", "oportunidad", "dueno", "particular", "liquida", "necesita"]
                score = sum(10 for kw in palabras_clave if kw in texto.lower())

                resultados.append({
                    "fuente": "ZonaProp",
                    "precio": precio,
                    "zona": zona.replace("-", " ").title(),
                    "descripcion": texto[:200],
                    "link": link,
                    "score_urgencia": min(score, 100),
                })
        except Exception as e:
            print(f"[ZonaProp] Error pagina {pagina}: {e}")
            break

    return resultados
