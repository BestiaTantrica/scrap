"""
=============================================================
  SCRAPER: INFOCASAS
  Estrategia: curl_cffi para bypass de TLS
=============================================================
"""
from curl_cffi import requests
from bs4 import BeautifulSoup
import re

def scrape_infocasas(operacion="venta", tipo="departamentos", zona="palermo", max_paginas=1):
    print(f"[Infocasas] Buscando {tipo} en {operacion} para {zona}...")
    resultados = []
    
    # Infocasas usa slugs simples
    zona_slug = zona.lower().replace(" ", "-")
    
    for pagina in range(1, max_paginas + 1):
        url = f"https://www.infocasas.com.ar/venta/departamentos/{zona_slug}/pagina{pagina}"
        
        try:
            r = requests.get(url, impersonate="chrome120", timeout=20)
            if r.status_code != 200: break
            
            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.select('div[class*="propList"] > div') or soup.select('.n-card')
            
            for item in items:
                try:
                    title_tag = item.select_one('a[class*="title"]') or item.select_one('h2')
                    if not title_tag: continue
                    
                    link = "https://www.infocasas.com.ar" + title_tag['href'] if title_tag['href'].startswith('/') else title_tag['href']
                    price_tag = item.select_one('div[class*="price"]') or item.select_one('.n-card__price')
                    
                    desc = title_tag.get_text(strip=True)
                    precio = price_tag.get_text(strip=True) if price_tag else "Consultar"
                    
                    # Score de Urgencia (Simulado por tags de 'Nuevo' o 'Bajó de precio')
                    score = 30
                    if "bajó" in item.get_text().lower(): score += 40
                    if "urgente" in item.get_text().lower(): score += 50
                    
                    resultados.append({
                        "fuente": "Infocasas",
                        "zona": zona.title(),
                        "descripcion": desc,
                        "precio": precio,
                        "link": link,
                        "score_urgencia": min(score, 99)
                    })
                except: continue
        except: break
        
    return resultados
