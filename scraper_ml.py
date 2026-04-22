"""
=============================================================
  SCRAPER MERCADOLIBRE INMUEBLES v1.0
  Fuente: ML Argentina — Propiedades sin portal profesional
  Stack: curl-cffi + BeautifulSoup (RAM-safe)
=============================================================
"""

from curl_cffi import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime

# ─── CONFIGURACIÓN ───────────────────────────────────────────
CONFIG_ML = {
    # Mismas zonas que Zonaprop para poder cruzar datos
    "zonas": ["palermo", "belgrano", "caballito", "villa-del-parque", "almagro"],
    "max_paginas": 3,
    "delay_min": 3.0,
    "delay_max": 7.0,
    "output_json": "resultados_ml.json",
    "palabras_urgencia": [
        "urgente", "urge", "dueno vende", "particular",
        "sin comision", "oportunidad", "negociable",
        "acepto oferta", "permuta", "por viaje",
    ],
}

def calcular_score_urgencia(texto: str) -> dict:
    texto_lower = texto.lower()
    encontradas = [p for p in CONFIG_ML["palabras_urgencia"] if p in texto_lower]
    score = min(100, len(encontradas) * 30)
    if "particular" in texto_lower or "dueno" in texto_lower:
        score = min(100, score + 35)
    return {
        "score": score,
        "senales": ", ".join(encontradas),
        "etiqueta": "URGENTE" if score >= 60 else ("INTERESANTE" if score >= 30 else "NORMAL")
    }

def scrape_ml_zona(zona: str, pagina: int):
    """Extrae propiedades de ML Capital Federal por zona y página."""
    offset = (pagina - 1) * 48
    # URL correcta para ML Capital Federal por barrio
    if pagina == 1:
        url = f"https://inmuebles.mercadolibre.com.ar/inmuebles/venta/capital-federal/{zona}/"
    else:
        url = f"https://inmuebles.mercadolibre.com.ar/inmuebles/venta/capital-federal/{zona}/_Desde_{offset + 1}_NoIndex_True"
    
    print(f"  -> ML Infiltrando: {zona} (pag {pagina})")
    
    try:
        response = requests.get(url, impersonate="chrome120", timeout=30)
        
        if response.status_code == 200:
            return parsear_ml(response.text, zona)
        else:
            print(f"  [X] Error {response.status_code}")
            return []
    except Exception as e:
        print(f"  [X] Error conexion: {str(e)[:50]}")
        return []

def parsear_ml(html: str, zona: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    propiedades = []
    
    # Selectores ML (múltiples fallbacks por si cambian)
    cards = (
        soup.select('li.ui-search-layout__item') or
        soup.select('div.ui-search-result') or
        soup.select('li[class*="result"]') or
        soup.select('div[class*="Result"]')
    )
    
    for card in cards:
            try:
                texto_completo = card.get_text(" ", strip=True)
                
                # Titulo (nuevo selector poly-card de ML 2024)
                titulo_tag = card.select_one('a.poly-component__title')
                titulo = titulo_tag.get_text(strip=True) if titulo_tag else texto_completo[:100]
                
                # Link (limpiar tracking)
                link = titulo_tag["href"].split("#")[0] if titulo_tag and titulo_tag.get("href") else ""
                
                # Precio
                moneda_tag = card.select_one('span.andes-money-amount__currency-symbol')
                fraccion_tag = card.select_one('span.andes-money-amount__fraction')
                if fraccion_tag:
                    moneda = moneda_tag.get_text(strip=True) if moneda_tag else ""
                    precio = f"{moneda} {fraccion_tag.get_text(strip=True)}"
                else:
                    precio = "Consultar"
                
                # Vendedor: si tiene nombre es inmobiliaria, si no es particular
                seller_tag = card.select_one('span.poly-component__seller')
                vendedor = seller_tag.get_text(strip=True) if seller_tag else "Particular"
                es_inmobiliaria = bool(seller_tag)
                
                urgencia = calcular_score_urgencia(titulo + " " + texto_completo)
                
                # Solo guardar si tiene link válido
                if not link: continue
                
                propiedades.append({
                    "id": f"ml_{abs(hash(link)) % 10000000}",
                    "fuente": "MercadoLibre",
                    "zona": zona.title(),
                    "titulo": titulo[:150],
                    "precio": precio,
                    "direccion": zona.title(),
                    "vendedor": vendedor,
                    "es_inmobiliaria": es_inmobiliaria,
                    "score_urgencia": urgencia["score"],
                    "etiqueta": urgencia["etiqueta"],
                    "senales": urgencia["senales"],
                    "link": link,
                    "fecha": datetime.now().strftime("%Y-%m-%d")
                })
            except:
                continue
    return propiedades


def run(zona_arg=None):
    import sys
    zonas = [zona_arg] if zona_arg else (
        [sys.argv[1]] if len(sys.argv) > 1 else CONFIG_ML["zonas"]
    )
    
    print("\n" + "="*55)
    print("    RADAR ML INMUEBLES v1.0")
    print("="*55 + "\n")

    todas = []
    ids = set()
    
    for zona in zonas:
        print(f"[+] Zona ML: {zona}")
        for pagina in range(1, CONFIG_ML["max_paginas"] + 1):
            resultado = scrape_ml_zona(zona, pagina)
            if not resultado:
                break
            for p in resultado:
                if p["id"] not in ids:
                    ids.add(p["id"])
                    todas.append(p)
            time.sleep(random.uniform(CONFIG_ML["delay_min"], CONFIG_ML["delay_max"]))
        time.sleep(random.uniform(8, 15))
    
    if todas:
        todas.sort(key=lambda x: x["score_urgencia"], reverse=True)
        with open(CONFIG_ML["output_json"], "w", encoding="utf-8") as f:
            json.dump(todas, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] ML listo. {len(todas)} propiedades capturadas.")
    else:
        print("\n[!] Sin resultados. Verificar zona o conexion.")

if __name__ == "__main__":
    run()
