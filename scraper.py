"""
=============================================================
  RADAR INMOBILIARIO v3.0 (INFILTRATION) — MIGRACION_SCRAPING_CASH
  Scraper de Zonaprop con TLS Fingerprinting (curl-cffi)
  Optimizado para 1GB RAM | Cero dependencias de navegador
=============================================================
"""

from curl_cffi import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import os
import json
from datetime import datetime

# ─── CONFIGURACIÓN ───────────────────────────────────────────
CONFIG = {
    "zonas": ["palermo", "belgrano", "caballito", "villa-crespo", "almagro"],
    "operacion": "venta",
    "tipo": "departamentos",
    "max_paginas": 3,
    "delay_min": 3.0,
    "delay_max": 7.0,
    "palabras_urgencia": [
        "urgente", "urge", "dueño vende", "dueño directo",
        "particular", "sin comisión", "oportunidad", "negociable",
        "acepto oferta", "necesito vender", "por viaje",
    ],
    "output_csv": "resultados_radar.csv",
    "output_json": "resultados_radar.json",
}

def calcular_score_urgencia(titulo: str, descripcion: str) -> dict:
    texto = (titulo + " " + descripcion).lower()
    encontradas = [p for p in CONFIG["palabras_urgencia"] if p in texto]
    score = min(100, len(encontradas) * 25)
    if "dueño directo" in texto or "particular" in texto:
        score = min(100, score + 30)
    return {
        "score": score,
        "señales": encontradas,
        "etiqueta": "URGENTE" if score >= 60 else ("INTERESANTE" if score >= 30 else "NORMAL")
    }

def scrape_zona(zona: str, pagina: int):
    """Extracción usando curl-cffi. Soporta SLUGs o URLs completas."""
    if zona.startswith("http"):
        # Limpiar la URL de parámetros de paginación previos
        import re
        base = re.sub(r"-pagina-\d+", "", zona.replace(".html", ""))
        url = f"{base}-pagina-{pagina}.html"
    else:
        # Es un SLUG (comportamiento por defecto)
        url = f"https://www.zonaprop.com.ar/{CONFIG['tipo']}-{CONFIG['operacion']}-{zona}-dueno-directo-pagina-{pagina}.html"
    
    print(f"  -> Infiltrando URL: {url}")
    
    try:
        # curl-cffi imita el TLS fingerprint de Chrome 120
        response = requests.get(
            url, 
            impersonate="chrome120", 
            timeout=30
        )
        
        if response.status_code == 200:
            return parsear_listado(response.text, zona)
        elif response.status_code == 403:
            print(f"  [X] Bloqueo 403. Probando delay largo...")
            time.sleep(15)
            return []
        else:
            print(f"  [X] Error {response.status_code}")
            return []

    except Exception as e:
        print(f"  [X] Error conexión: {str(e)[:50]}")
        return []

def parsear_listado(html: str, zona: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    propiedades = []
    cards = soup.find_all("div", {"data-id": True})
    
    if not cards:
        cards = soup.select('div[class*="PostingCard"], div[class*="CardContainer"]')

    for card in cards:
        try:
            # Capturar todo el texto de la card para no fallar por selectores
            texto_completo = card.get_text(" ", strip=True)
            
            # Intentar capturar link
            link_tag = card.find("a", href=True)
            link = "https://www.zonaprop.com.ar" + link_tag["href"] if link_tag else ""
            
            # Intentar capturar precio (suele tener el signo $)
            precio = "Consultar"
            for div in card.find_all(["div", "span"]):
                txt = div.get_text(strip=True)
                if "$" in txt or "USD" in txt:
                    precio = txt
                    break

            # El "titulo" lo sacamos de los primeros 100 caracteres del texto completo si no hay tag
            titulo_tag = card.find(["h2", "h3"]) or card.select_one('div[class*="Title"]')
            titulo = titulo_tag.get_text(strip=True) if titulo_tag else texto_completo[:100]
            
            # El score lo calculamos sobre TODO el texto de la card
            urgencia = calcular_score_urgencia(titulo, texto_completo)
            
            if urgencia["score"] > 0 or "dueño" in texto_completo.lower():
                propiedades.append({
                    "id": card.get("data-id"),
                    "zona": zona.replace("-", " ").title(),
                    "titulo": titulo[:150],
                    "precio": precio,
                    "direccion": zona.replace("-", " ").title(), # Placeholder por zona
                    "score_urgencia": urgencia["score"],
                    "etiqueta": urgencia["etiqueta"],
                    "señales": ", ".join(urgencia["señales"]),
                    "link": link,
                    "fecha": datetime.now().strftime("%Y-%m-%d")
                })
        except: continue
    return propiedades

import sys

def run():
    # Soporte para argumentos de línea de comandos (versatilidad total)
    zonas_a_escanear = CONFIG["zonas"]
    if len(sys.argv) > 1:
        # Si se pasa un argumento, se usa como zona única
        zonas_a_escanear = [sys.argv[1]]
        print(f"\n[!] MODO MISION: Escaneando zona puntual: {sys.argv[1]}\n")

    print("\n" + "="*55)
    print("    RADAR INMOBILIARIO v3.1 (STEALTH & COMMANDS)")
    print("="*55 + "\n")
    
    todas = []
    ids = set()
    
    for zona in zonas_a_escanear:
        print(f"[+] Iniciando Infiltración: {zona}")
        # Reducir delays si es solo una zona para mayor velocidad percibida
        for pagina in range(1, CONFIG["max_paginas"] + 1):
            resultado = scrape_zona(zona, pagina)
            if not resultado: break
            
            for p in resultado:
                if p["id"] not in ids:
                    ids.add(p["id"])
                    todas.append(p)
            
            time.sleep(random.uniform(CONFIG["delay_min"], CONFIG["delay_max"]))
        
        time.sleep(random.uniform(5, 10))

    if todas:
        todas.sort(key=lambda x: x["score_urgencia"], reverse=True)
        with open(CONFIG["output_json"], "w", encoding="utf-8") as f:
            json.dump(todas, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Éxito. {len(todas)} propiedades filtradas.")
    else:
        print("\n[!] No se capturaron datos.")

if __name__ == "__main__":
    run()
