"""
=============================================================
  GENERADOR DE LEADS B2B — Motor DuckDuckGo
  Encuentra inmobiliarias reales y sus webs en cualquier zona.
  Filosofía: Sin Bloqueos, Low RAM, Datos Directos.
=============================================================
"""
import csv
import os
import random
import time
import urllib.parse
from curl_cffi import requests
from bs4 import BeautifulSoup

os.makedirs("clientes_b2b", exist_ok=True)

def extraer_leads_ddg(zona="palermo", max_resultados=20):
    print(f"\n[B2B-DDG] Escaneando inmobiliarias en: {zona.upper()}")
    leads = []
    
    # Busqueda mas amplia
    query = f"inmobiliaria {zona} venta"
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    
    # Lista de exclusión reducida para no perder inmobiliarias reales
    exclusiones = ["zonaprop", "argenprop", "mercadolibre", "properati", "remax", "facebook", "instagram"]
    
    try:
        # Usamos curl_cffi para máxima infiltración
        time.sleep(random.uniform(1.0, 2.0))
        r = requests.get(url, impersonate="chrome120", timeout=20)
        
        if r.status_code != 200:
            print(f"  - Error de conexión (Status {r.status_code})")
            return []
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        # En DDG HTML, cada resultado es un div con clase 'result'
        results = soup.select(".result")
        
        for res in results[:max_resultados]:
            try:
                title_tag = res.select_one(".result__a")
                snippet_tag = res.select_one(".result__snippet")
                url_tag = res.select_one(".result__url")
                
                if not title_tag: continue
                
                nombre = title_tag.get_text(strip=True)
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                web = url_tag.get_text(strip=True) if url_tag else ""
                
                # Limpieza: Evitar resultados de portales grandes (ZP, Argenprop, ML)
                # Queremos ir al dueño de la inmobiliaria directamente
                skip_list = ["zonaprop", "argenprop", "mercadolibre", "remax", "properati"]
                if any(s in web.lower() for s in skip_list):
                    continue
                
                # Intentar detectar un teléfono en el snippet
                import re
                tel_match = re.search(r"(\d{2,4}[-\s]?\d{4}[-\s]?\d{4})", snippet)
                telefono = tel_match.group(1) if tel_match else "No detectado"
                
                print(f"  + {nombre} | Web: {web}")
                
                leads.append({
                    "zona": zona.title(),
                    "nombre": nombre,
                    "web": web,
                    "telefono": telefono,
                    "snippet": snippet[:100],
                    "fuente": "DuckDuckGo"
                })
            except:
                continue
                
    except Exception as e:
        print(f"  - Error en el motor: {e}")
        
    # Guardar en CSV acumulativo
    if leads:
        fname = "clientes_b2b/base_inmobiliarias.csv"
        file_exists = os.path.isfile(fname)
        with open(fname, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["zona", "nombre", "web", "telefono", "snippet", "fuente"])
            if not file_exists:
                writer.writeheader()
            writer.writerows(leads)
        print(f"\n[B2B-DDG] {len(leads)} leads guardados en {fname}")
        
    return leads

if __name__ == "__main__":
    import sys
    z = sys.argv[1] if len(sys.argv) > 1 else "palermo"
    extraer_leads_ddg(z)
