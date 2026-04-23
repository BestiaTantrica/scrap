"""
=============================================================
  SCRAPER: LA GRAN INMOBILIARIA
  Estrategia: Infiltración limpia para captar Dueños Directos.
=============================================================
"""
from curl_cffi import requests
from bs4 import BeautifulSoup

def scrape_lagraninmo(operacion="venta", tipo="departamentos", zona="palermo", max_paginas=1):
    print(f"[LaGranInmo] Buscando {tipo} en {operacion} para {zona}...")
    resultados = []
    zona_slug = zona.lower().replace(" ", "-")
    
    for pagina in range(1, max_paginas + 1):
        url = f"https://www.lagraninmobiliaria.com/venta/departamentos/{zona_slug}"
        if pagina > 1: url += f"?pagina={pagina}"
        
        try:
            r = requests.get(url, impersonate="chrome120", timeout=20)
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Buscamos los contenedores de avisos
            items = soup.select('article') or soup.select('.card')
            
            for item in items:
                try:
                    title_tag = item.select_one('h2') or item.select_one('h3')
                    link_tag = item.select_one('a')
                    price_tag = item.select_one('.price') or item.select_one('b')
                    
                    if not title_tag or not link_tag: continue
                    
                    link = link_tag['href']
                    if not link.startswith('http'): link = "https://www.lagraninmobiliaria.com" + link
                    
                    desc = title_tag.get_text(strip=True)
                    precio = price_tag.get_text(strip=True) if price_tag else "Consultar"
                    
                    score = 20
                    if "dueño" in item.get_text().lower() or "particular" in item.get_text().lower():
                        score += 60
                    
                    resultados.append({
                        "fuente": "GranInmo",
                        "zona": zona.title(),
                        "descripcion": desc,
                        "precio": precio,
                        "link": link,
                        "score_urgencia": min(score, 99)
                    })
                except: continue
        except: break
        
    return resultados
